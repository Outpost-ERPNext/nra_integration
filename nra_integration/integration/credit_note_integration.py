import frappe
import requests
import json
from nra_integration.integration.sales_invoice_integration import generate_qr_base64

MAX_INVOICE_LIST_PAGES = 10  # bound the scan since GET /invoices has no filter-by-id


def get_digitax_invoice(invoice_id, headers):
    """
    Find the Digitax record for an invoice.

    GET /invoices has no filter-by-id, only cursor pagination (before/after/page_size),
    so we page through it looking for a matching "id". Bounded to avoid scanning
    an unbounded invoice history.
    """
    cursor_after = None
    for _ in range(MAX_INVOICE_LIST_PAGES):
        params = {"page_size": 20}
        if cursor_after:
            params["after"] = cursor_after

        resp = requests.get("https://api.digitax.tech/ng/v1/invoices", headers=headers, params=params, timeout=20)
        if resp.status_code != 200:
            return None

        body = resp.json() or {}
        for row in body.get("data", []):
            if row.get("id") == invoice_id:
                return row

        cursor_after = (body.get("cursor") or {}).get("next")
        if not cursor_after:
            break

    return None


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
            "unit_price": round(unit_price, 2),
            "tax_rate": round(tax_rate, 4),
            "item_description": item.description or item.item_name
        })

    # Retrieve original invoice's Digitax ID
    original_digitax_id = None
    if doc.get("return_against"):
        original_digitax_id = frappe.db.get_value("Sales Invoice", doc.return_against, "digitax_invoice_id")
    
    if not original_digitax_id:
        frappe.throw(f"Original Digitax Invoice ID not found for return against {doc.return_against}. Ensure the original invoice was synced.")

    # Digitax only accepts credit notes against invoices that have finished signing
    # (indicated by a non-null "signed_at" on the invoice). Check upfront so we fail
    # with a clear message instead of a raw 412 from the credit-notes endpoint.
    invoice_record = get_digitax_invoice(original_digitax_id, headers)
    if invoice_record is not None and not invoice_record.get("signed_at"):
        frappe.throw(
            f"Cannot sync credit note: original invoice {doc.return_against} (Digitax ID {original_digitax_id}) "
            f"has not been signed yet on Digitax (signed_at is not set). "
            f"Wait for signing to complete on Digitax and retry."
        )

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
