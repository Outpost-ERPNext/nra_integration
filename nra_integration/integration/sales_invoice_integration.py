import frappe
import requests
import qrcode
import os


@frappe.whitelist()
def manual_sync_invoice_to_digitax(invoice_name):
    """
    Whitelisted method to manually trigger sync for a Sales Invoice.
    """
    if not frappe.db.exists("Sales Invoice", invoice_name):
        frappe.throw(f"Sales Invoice {invoice_name} not found")
    
    doc = frappe.get_doc("Sales Invoice", invoice_name)
    
    # Must be submitted
    if doc.docstatus != 1:
        return {"status": "failed", "message": "Invoice must be submitted to sync to Digitax."}

    if doc.get("is_return"):
        from nra_integration.integration.credit_note_integration import sync_credit_note_to_digitax
        return sync_credit_note_to_digitax(doc)

    # Trigger sync
    res = sync_sales_invoice_to_digitax(doc)

    if res.get("status") == "success":
        # 🔥 Fetch QR Data if missing
        if not frappe.db.get_value("Sales Invoice", invoice_name, "nra_qr_code"):
            try:
                from nra_integration.customizations.sales_invoice_qr import fetch_digitax_invoice_details
                fetch_digitax_invoice_details(invoice_name)
            except Exception:
                pass
        
        # 🆕 Generate QR Image (if data exists now)
        if frappe.db.get_value("Sales Invoice", invoice_name, "nra_qr_code"):
            try:
                generate_digitax_qr(invoice_name)
            except Exception:
                pass

    return res

def sync_sales_invoice_to_digitax(doc, method=None):
    """
    Core logic to sync Sales Invoice to Digitax.
    """
    if doc.get("is_return"):
        from nra_integration.integration.credit_note_integration import sync_credit_note_to_digitax
        return sync_credit_note_to_digitax(doc)

    settings = frappe.get_single("NRA Settings")
    if not settings.enable_digitax_integration:
        return {"status": "failed", "message": "Digitax Integration is disabled in NRA Settings."}

    api_key = settings.get_password("api_key")
    if not api_key:
        return {"status": "failed", "message": "API Key is missing in NRA Settings."}

    # API Endpoint for Invoices
    url = "https://api.digitax.tech/ng/v1/invoices"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": api_key
    }

    invoice_type_code = ""
    invoice_kind = ""
    if doc.get("invoice_types"):
        invoice_type = frappe.db.get_value("Invoice Type", doc.invoice_types, ["code", "invoice_category"], as_dict=True)
        if invoice_type:
            invoice_type_code = invoice_type.code or ""
            invoice_kind = invoice_type.invoice_category or ""

    if not invoice_kind:
        invoice_kind = "B2B"

    party_id = frappe.db.get_value("Customer", doc.customer, "digitax_customer_id")
    if invoice_kind == "B2B" and not party_id:
        frappe.throw(f"Customer {doc.customer} has not been synced to Digitax yet (missing Digitax Customer ID). Sync the customer before syncing this invoice.")

    items_payload = []

    for item in doc.items:
        digitax_item_id = frappe.db.get_value("Item", item.item_code, "digitax_item_id")

        if not digitax_item_id:
            frappe.throw(f"Digitax Item ID missing for item {item.item_code}")

        # ✅ Get from item row (IMPORTANT)
        item_tax_template = item.item_tax_template

        # 🔥 Fallback (if not set)
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
            "quantity": item.qty,
            "unit_price": round(unit_price, 2),
            "tax_rate": round(tax_rate, 4)
        })


    payload = {
        "invoice_date": str(doc.posting_date) if doc.posting_date else "",
        "issue_date": str(doc.posting_date) if doc.posting_date else "",
        "invoice_type_code": invoice_type_code,
        "invoice_kind": invoice_kind,
        "document_currency_code": doc.currency,
        "trader_invoice_number": doc.po_no or "",
        "party_id": party_id,
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
            # Extract ID and QR Code from response
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

            # Attach the QR code so invoices synced via the on_submit hook get it too, not just
            # ones synced through manual_sync_invoice_to_digitax.
            try:
                if not qr_code:
                    from nra_integration.customizations.sales_invoice_qr import fetch_digitax_invoice_details
                    fetch_digitax_invoice_details(doc.name)
                if frappe.db.get_value("Sales Invoice", doc.name, "nra_qr_code"):
                    generate_digitax_qr(doc.name)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Digitax QR Attach Error")

            return {"status": "success", "digitax_id": digitax_id or "Sync successful without ID returned"}
            
        else:
            frappe.db.set_value("Sales Invoice", doc.name, "digitax_sync_status", "Failed", update_modified=False)
            frappe.db.commit()
            
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return {"status": "failed", "message": f"Digitax API returned status {response.status_code}"}

    except Exception as e:
        try:
            frappe.db.set_value("Sales Invoice", doc.name, "digitax_sync_status", "Failed", update_modified=False)
            frappe.db.commit()
        except Exception:
            pass

        log_entry.response = str(e)
        try:
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
            
        frappe.log_error(frappe.get_traceback(), "Digitax Invoice Sync Exception")
        return {"status": "failed", "message": f"An error occurred: {str(e)}"}

def generate_qr_base64(text,doc):
    # Create QR image
    img = qrcode.make(text)
    # Define public files path
    public_path = frappe.get_site_path("public", "files")

    # File name
    safe_name = doc.name.replace("/", "-")
    file_name = safe_name + " Digitax QR Code.png"
    file_path = os.path.join(public_path, file_name)

    # Save image to public/files
    img.save(file_path)
    filedoc = frappe.get_doc({
        "doctype": "File",
        "attached_to_doctype": doc.doctype,
        "attached_to_name": doc.name,
        "file_name": file_name,
        "file_url": '/files/' + file_name,
        "original_file_name": file_name,
        "dont_change_file_name": 1
    })
    filedoc.save()
    return filedoc.file_url

@frappe.whitelist()
def generate_digitax_qr(invoice_name):
    """
    Whitelisted method to generate and store QR image for an invoice.
    """
    if not frappe.db.exists("Sales Invoice", invoice_name):
        frappe.throw(f"Sales Invoice {invoice_name} not found")
    
    doc = frappe.get_doc("Sales Invoice", invoice_name)
    
    if not doc.nra_qr_code:
        frappe.throw("NRA QR Code data is missing. Please fetch details first.")
        
    file_url = generate_qr_base64(doc.nra_qr_code, doc)
    
    if file_url:
        doc.db_set("digitax_qr", file_url)
        return {"status": "success", "file_url": file_url}
    else:
        return {"status": "failed", "message": "Failed to generate QR file."}

@frappe.whitelist()
def bulk_sync_invoices_to_digitax(invoice_names):
    """
    Bulk sync selected Sales Invoices to Digitax.
    """
    if isinstance(invoice_names, str):
        import json
        invoice_names = json.loads(invoice_names)

    success_count = 0
    fail_count = 0
    messages = []

    for name in invoice_names:
        try:
            res = manual_sync_invoice_to_digitax(name)
            if res.get("status") == "success":
                success_count += 1
            else:
                fail_count += 1
                messages.append(f"{name}: {res.get('message')}")
        except Exception as e:
            fail_count += 1
            messages.append(f"{name}: {str(e)}")

    summary = f"Processed {len(invoice_names)} invoices. {success_count} Success, {fail_count} Failed."
    if messages:
        summary += "\nErrors:\n" + "\n".join(messages)

    return {
        "status": "success" if fail_count == 0 else "partial_success",
        "message": summary,
        "success_count": success_count,
        "fail_count": fail_count
    }