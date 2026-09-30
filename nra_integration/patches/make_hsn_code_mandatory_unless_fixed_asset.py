import frappe


def execute():
    custom_field = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "hsn_code"})
    if not custom_field:
        return

    frappe.db.set_value(
        "Custom Field",
        custom_field,
        {"reqd": 0, "mandatory_depends_on": "eval:!doc.is_fixed_asset"},
    )
    frappe.clear_cache(doctype="Item")
