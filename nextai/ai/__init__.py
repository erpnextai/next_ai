import frappe


@frappe.whitelist()
def get_field_info(**kwargs):
    return {"status": "success"}

