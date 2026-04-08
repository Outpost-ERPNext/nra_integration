import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_custom_fields():
    custom_fields = {
        "Company": [
            {
                "fieldname": "digitax_company_id",
                "fieldtype": "Data",
                "label": "Digitax Company ID",
                "insert_after": "company_name",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "digitax_line_of_business_id",
                "fieldtype": "Data",
                "label": "Digitax Line of Business ID",
                "insert_after": "digitax_company_id",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname": "digitax_sync_status",
                "fieldtype": "Select",
                "label": "Digitax Sync Status",
                "options": "Pending\nSuccess\nFailed",
                "default": "Pending",
                "insert_after": "digitax_line_of_business_id",
                "read_only": 1,
            }
        ]
    }

    for doctype, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
                create_custom_field(doctype, field)
                frappe.db.commit()
                frappe.clear_cache(doctype=doctype)

def delete_custom_fields():
    custom_fields_to_delete = {
        "Company": ["digitax_company_id", "digitax_line_of_business_id", "digitax_sync_status"]
    }

    for doctype, fields in custom_fields_to_delete.items():
        for field_name in fields:
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
                frappe.delete_doc("Custom Field", f"{doctype}-{field_name}", ignore_missing=True)
                frappe.db.commit()
                frappe.clear_cache(doctype=doctype)
