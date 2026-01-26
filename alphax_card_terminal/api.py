import hmac
import hashlib

import frappe
from frappe.utils import now_datetime

from alphax_card_terminal.drivers.base import CaptureRequest
from alphax_card_terminal.drivers.registry import get_driver


def _get_settings_from_mop(mode_of_payment: str):
    # Mode of Payment custom fields (fixtures)
    settings_name = frappe.db.get_value("Mode of Payment", mode_of_payment, "act_terminal_settings")
    if not settings_name:
        return None
    return frappe.get_doc("AlphaX Payment Terminal Settings", settings_name)


@frappe.whitelist()
def get_available_drivers():
    return frappe.get_all(
        "AlphaX Terminal Driver",
        filters={"is_active": 1},
        fields=["name", "driver_code", "driver_name", "description", "capabilities"],
        order_by="driver_name asc",
    )


@frappe.whitelist()
def terminal_test_connection(settings_name: str):
    s = frappe.get_doc("AlphaX Payment Terminal Settings", settings_name)
    drv = get_driver(s)
    return drv.test_connection()


@frappe.whitelist()
def create_terminal_session(
    mode_of_payment: str,
    amount: float,
    currency: str = "SAR",
    reference_doctype: str | None = None,
    reference_name: str | None = None,
    settings_name: str | None = None,
    idempotency_key: str | None = None,
):
    """Create a terminal session record (vendor-neutral correlation object)."""
    s = frappe.get_doc("AlphaX Payment Terminal Settings", settings_name) if settings_name else _get_settings_from_mop(mode_of_payment)
    if not s:
        frappe.throw("Terminal Settings not configured for this Mode of Payment.")

    drv_doc = frappe.get_doc("AlphaX Terminal Driver", s.driver) if getattr(s, "driver", None) else None

    doc = frappe.new_doc("AlphaX Terminal Session")
    doc.uuid = frappe.generate_hash(length=32)
    doc.status = "PENDING"
    doc.company = getattr(s, "company", None)
    doc.branch = getattr(s, "branch", None)
    doc.mode_of_payment = mode_of_payment
    doc.terminal_settings = s.name
    doc.driver = drv_doc.name if drv_doc else None
    doc.amount = amount
    doc.currency = currency or "SAR"
    doc.reference_doctype = reference_doctype
    doc.reference_name = reference_name
    doc.started_on = now_datetime()
    doc.created_by_user = frappe.session.user
    doc.idempotency_key = idempotency_key
    doc.insert(ignore_permissions=True)
    return {"session": doc.name, "uuid": doc.uuid}


@frappe.whitelist()
def terminal_capture_start(
    mode_of_payment: str,
    amount: float,
    currency: str | None = None,
    reference_doctype: str | None = None,
    reference_name: str | None = None,
    settings_name: str | None = None,
    session: str | None = None,
    idempotency_key: str | None = None,
):
    """Start a terminal capture using the selected driver.

    - If session is provided, the driver request/response will be written to the session record.
    - If session is not provided, you can call create_terminal_session() first for async flows.
    """
    s = frappe.get_doc("AlphaX Payment Terminal Settings", settings_name) if settings_name else _get_settings_from_mop(mode_of_payment)
    if not s:
        return {"status": "ERROR", "message": "Terminal Settings not configured for this Mode of Payment."}

    drv = get_driver(s)

    req = CaptureRequest(
        mode_of_payment=mode_of_payment,
        amount=amount,
        currency=currency,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        idempotency_key=idempotency_key,
    )

    res = drv.start_capture(req)

    if session:
        try:
            ss = frappe.get_doc("AlphaX Terminal Session", session)
            ss.request_payload = frappe.as_json(res.get("payload") or res.get("request") or {})
            # For sync drivers we may already have a final response
            if res.get("status") in ("APPROVED", "DECLINED", "ERROR", "CANCELLED"):
                ss.status = res.get("status")
                ss.response_payload = frappe.as_json(res)
                ss.completed_on = now_datetime()
            ss.save(ignore_permissions=True)
        except Exception:
            pass

    return res


def _hmac_ok(secret: str, raw_body: bytes, signature: str | None) -> bool:
    if not secret or not signature:
        return False
    dig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    # allow "sha256=<hex>" or raw hex
    sig = signature.replace("sha256=", "").strip()
    return hmac.compare_digest(dig, sig)


@frappe.whitelist(allow_guest=True)
def terminal_callback(uuid: str):
    """HTTP callback/webhook endpoint for async agents.

    Expected:
    - raw body is JSON
    - header X-AlphaX-Signature = sha256=<hex> (optional but recommended)
    The secret is taken from Terminal Settings config_json.callback_secret if present.
    """
    raw = frappe.request.get_data() or b"{}"
    headers = {k: v for k, v in (frappe.request.headers or {}).items()}
    payload = frappe.parse_json(raw)

    # Locate session
    ss_name = frappe.db.get_value("AlphaX Terminal Session", {"uuid": uuid}, "name")
    if not ss_name:
        frappe.throw("Invalid UUID", frappe.ValidationError)
    ss = frappe.get_doc("AlphaX Terminal Session", ss_name)

    # Verify signature (if configured)
    secret = None
    try:
        sdoc = frappe.get_doc("AlphaX Payment Terminal Settings", ss.terminal_settings)
        cfg = frappe.parse_json(getattr(sdoc, "config_json", None) or "{}")
        secret = cfg.get("callback_secret")
    except Exception:
        secret = None

    sig = headers.get("X-AlphaX-Signature") or headers.get("x-alphax-signature")
    if secret and not _hmac_ok(secret, raw, sig):
        frappe.throw("Invalid signature", frappe.PermissionError)

    ss.response_payload = frappe.as_json(payload)
    # Normalize status
    status = (payload.get("status") or payload.get("result") or "PENDING").upper()
    if status not in ("APPROVED", "DECLINED", "ERROR", "CANCELLED", "PENDING"):
        status = "PENDING"
    ss.status = status
    if status in ("APPROVED", "DECLINED", "ERROR", "CANCELLED"):
        ss.completed_on = now_datetime()
    ss.save(ignore_permissions=True)

    # Optional: create AlphaX Card Transaction record for approved/declined
    if status in ("APPROVED", "DECLINED"):
        _ = log_terminal_response(
            {
                "status": "Approved" if status == "APPROVED" else "Declined",
                "amount": ss.amount,
                "currency": ss.currency,
                "reference_doctype": ss.reference_doctype,
                "reference_name": ss.reference_name,
                "mode_of_payment": ss.mode_of_payment,
                "terminal_id": payload.get("terminal_id") or payload.get("tid"),
                "merchant_id": payload.get("merchant_id") or payload.get("mid"),
                "rrn": payload.get("rrn") or payload.get("transaction_id"),
                "auth_code": payload.get("auth_code"),
                "response_code": payload.get("response_code"),
                "response_message": payload.get("message") or payload.get("response_message"),
                "raw_response": frappe.as_json(payload),
            },
            session_uuid=uuid,
        )

    return {"ok": True, "uuid": uuid, "status": ss.status}


@frappe.whitelist()
def get_terminal_session_status(uuid: str):
    ss_name = frappe.db.get_value("AlphaX Terminal Session", {"uuid": uuid}, "name")
    if not ss_name:
        return {"ok": False, "message": "Not found"}
    ss = frappe.get_doc("AlphaX Terminal Session", ss_name)
    return {
        "ok": True,
        "uuid": ss.uuid,
        "status": ss.status,
        "session": ss.name,
        "response": frappe.parse_json(ss.response_payload or "{}"),
    }


@frappe.whitelist()
def log_terminal_response(payload: dict, session_uuid: str | None = None):
    """Log a terminal response into AlphaX Card Transaction."""
    d = frappe.new_doc("AlphaX Card Transaction")
    allowed = set(d.as_dict().keys())

    for k, v in (payload or {}).items():
        if k in allowed:
            setattr(d, k, v)

    # Always keep full raw JSON
    d.raw_response = frappe.as_json(payload or {})
    d.insert(ignore_permissions=True)

    # link session if provided
    if session_uuid:
        ss_name = frappe.db.get_value("AlphaX Terminal Session", {"uuid": session_uuid}, "name")
        if ss_name:
            ss = frappe.get_doc("AlphaX Terminal Session", ss_name)
            # If session is still pending, mark it final based on transaction status
            if ss.status == "PENDING":
                ss.status = "APPROVED" if (d.status or "").lower() == "approved" else "DECLINED"
                ss.completed_on = now_datetime()
            ss.save(ignore_permissions=True)

    return d.name
