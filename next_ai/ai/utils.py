import frappe
from frappe.utils import now_datetime
from datetime import date, datetime



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


def get_parser_type_details() -> dict:
    parser_type_details = {
        "Autocomplete": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Attach": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Attach Image": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Barcode": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Button": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Check": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Code": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Color": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Column Break": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Currency": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Data": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": True
        },
        "Date": {
            "type": date,
            "default_description": "A calendar date in YYYY-MM-DD format.",
            "is_active": True
        },
        "Datetime": {
            "type": datetime,
            "default_description": "A full timestamp in YYYY-MM-DD HH:MM:SS format.",
            "is_active": True
        },
        "Duration": {
            "type": int,
            "default_description": "Duration value represented in total seconds (e.g., 1 hour = 3600 seconds).",
            "is_active": False
        },
        "Dynamic Link": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Float": {
            "type": float,
            "default_description": "A floating-point number with decimal precision (e.g., 3.142).",
            "is_active": True
        },
        "Fold": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Geolocation": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Heading": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "HTML": {
            "type": str,
            "default_description": "HTML content supported with Bootstrap styling and components.",
            "is_active": True
        },
        "HTML Editor": {
            "type": str,
            "default_description": "HTML content supported with Bootstrap styling and components.",
            "is_active": True
        },
        "Icon": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Image": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Int": {
            "type": int,
            "default_description": "An integer value without decimals.",
            "is_active": True
        },
        "JSON": {
            "type": str,
            "default_description": "A valid JSON string.",
            "is_active": False
        },
        "Link": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Long Text": {
            "type": str,
            "default_description": "A long text value.",
            "is_active": True
        },
        "Markdown Editor": {
            "type": str,
            "default_description": "A markdown formatted text value.",
            "is_active": True
        },
        "Password": {
            "type": str,
            "default_description": "A secure password string.",
            "is_active": True
        },
        "Percent": {
            "type": float,
            "default_description": "A percentage value represented as a number.",
            "is_active": False
        },
        "Phone": {
            "type": str,
            "default_description": "A phone number including the country code. Default country code is +91. example format +91-18001234567",
            "is_active": True
        },
        "Read Only": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Rating": {
            "type": str,
            "default_description": "A rating value between 0.0 and 1.0 in increments of 0.1 (allowed: 0.0, 0.1, 0.2 ... 0.9, 1.0).",
            "is_active": True
        },
        "Section Break": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Select": {
            "type": str,
            "default_description": "Select one value from the predefined options (case-sensitive; must match exactly). The options are: Option 1, Option 2, Option 3.",
            "is_active": True
        },
        "Signature": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Small Text": {
            "type": str,
            "default_description": "Provide a short single-line text value.",
            "is_active": True
        },
        "Tab Break": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Table": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Table MultiSelect": {
            "type": str,
            "default_description": "Get appropriate data for the field",
            "is_active": False
        },
        "Text": {
            "type": str,
            "default_description": "Provide multi-line plain text content.",
            "is_active": True
        },
        "Text Editor": {
            "type": str,
            "default_description": "Provide rich-text HTML content produced by a Quill editor. Example HTML <div class=\"ql-editor read-mode\"><p>Hi I'm an example content, This is <strong>BOLD</strong></p></div>",
            "is_active": True
        },
        "Time": {
            "type": str,
            "default_description": "Provide a valid time value in HH:MM:SS (24-hour) format. Example: 23:59:59",
            "is_active": True
        }
    }
    return parser_type_details

