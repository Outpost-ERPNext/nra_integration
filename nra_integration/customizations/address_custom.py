import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_custom_fields():
    custom_fields = {
        "Address": [
            {
                "fieldname": "states",
                "fieldtype": "Link",
                "label": "States",
                "insert_after": "state",
                "options": "State",
                "reqd": 1
            },
            {
                "fieldname": "state_code",
                "fieldtype": "Data",
                "label": "State Code",
                "insert_after": "states",
                "fetch_from": "states.code",
                "read_only": 1
            },
            {
                "fieldname": "local_government_list",
                "fieldtype": "Link",
                "label": "Local Government List",
                "insert_after": "state_code",
                "options": "Local Government List",
                "reqd": 1
            },
            {
                "fieldname": "local_government_code",
                "fieldtype": "Data",
                "label": "Local Government Code",
                "insert_after": "local_government_list",
                "fetch_from": "local_government_list.code",
                "read_only": 1
            },
            {
                "fieldname": "country_code",
                "fieldtype": "Data",
                "label": "Country Code",
                "insert_after": "country",
                "fetch_from": "country.code",
                "read_only": 1
            },
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
        "Address": ["states", "state_code", "local_government_list", "local_government_code","country_code"]
    }

    for doctype, fields in custom_fields_to_delete.items():
        for field_name in fields:
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
                frappe.delete_doc("Custom Field", f"{doctype}-{field_name}", ignore_missing=True)
                frappe.db.commit()
                frappe.clear_cache(doctype=doctype)
