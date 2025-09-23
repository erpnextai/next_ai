# Copyright (c) 2025, NextAI Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class NextAIUsageLog(Document):
	pass


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    # Allow System Managers to see all
    if "System Manager" in frappe.get_roles(user):
        return None

    # Restrict other users to only see records they created
    return f"`tabNextAI Usage Log`.owner = '{user}' OR `tabNextAI Usage Log`.user = '{user}'"