import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_custom_fields():
    custom_fields = {
        "Item": [
            {
                "fieldname": "digitax_item_id",
                "fieldtype": "Data",
                "label": "Digitax Item ID",
                "insert_after": "item_name",
                "no_copy": 1,
                "read_only": 1,
            },
            {
                "fieldname":"hsn_code",
                "fieldtype":"Link",
                "label": "HSN Code",
                "options":"HSN Code",
                "insert_after":"item_group",
                "reqd": 1,
            },
            {
                "fieldname":"is_service",
                "fieldtype":"Select",
                "label": "Is Service",
                "options":"Yes\nNo",
                "insert_after":"hsn_code",
                "reqd": 1,
                "default":"No"
            },
            {
                "fieldname": "digitax_sync_status",
                "fieldtype": "Select",
                "label": "Digitax Sync Status",
                "options": "Pending\nSuccess\nFailed",
                "default": "Pending",
                "insert_after": "digitax_item_id",
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
    custom_fields_to_delete = { "Item": ["digitax_item_id","hsn_code","is_service", "digitax_sync_status"]}  

    for doctype, fields in custom_fields_to_delete.items(): 
        for field_name in fields: 
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}): 
                frappe.delete_doc("Custom Field", f"{doctype}-{field_name}", ignore_missing=True) 
                frappe.db.commit() 
                frappe.clear_cache(doctype=doctype)      