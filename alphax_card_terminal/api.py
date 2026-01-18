import frappe

@frappe.whitelist()
def terminal_capture_start(mode_of_payment, amount, currency=None, reference_doctype=None, reference_name=None, settings_name=None):
    # Framework stub: integrators implement driver calls here
    return {
        "status": "PENDING",
        "mode_of_payment": mode_of_payment,
        "amount": amount,
        "currency": currency,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "message": "AlphaX Card Terminal is installed. Configure a driver to capture real terminal responses."
    }

@frappe.whitelist()
def log_terminal_response(payload: dict):
    d = frappe.new_doc("AlphaX Card Transaction")
    allowed = set(d.as_dict().keys())
    for k,v in (payload or {}).items():
        if k in allowed:
            setattr(d, k, v)
    d.raw_response = frappe.as_json(payload or {})
    d.insert(ignore_permissions=True)
    return d.name
