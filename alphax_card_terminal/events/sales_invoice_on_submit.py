import frappe


def sales_invoice_on_submit(doc, method=None):
    """Hook: called when a Sales Invoice is submitted.

    This is a safe default implementation that can be expanded.
    It deliberately avoids hard dependencies so the app can install cleanly.
    """
    # Example: log a message without breaking submission
    try:
        frappe.logger("alphax_card_terminal").info(
            "Sales Invoice submitted: %s", getattr(doc, "name", "<unknown>")
        )
    except Exception:
        # Never block core workflows due to logging
        pass
