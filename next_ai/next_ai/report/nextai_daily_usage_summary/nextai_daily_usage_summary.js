// Copyright (c) 2025, Antony Praveenkumar Moses and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["NextAI Daily Usage Summary"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -10),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        }
	]
};
