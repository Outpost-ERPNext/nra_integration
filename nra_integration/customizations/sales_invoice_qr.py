import frappe
import requests
import time

@frappe.whitelist()
def fetch_digitax_invoice_details(invoice_name):

    if not frappe.db.exists("Sales Invoice", invoice_name):
        frappe.throw(f"Sales Invoice {invoice_name} not found")

    doc = frappe.get_doc("Sales Invoice", invoice_name)

    if not doc.digitax_invoice_id:
        frappe.throw("Digitax Invoice ID is missing")

    # ✅ Skip if QR already exists
    if doc.nra_qr_code:
        return {"status": "skipped", "message": "QR already fetched"}

    settings = frappe.get_single("NRA Settings")
    api_key = settings.get_password("api_key")

    url = f"https://api.digitax.tech/ng/v1/invoices/{doc.digitax_invoice_id}"

    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    try:
        qr_code = None
        data = {}

        # 🔥 Retry (QR not always ready immediately)
        for _ in range(3):
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                qr_code = data.get("qr_code_data")

                if qr_code:
                    break

            time.sleep(2)

        if not data:
            return {
                "status": "failed",
                "message": "No response data from Digitax"
            }

        update_data = {}

        # ✅ Save QR
        if qr_code:
            update_data["nra_qr_code"] = qr_code

        # ✅ Safe optional fields (no crash)
        meta = frappe.get_meta("Sales Invoice")

        if meta.has_field("digitax_status"):
            update_data["digitax_status"] = data.get("status")

        if meta.has_field("digitax_invoice_number"):
            update_data["digitax_invoice_number"] = data.get("invoice_number")

        if update_data:
            frappe.db.set_value(
                "Sales Invoice",
                doc.name,
                update_data,
                update_modified=False
            )

        return {
            "status": "success",
            "qr_code": qr_code,
            "message": "QR fetched" if qr_code else "QR not ready yet"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Digitax GET Invoice Error")
        return {"status": "failed", "message": str(e)}