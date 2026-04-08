import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def hsn_search(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """
        SELECT
            name,
            description
        FROM `tabHSN Code`
        WHERE
            name LIKE %(txt)s
            OR description LIKE %(txt)s
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        },
    )