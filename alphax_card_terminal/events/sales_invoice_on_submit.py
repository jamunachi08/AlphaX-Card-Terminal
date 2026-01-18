import frappe
from frappe.utils import flt

def _is_capture_mop(mop_name: str) -> bool:
    return bool(frappe.db.get_value("Mode of Payment", mop_name, "act_capture_terminal_data"))

def _get_terminal_settings_for_mop(mop_name: str):
    return frappe.db.get_value("Mode of Payment", mop_name, "act_terminal_settings")

def _auto_log_enabled(settings_name: str) -> bool:
    if not settings_name:
        return False
    try:
        return bool(frappe.db.get_value("AlphaX Payment Terminal Settings", settings_name, "auto_log_from_sales_invoice"))
    except Exception:
        return False

def sales_invoice_on_submit(doc, method=None):
    if not getattr(doc, "payments", None):
        return

    for p in doc.payments:
        mop = getattr(p, "mode_of_payment", None)
        if not mop or not _is_capture_mop(mop):
            continue

        settings = _get_terminal_settings_for_mop(mop)
        if not _auto_log_enabled(settings):
            continue

        exists = frappe.db.exists("AlphaX Card Transaction", {
            "reference_doctype": "Sales Invoice",
            "reference_name": doc.name,
            "mode_of_payment": mop
        })
        if exists:
            continue

        tx = frappe.new_doc("AlphaX Card Transaction")
        tx.status = "Approved"
        tx.amount = flt(getattr(p, "amount", 0))
        tx.currency = doc.currency
        tx.reference_doctype = "Sales Invoice"
        tx.reference_name = doc.name
        tx.mode_of_payment = mop
        tx.rrn = getattr(p, "reference_no", None) or ""
        tx.response_message = "Auto-logged from Sales Invoice submit"
        tx.insert(ignore_permissions=True)
