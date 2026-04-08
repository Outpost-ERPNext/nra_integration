import frappe
import requests
import json
from nra_integration.integration.sales_invoice_integration import generate_qr_base64

@frappe.whitelist()
def sync_credit_note_to_digitax(doc, method=None):
    """
    Core logic to sync Credit Note (Sales Return) to Digitax.
    """
    settings = frappe.get_single("NRA Settings")
    if not settings.enable_digitax_integration:
        return {"status": "failed", "message": "Digitax Integration is disabled in NRA Settings."}

    api_key = settings.get_password("api_key")
    if not api_key:
        return {"status": "failed", "message": "API Key is missing in NRA Settings."}

    # API Endpoint for Credit Notes
    url = "https://api.digitax.tech/ng/v1/credit-notes"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": api_key
    }

    # Prepare items payload
    items_payload = []
    for item in doc.items:
        digitax_item_id = frappe.db.get_value("Item", item.item_code, "digitax_item_id")
        if not digitax_item_id:
            frappe.throw(f"Digitax Item ID missing for item {item.item_code}")

        # Get tax rate
        item_tax_template = item.item_tax_template
        if not item_tax_template:
            if doc.taxes:
                tax_rate = float(doc.taxes[0].rate) / 100
            else:
                frappe.throw(f"No tax defined for item {item.item_code}")
        else:
            taxes = frappe.get_all(
                "Item Tax Template Detail",
                filters={"parent": item_tax_template},
                fields=["tax_rate"]
            )
            if not taxes:
                frappe.throw(f"No tax rate in Item Tax Template {item_tax_template}")
            tax_rate = float(taxes[0].tax_rate) / 100

        is_inclusive = False
        if doc.taxes:
            for t in doc.taxes:
                if t.included_in_print_rate:
                    is_inclusive = True
                    break

        unit_price = item.rate
        if is_inclusive and tax_rate > 0:
            unit_price = item.rate / (1 + tax_rate)

        items_payload.append({
            "item_id": digitax_item_id,
            "quantity": abs(item.qty), # Credit notes use positive quantities in Digitax
            "unit_price": round(unit_price, 4),
            "tax_rate": round(tax_rate, 4),
            "item_description": item.description or item.item_name
        })

    # Retrieve original invoice's Digitax ID
    original_digitax_id = None
    if doc.get("return_against"):
        original_digitax_id = frappe.db.get_value("Sales Invoice", doc.return_against, "digitax_invoice_id")
    
    if not original_digitax_id:
        frappe.throw(f"Original Digitax Invoice ID not found for return against {doc.return_against}. Ensure the original invoice was synced.")

    payload = {
        "return_date": str(doc.posting_date) if doc.posting_date else "",
        "issue_date": str(doc.posting_date) if doc.posting_date else "",
        "issue_time": str(doc.posting_time) if doc.posting_time else "00:00:00",
        "tax_point_date": str(doc.posting_date) if doc.posting_date else "",
        "document_currency_code": doc.currency,
        "buyer_reference": doc.po_no or doc.name,
        "trader_invoice_number": doc.name,
        "invoice_id": original_digitax_id,
        "items": items_payload
    }

    log_entry = frappe.get_doc({
        "doctype": "Digi Tax Error Log List",
        "dt": "Sales Invoice",
        "name1": doc.name,
        "status": "Failed",
        "response": ""
    })

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        log_entry.response = response.text

        if response.status_code in [200, 201]:
            data = response.json()
            digitax_id = data.get("id") or data.get("invoice_id")
            qr_code = data.get("qr_code") or ""
            
            update_data = {
                "digitax_sync_status": "Success"
            }
            if digitax_id:
                update_data["digitax_invoice_id"] = digitax_id
            if qr_code:
                update_data["nra_qr_code"] = qr_code

            frappe.db.set_value("Sales Invoice", doc.name, update_data, update_modified=False)
            frappe.db.commit()

            log_entry.status = "Success"
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()

            return {"status": "success", "digitax_id": digitax_id or "Sync successful without ID returned"}
            
        else:
            frappe.db.set_value("Sales Invoice", doc.name, "digitax_sync_status", "Failed", update_modified=False)
            frappe.db.commit()
            
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return {"status": "failed", "message": f"Digitax API returned status {response.status_code}: {response.text}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Digitax Credit Note Sync Exception")
        try:
            log_entry.response = str(e)
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
        return {"status": "failed", "message": f"An error occurred: {str(e)}"}
