# Copyright (c) 2025, Antony Praveenkumar Moses and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

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
	return data