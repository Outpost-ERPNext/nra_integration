import frappe


def execute():
    custom_field = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "invoice_types"})
    if not custom_field:
        return

    frappe.db.set_value("Custom Field", custom_field, "allow_on_submit", 1)
    frappe.clear_cache(doctype="Sales Invoice")
