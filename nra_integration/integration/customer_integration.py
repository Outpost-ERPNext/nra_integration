import frappe
import requests
import json
import pycountry


def get_alpha3_country_code(alpha2_code):
    """Digitax expects ISO 3166-1 alpha-3 country codes (e.g. "NGA"), but
    Frappe's Country doctype stores alpha-2 codes (e.g. "NG")."""
    if not alpha2_code:
        return None
    country = pycountry.countries.get(alpha_2=alpha2_code.upper())
    return country.alpha_3 if country else None


@frappe.whitelist()
def get_customer_digitax_id(customer_name):
    """
    Fetches all parties from Digitax and matches by tax_id (TIN) to find
    the customer's Digitax party ID. Pulls address details from customer_primary_address.
    """
    if not frappe.db.exists("Customer", customer_name):
        frappe.throw(f"Customer {customer_name} not found")

    customer = frappe.get_doc("Customer", customer_name)

    settings = frappe.get_single("NRA Settings")
    if not settings.enable_digitax_integration:
        frappe.throw("Digitax Integration is not enabled. Please enable it in NRA Settings.")

    api_key = settings.get_password("api_key")
    if not api_key:
        frappe.throw("API Key is not configured in NRA Settings.")

    url = "https://api.digitax.tech/ng/v1/parties"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    log_entry = frappe.get_doc({
        "doctype": "Digi Tax Error Log List",
        "dt": "Customer",
        "name1": customer.name,
        "status": "Failed",
        "response": ""
    })

    try:
        response = requests.get(url, headers=headers, timeout=20)
        log_entry.response = response.text

        if response.status_code == 200:
            data = response.json()
            parties = data.get("data", [])

            # Match by tax_identification_number (TIN)
            matched_party = None
            customer_tin = customer.get("tax_id") or ""

            if customer_tin:
                for party in parties:
                    if party.get("tax_identification_number") == customer_tin:
                        matched_party = party
                        break

            # Fallback: match by customer_name
            if not matched_party:
                for party in parties:
                    if party.get("name", "").strip().lower() == customer.customer_name.strip().lower():
                        matched_party = party
                        break

            if matched_party:
                digitax_id = matched_party.get("id")
                frappe.db.set_value("Customer", customer.name, {
                    "digitax_customer_id": digitax_id,
                    "digitax_sync_status": "Success"
                }, update_modified=False)
                frappe.db.commit()

                log_entry.status = "Success"
                log_entry.insert(ignore_permissions=True)
                frappe.db.commit()

                return {
                    "status": "success",
                    "digitax_id": digitax_id,
                    "message": f"Customer matched successfully. Digitax ID: {digitax_id}"
                }
            else:
                frappe.db.set_value("Customer", customer.name, "digitax_sync_status", "Failed", update_modified=False)
                frappe.db.commit()

                log_entry.status = "Failed"
                log_entry.response = f"No matching party found in Digitax. Searched by TIN: '{customer_tin}' and Name: '{customer.customer_name}'. Total parties returned: {len(parties)}"
                log_entry.insert(ignore_permissions=True)
                frappe.db.commit()

                return {
                    "status": "failed",
                    "message": f"No matching party found in Digitax for TIN '{customer_tin}' or name '{customer.customer_name}'."
                }
        else:
            frappe.db.set_value("Customer", customer.name, "digitax_sync_status", "Failed", update_modified=False)
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()

            return {
                "status": "failed",
                "message": f"Digitax API returned status {response.status_code}: {response.text}"
            }

    except Exception as e:
        try:
            frappe.db.set_value("Customer", customer.name, "digitax_sync_status", "Failed", update_modified=False)
        except Exception:
            pass

        log_entry.response = str(e)
        try:
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

        frappe.log_error(frappe.get_traceback(), "Digitax Customer Integration Exception")
        return {
            "status": "failed",
            "message": f"An error occurred: {str(e)}"
        }


@frappe.whitelist()
def integrate_customer_to_digitax(customer_name):
    """
    Posts customer data to Digitax to create a party.
    Pulls address from customer_primary_address.
    (POST endpoint - to be implemented once endpoint details are available)
    """
    if not frappe.db.exists("Customer", customer_name):
        frappe.throw(f"Customer {customer_name} not found")

    customer = frappe.get_doc("Customer", customer_name)

    settings = frappe.get_single("NRA Settings")
    if not settings.enable_digitax_integration:
        frappe.throw("Digitax Integration is not enabled. Please enable it in NRA Settings.")

    api_key = settings.get_password("api_key")
    if not api_key:
        frappe.throw("API Key is not configured in NRA Settings.")

    # Get address details from customer_primary_address
    address_data = {}
    address_email = ""
    address_phone = ""
    
    if customer.customer_primary_address:
        address = frappe.get_doc("Address", customer.customer_primary_address)
        raw_address = {
            "street_name": address.address_line1,
            "city_name": address.city,
            "postal_zone": address.pincode,
            "country_code": get_alpha3_country_code(address.get("country_code")),
            "local_government_code": address.get("local_government_code"),
            "state_code": address.get("state_code")
        }
        address_data = {k: v for k, v in raw_address.items() if v}
        address_email = address.get("email_id")
        address_phone = address.get("phone")
        
    url = "https://api.digitax.tech/ng/v1/parties"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": api_key
    }

    raw_payload = {
        "tax_identification_number": customer.get("tax_id"),
        "name": customer.customer_name,
        "phone": customer.get("mobile_no") or address_phone,
        "email": customer.get("email_id") or address_email,
        "address": address_data
    }
    
    payload = {k: v for k, v in raw_payload.items() if v}


    log_entry = frappe.get_doc({
        "doctype": "Digi Tax Error Log List",
        "dt": "Customer",
        "name1": customer.name,
        "status": "Failed",
        "response": ""
    })

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response_data = response.json()
        log_entry.response = response.text

        if response.status_code in [200, 201]:
            digitax_id = response_data.get("id") or response_data.get("party_id")
            if digitax_id:
                frappe.db.set_value("Customer", customer.name, {
                    "digitax_customer_id": digitax_id,
                    "digitax_sync_status": "Success"
                }, update_modified=False)
                frappe.db.commit()

                log_entry.status = "Success"
                log_entry.insert(ignore_permissions=True)
                frappe.db.commit()

                return {
                    "status": "success",
                    "digitax_id": digitax_id,
                    "message": f"Customer integrated with Digitax. ID: {digitax_id}"
                }
            else:
                log_entry.insert(ignore_permissions=True)
                frappe.db.commit()
                return {
                    "status": "failed",
                    "message": "Digitax returned success but no ID found in response."
                }
        else:
            frappe.db.set_value("Customer", customer.name, "digitax_sync_status", "Failed", update_modified=False)
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()

            return {
                "status": "failed",
                "message": f"Digitax API returned status {response.status_code}: {response.text}"
            }

    except Exception as e:
        try:
            frappe.db.set_value("Customer", customer.name, "digitax_sync_status", "Failed", update_modified=False)
        except Exception:
            pass

        log_entry.response = str(e)
        try:
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

        frappe.log_error(frappe.get_traceback(), "Digitax Customer Integration Exception")
        return {
            "status": "failed",
            "message": f"An error occurred: {str(e)}"
        }
