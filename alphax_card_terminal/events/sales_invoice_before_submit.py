import frappe

def sales_invoice_before_submit(doc, method=None):
    """Block submission if any card MoP requires terminal approval and no Approved transaction exists."""
    try:
        payments = getattr(doc, "payments", None) or []
    except Exception:
        payments = []

    if not payments:
        return

    for p in payments:
        mop = getattr(p, "mode_of_payment", None)
        amt = getattr(p, "amount", None)
        if not mop or not amt:
            continue

        capture = frappe.db.get_value("Mode of Payment", mop, "act_capture_terminal_data") or 0
        if not int(capture):
            continue

        require = frappe.db.get_value("Mode of Payment", mop, "act_require_terminal_approval") or 0
        if not int(require):
            continue

        exists = frappe.db.exists(
            "AlphaX Card Transaction",
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": doc.name,
                "mode_of_payment": mop,
                "status": "Approved",
                "amount": amt,
            },
        )
        if not exists:
            frappe.throw(
                f"Terminal approval is required for Mode of Payment '{mop}' (Amount: {amt}). "
                "Capture and log an Approved terminal transaction before submitting."
            )
