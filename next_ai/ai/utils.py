import frappe
from frappe.utils import now_datetime


def nextai_usage_log_create(**kwargs):
    '''
        This funtion is used to create usage log for nextai usage it should contains the 
        neccessary details to create the usage log
    '''
    try:
        doc = frappe.new_doc("NextAI Usage Log")
        kwargs["usage_at"] = now_datetime()
        doc.update(kwargs)
        doc.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Nextai Usage Log Create Failed")
