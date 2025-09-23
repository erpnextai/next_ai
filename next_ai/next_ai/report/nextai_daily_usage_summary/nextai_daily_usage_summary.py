# Copyright (c) 2025, NextAI Team
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    query = """
        SELECT 
            DATE(usage_at) AS usage_date,
            DATE_FORMAT(usage_at, '%%b %%d') AS month_day,
            COUNT(*) AS usage_count
        FROM 
            `tabNextAI Usage Log`
        WHERE 1=1
    """

    values = {}

    # --- Handle date filters ---
    if filters.get("from_date") and filters.get("to_date"):
        query += " AND DATE(usage_at) BETWEEN %(from_date)s AND %(to_date)s"
        values.update({
            "from_date": filters["from_date"],
            "to_date": filters["to_date"]
        })
    elif filters.get("from_date"):
        query += " AND DATE(usage_at) >= %(from_date)s"
        values.update({"from_date": filters["from_date"]})
    elif filters.get("to_date"):
        query += " AND DATE(usage_at) <= %(to_date)s"
        values.update({"to_date": filters["to_date"]})
    else:
        # Default: last 10 days
        query += " AND DATE(usage_at) >= DATE_SUB(CURDATE(), INTERVAL 10 DAY)"

    # --- Handle user filter ---
    current_user = frappe.session.user
    selected_user = filters.get("user")

    # check roles
    user_roles = frappe.get_roles(current_user)
    is_system_manager = "System Manager" in user_roles

    if selected_user:
        if not is_system_manager and selected_user != current_user:
            frappe.throw(_("You don't have permission to view other user's data. Only <b>System Managers</b> can."))
        query += " AND user = %(user)s"
        values.update({"user": selected_user})
    else:
        if not is_system_manager:
            query += " AND user = %(user)s"
            values.update({"user": current_user})
        # else System Manager sees all

    query += " GROUP BY DATE(usage_at) ORDER BY usage_date DESC"

    data = frappe.db.sql(query, values, as_dict=True)

    # Columns
    columns = [
        {"label": "Usage Date", "fieldname": "usage_date", "fieldtype": "Date", "width": 120},
        {"label": "Month Day", "fieldname": "month_day", "fieldtype": "Data", "width": 100},
        {"label": "Usage Count", "fieldname": "usage_count", "fieldtype": "Int", "width": 120},
    ]

    return columns, data
