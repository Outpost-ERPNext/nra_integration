import frappe
import requests
import json

def sync_item_to_digitax(doc, method=None):

    settings = frappe.get_single("NRA Settings")
    if not settings.enable_digitax_integration:
        return

    api_key = settings.get_password("api_key")
    if not api_key:
        frappe.log_error("Digitax Integration: API Key not found in NRA Settings", "Digitax Integration Error")
        return

    # Map tax category from taxes table
    tax_category_code = "STANDARD_VAT" # Default/Fallback
    if doc.taxes:
        for tax in doc.taxes:
            if tax.item_tax_template:
                template_title = frappe.db.get_value("Item Tax Template", tax.item_tax_template, "title")
                if template_title:
                    tax_category_code = template_title
                    break

    url = "https://api.digitax.tech/ng/v1/items"
    
    payload = {
        "tax_category_code": tax_category_code,
        "product_category": doc.item_group,
        "item_name": doc.item_name,
        "hsn_code": doc.hsn_code,
        "description": doc.description or doc.item_name,
        "display_name": doc.item_name,
        "price_unit": "NGN per 1", # Hardcoded per user request
        "item_code": doc.item_code,
        "is_service": True if doc.get("is_service") == "Yes" else False
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": api_key
    }

    try:
        log_entry = frappe.get_doc({
            "doctype": "Digi Tax Item Log List",
            "item_name": doc.name,
            "status": "Failed",
            "data_response": ""
        })

        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response_data = response.json()
        log_entry.data_response = response.text
        
        if response.status_code in [200, 201]:
            digitax_id = response_data.get("id") or response_data.get("item_id")
            if digitax_id:
                # Update digitax_item_id (this field existed before)
                frappe.db.set_value("Item", doc.name, "digitax_item_id", digitax_id, update_modified=False)
                
                # Try updating sync status (new field)
                try:
                    frappe.db.set_value("Item", doc.name, "digitax_sync_status", "Success", update_modified=False)
                except Exception:
                    pass
                
                log_entry.status = "Success"
                log_entry.digitax_item_id = digitax_id
            else:
                log_entry.status = "Failed"
        else:
            try:
                frappe.db.set_value("Item", doc.name, "digitax_sync_status", "Failed", update_modified=False)
            except Exception:
                pass
            
            frappe.log_error(
                message=f"Digitax API Error: {response.status_code} - {response.text}\nPayload: {json.dumps(payload, indent=2)}",
                title="Digitax Integration Sync Failure"
            )
            
        try:
            log_entry.insert(ignore_permissions=True)
        except Exception:
            pass # Even logging might fail if Doctype is missing/corrupt
            
        frappe.db.commit()

    except Exception as e:
        try:
            frappe.db.set_value("Item", doc.name, "digitax_sync_status", "Failed", update_modified=False)
        except Exception:
            pass
        
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Digitax Integration Exception"
        )

@frappe.whitelist()
def manual_sync_item_to_digitax(item_code):
    """
    Whitelisted method to manually trigger sync for an item.
    """
    if not frappe.db.exists("Item", item_code):
        frappe.throw(f"Item {item_code} not found")
    
    doc = frappe.get_doc("Item", item_code)
    
    # Validation
    if not doc.hsn_code:
        return {"status": "failed", "message": "HSN Code is required for Digitax sync."}
    if not doc.is_service:
        return {"status": "failed", "message": "Is Service selection is required for Digitax sync."}

    sync_item_to_digitax(doc)
    
    # Check if sync was successful by verifying digitax_item_id and status
    try:
        item_data = frappe.db.get_value("Item", item_code, ["digitax_item_id", "digitax_sync_status"], as_dict=1)
        if item_data and item_data.digitax_sync_status == "Success":
            return {"status": "success", "digitax_id": item_data.digitax_item_id}
    except Exception:
        # Fallback for when column is missing
        digitax_id = frappe.db.get_value("Item", item_code, "digitax_item_id")
        if digitax_id:
            return {"status": "success", "digitax_id": digitax_id}
            
    return {"status": "failed", "message": "Sync failed or database requires migration. Check Digi Tax Item Log List for details."}

def get_item_tax_category(item_doc):
    """
    Helper to get tax category from item tax template title.
    """
    if item_doc.taxes:
        for tax in item_doc.taxes:
            if tax.item_tax_template:
                return frappe.db.get_value("Item Tax Template", tax.item_tax_template, "title")
    return "STANDARD_VAT"
