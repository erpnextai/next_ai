// Copyright (c) 2025, NextAI Team and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["NextAI Daily Usage Summary"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -10),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "user",
            "label": "User",
            "fieldtype": "Link",
            "options": "User",
            "default": frappe.session.user,
            "reqd": 0
        }
	]
};
