app_name = "alphax_card_terminal"
app_title = "AlphaX Card Terminal"
app_publisher = "AlphaX"
app_description = "Card terminal metadata capture framework (MoP-driven) for ERPNext/Frappe."
app_email = "support@alphax.local"
app_license = "MIT"

fixtures = [
    "Custom Field",
    "Print Format",
]

doc_events = {
    "Sales Invoice": {
        "on_submit": "alphax_card_terminal.events.sales_invoice_on_submit.sales_invoice_on_submit"
    }
}
