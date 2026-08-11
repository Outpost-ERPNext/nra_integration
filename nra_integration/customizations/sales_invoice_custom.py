import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_custom_fields():
    custom_fields = {
        "Sales Invoice": [
            {
                "fieldname": "invoice_types",
                "fieldtype": "Link",
                "label": "Invoice Type",
                "insert_after": "update_stock",
                "options": "Invoice Type",
                "reqd": 0,
                "in_standard_filter": 1,
                "in_list_view": 1,
                "in_global_search": 1,
                "allow_on_submit": 1,
            },
            {
                "fieldname": "invoice_number",
                "fieldtype": "Data",
                "label": "Invoice Number",
                "insert_after": "source",
                "no_copy": 1
            },
            {
                "fieldname": "digitax_invoice_id",
                "fieldtype": "Data",
                "label": "Digitax Invoice Id",
                "insert_after": "customer_name",
                "no_copy": 1
            },
            {
                "fieldname": "nra_qr_code",
                "fieldtype": "Small Text",
                "label": "NRA QR Code",
                "insert_after": "invoice_number",
                "no_copy": 1
            },
            {
                "fieldname": "digitax_sync_status",
                "fieldtype": "Data",
                "label": "Digitax Sync Status",
                "insert_after": "nra_qr_code",
                "no_copy": 1,
                "read_only": 1
            },
            {
                "fieldname": "digitax_qr",
                "fieldtype": "Attach",
                "label": "Digitax QR",
                "insert_after": "digitax_sync_status",
                "no_copy": 1,
                "read_only": 1
            }
        ]
    }

    for doctype, fields in custom_fields.items():
        for field in fields:
            existing = frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})
            if not existing:
                create_custom_field(doctype, field)
            else:
                custom_field = frappe.get_doc("Custom Field", existing)
                custom_field.update(field)
                custom_field.save()
            frappe.db.commit()
            frappe.clear_cache(doctype=doctype)

def delete_custom_fields():
    custom_fields_to_delete = {
        "Sales Invoice": ["invoice_types","invoice_number","digitax_invoice_id","nra_qr_code", "digitax_sync_status","digitax_qr"]
    }

    for doctype, fields in custom_fields_to_delete.items():
        for field_name in fields:
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
                frappe.delete_doc("Custom Field", f"{doctype}-{field_name}", ignore_missing=True)
                frappe.db.commit()
                frappe.clear_cache(doctype=doctype)
