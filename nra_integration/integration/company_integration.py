import frappe
import requests
import json

@frappe.whitelist()
def verify_api_key(api_key=None):
    """
    Verifies the Digitax API Key using the /info endpoint.
    """
    if not api_key:
        settings = frappe.get_single("NRA Settings")
        api_key = settings.get_password("api_key")

    if not api_key:
        frappe.throw("API Key is required for verification.")

    url = "https://api.digitax.tech/ng/v1/info"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "API Key verified successfully.",
                "data": response.json()
            }
        else:
            return {
                "status": "failed",
                "message": f"Verification failed with status code {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"An error occurred during verification: {str(e)}"
        }

@frappe.whitelist()
def manual_sync_company_to_digitax(company_name):
    """
    Whitelisted method to manually trigger sync for a company.
    """
    if not frappe.db.exists("Company", company_name):
        frappe.throw(f"Company {company_name} not found")
    
    doc = frappe.get_doc("Company", company_name)
    
    # Trigger sync
    sync_company_to_digitax(doc)
    
    # Check result with resilience
    digitax_id = None
    try:
        digitax_id = frappe.db.get_value("Company", company_name, "digitax_company_id")
    except Exception:
        pass
    
    if digitax_id:
        return {"status": "success", "digitax_id": digitax_id}
    else:
        return {"status": "failed", "message": "Company sync failed or database columns are missing. Please run migrations."}

def sync_company_to_digitax(doc, method=None):
    """
    Core logic to sync Company to Digitax.
    Fetches account info and updates the local Company record with Digitax IDs.
    """
    settings = frappe.get_single("NRA Settings")
    if not settings.enable_digitax_integration:
        return

    api_key = settings.get_password("api_key")
    if not api_key:
        return

    url = "https://api.digitax.tech/ng/v1/info"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            # Extract IDs - Mapping based on common Digitax response patterns
            # Note: Adjust these keys if the API response uses different field names
            company_id = data.get("company_id") or data.get("id")
            lob_id = data.get("line_of_business_id") or data.get("default_lob_id")
            
            update_data = {}
            if company_id:
                update_data["digitax_company_id"] = company_id
            if lob_id:
                update_data["digitax_line_of_business_id"] = lob_id
            
            # Resilience for status field
            try:
                if frappe.db.has_column("Company", "digitax_sync_status"):
                    update_data["digitax_sync_status"] = "Success"
            except Exception:
                pass

            if update_data:
                frappe.db.set_value("Company", doc.name, update_data, update_modified=False)
                frappe.db.commit()
        else:
            try:
                frappe.db.set_value("Company", doc.name, "digitax_sync_status", "Failed", update_modified=False)
            except Exception:
                pass
            frappe.log_error(f"Digitax Company Sync Failed: {response.text}", "Digitax Error")

    except Exception as e:
        try:
            frappe.db.set_value("Company", doc.name, "digitax_sync_status", "Failed", update_modified=False)
        except Exception:
            pass
        frappe.log_error(frappe.get_traceback(), "Digitax Exception")
