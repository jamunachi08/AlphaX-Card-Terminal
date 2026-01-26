app_name = "alphax_card_terminal"
app_title = "AlphaX Card Terminal"
app_publisher = "AlphaX"
app_description = "Card terminal metadata capture framework (MoP-driven) for ERPNext/Frappe."
app_email = "support@alphax.com"
app_license = "MIT"

# -----------------------------------------------------------------------------
# Assets
# -----------------------------------------------------------------------------
app_include_js = [
    "/assets/alphax_card_terminal/js/alphax_card_terminal.js",
]

app_include_css = [
    "/assets/alphax_card_terminal/css/alphax_card_terminal.css",
]

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
fixtures = [
    "Custom Field",
    "Print Format",
    {"dt": "AlphaX Terminal Driver", "filters": [["is_active", "=", 1]]},
]

# -----------------------------------------------------------------------------
# DocType Events
# -----------------------------------------------------------------------------
doc_events = {
    "Sales Invoice": {
        "before_submit": "alphax_card_terminal.events.sales_invoice_before_submit.sales_invoice_before_submit",
        "on_submit": "alphax_card_terminal.events.sales_invoice_on_submit.sales_invoice_on_submit",
    }
}
