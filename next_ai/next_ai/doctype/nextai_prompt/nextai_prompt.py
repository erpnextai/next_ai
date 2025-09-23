# Copyright (c) 2025, NextAI Team and contributors
# For license information, please see license.txt

import frappe
import re
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

from next_ai.ai.prompt import PROMPTS

class NextAIPrompt(Document):
	def validate(self):
		if self.enable:
			self.validate_user_specific()
			self.validate_duplicate()
		self.validate_prompt_input()

	def validate_duplicate(self):
		"""
		1. Validation for saving duplicates 
		→ based on doctype and the fieldname. 
		Only one record should exist.
		"""
		duplicate = frappe.db.get_value(
			"NextAI Prompt",
			{
				"ref_doctype": self.ref_doctype,
				"field_name": self.field_name,
				"is_user_specific": self.is_user_specific,
				"user": self.user,
				"enable": 1,
				"name": ["!=", self.name]   # exclude self while editing
			},
			"name"
		)
		if duplicate:
			link = get_link_to_form("NextAI Prompt", duplicate)
			frappe.throw(
				_("Duplicate Entry: A prompt already exists for DocType <b>{0}</b> and Field <b>{1}</b>. {2}")
				.format(self.ref_doctype, self.field_name, link)
			)


	def validate_user_specific(self):
		"""
		2. Only one record can be unchecked for user specific 
		→ based on doctype and fieldname.
		"""
		if not self.is_user_specific:  # unchecked
			other = frappe.db.get_value(
				"NextAI Prompt",
				{
					"ref_doctype": self.ref_doctype,
					"field_name": self.field_name,
					"is_user_specific": 0,
					"enable": 1,
					"name": ["!=", self.name]
				},
				"name"
			)
			if other:
				link = get_link_to_form("NextAI Prompt", other)
				frappe.throw(
					_("Only one <b>Organization-wide</b> prompt is allowed for DocType <b>{0}</b> and Field <b>{1}</b>. {2}")
					.format(self.ref_doctype, self.field_name, link)
				)

	def validate_prompt_input(self):
		"""
		3. {Input} string must appear exactly once in the prompt.
		"""
		if self.prompt:
			matches = re.findall(r"\{input\}", self.prompt, flags=re.IGNORECASE)
			count = len(matches)
			if count == 0:
				frappe.throw(_("The prompt must contain <b>{Input}</b> exactly once."))
			elif count > 1:
				frappe.throw(_("The prompt contains <b>{input}</b> {count} times. Only once is allowed.".format(count=count, input="{Input}")))



@frappe.whitelist(methods=['POST'])
def get_field_type_fielname(ref_doctype:str):
	"""
	Get the field details of the given doctype.
	"""
	query = """
	SELECT
		parent AS doc_type,
		label,
		fieldname,
		fieldtype
	FROM
		`tabDocField`
	WHERE
		parent = '{ref_doctype}'
		AND fieldtype IN ('Markdown Editor', 'Small Text', 'Long Text', 'Text', 'HTML Editor', 'Text Editor', 'Code')

	UNION ALL

	SELECT
		dt AS doc_type,
		label,
		fieldname,
		fieldtype
	FROM
		`tabCustom Field`
	WHERE
		dt = '{ref_doctype}'
		AND fieldtype IN ('Markdown Editor', 'Small Text', 'Long Text', 'Text', 'HTML Editor', 'Text Editor', 'Code')
	ORDER BY label;
	""".format(ref_doctype=ref_doctype)

	data = frappe.db.sql(query, as_dict=True)
	
	temp = {}
	for i in data:
		if i['label'] not in temp:
			temp[i['label']] = 1
		else:
			temp[i['label']] = temp[i['label']] + 1
			i['label'] = f"{i['label']} {temp[i['label']]}"
	

	return data


@frappe.whitelist()
def filter_user_field(doctype, txt, searchfield, start, page_len, filters):
    user = frappe.session.user
    roles = frappe.get_roles(user)

    # Case 1: System Manager → all employees
    if "System Manager" in roles:
        return frappe.db.sql("""
            SELECT name
            FROM `tabUser`
            WHERE {searchfield} LIKE %s
            LIMIT %s, %s
        """.format(searchfield=searchfield),
        ("%%%s%%" % txt, start, page_len))

    # Find Employee linked with current user
    emp = frappe.db.get_value("Employee", {"user_id": user}, "name")

    if emp:
        # Case 2: user has Employee record → show employees reporting to them
        return frappe.db.sql("""
            SELECT user_id
            FROM `tabEmployee`
            WHERE (name = %s OR reports_to = %s)
            AND {searchfield} LIKE %s
            LIMIT %s, %s
        """.format(searchfield=searchfield),
        (emp, emp, "%%%s%%" % txt, start, page_len))

    # Case 3: user has no Employee record → show only themselves
    return [(user,)]


@frappe.whitelist()
def generate_prompt(field_type: str):
	prompt_template = PROMPTS.get(field_type, '')
	return prompt_template


@frappe.whitelist()
def validate_enable_check(ref_doctype, field_name, user, is_user_specific):
	duplicate = frappe.db.get_value(
		"NextAI Prompt",
		{
			"ref_doctype": ref_doctype,
			"field_name": field_name,
			"is_user_specific": is_user_specific,
			"user": user if user else None,
			"enable": 1,
		},
		"name"
	)
	if duplicate:
		link = get_link_to_form("NextAI Prompt", duplicate)
		frappe.msgprint(
			_("Duplicate Entry: A prompt already exists for DocType <b>{0}</b> and Field <b>{1}</b>. {2}")
			.format(ref_doctype, field_name, link)
		)

		return False
	
	return True


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    # Allow System Managers to see all
    if "System Manager" in frappe.get_roles(user):
        return None

    # Restrict other users to only see records they created
    return f"`tabNextAI Prompt`.owner = '{user}' OR `tabNextAI Prompt`.user = '{user}'"
