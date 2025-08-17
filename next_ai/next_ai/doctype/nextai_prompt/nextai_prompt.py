# Copyright (c) 2025, Antony Praveenkumar Moses and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from next_ai.ai.prompt import PROMPTS

class NextAIPrompt(Document):
	pass


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