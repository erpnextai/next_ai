"""
Page / DocType context extraction.

chat.md: "If it's in a page it's supposed to take the information from the
page. If it's in a doctype it's supposed to take it from the doctype.
People can randomly open in some place, that time keep as it is."

The browser tells us *where* it is (route/doctype/docname) via
`nextai.chat.getCurrentContext()` in chat.js; this module is the only place
that actually reads document data, and it always re-checks permissions
server-side - the frontend's notion of "current doctype" is not trusted.
"""

import frappe

# Never surface these to the LLM: internal bookkeeping metadata, secrets,
# or fields too heavy to be useful context (mirrors the low-priority /
# sensitive column guidance used across next_ai).
_EXCLUDED_FIELDNAMES = {"_user_tags", "_comments", "_assign", "_liked_by"}
_EXCLUDED_FIELDTYPES = {"Password", "Attach", "Attach Image", "Signature"}
_MAX_FIELD_CHARS = 2000

# Doctypes the chat agent's context/search_doctype/read_document tools
# should never touch. Intentionally neutral (empty) for now, per explicit
# instruction - every doctype the requesting user can otherwise read is
# allowed. Field-level protection still applies regardless (Password/Attach/
# Signature fields are always stripped, see _EXCLUDED_FIELDTYPES below, and
# frappe.has_permission()/frappe.get_list() still enforce normal Frappe
# permissions) - this set is only for doctypes to exclude on top of that.
# Shared with tools.py's search_doctype/read_document tools.
RESTRICTED_DOCTYPES = set()


def build_context(route: list | None, doctype: str | None, docname: str | None) -> dict:
	"""
	Returns one of:
	  {"type": "document", "doctype": ..., "docname": ..., "fields": {...}}
	  {"type": "new_document", "doctype": ..., "meta": {...}}
	  {"type": "page", "route": [...]}
	  {"type": "none"}
	"""
	route = route or []

	if doctype and doctype in RESTRICTED_DOCTYPES:
		return {"type": "none"}

	if doctype and docname and docname != "new":
		return document_context(doctype, docname)

	if doctype and (not docname or docname == "new"):
		return _newdocument_context(doctype)

	if route:
		return {"type": "page", "route": route}

	return {"type": "none"}


def document_context(doctype: str, docname: str) -> dict:
	if not frappe.db.exists("DocType", doctype):
		return {"type": "none"}

	if not frappe.has_permission(doctype, "read", doc=docname, user=frappe.session.user):
		return {"type": "none"}

	try:
		doc = frappe.get_doc(doctype, docname)
	except frappe.DoesNotExistError:
		return {"type": "none"}

	meta = frappe.get_meta(doctype)
	fields = {}
	for df in meta.fields:
		if df.fieldname in _EXCLUDED_FIELDNAMES or df.fieldtype in _EXCLUDED_FIELDTYPES:
			continue
		value = doc.get(df.fieldname)
		if value in (None, ""):
			continue
		value = str(value)
		if len(value) > _MAX_FIELD_CHARS:
			value = value[:_MAX_FIELD_CHARS] + "... (truncated)"
		fields[df.fieldname] = value

	# Always include the standard identifying fields even if not explicit DocFields.
	fields.setdefault("name", doc.name)
	if meta.has_field("status") is False and doc.get("docstatus") is not None:
		fields["docstatus"] = doc.docstatus

	return {"type": "document", "doctype": doctype, "docname": docname, "fields": fields}


def _newdocument_context(doctype: str) -> dict:
	if not frappe.db.exists("DocType", doctype):
		return {"type": "none"}
	if not frappe.has_permission(doctype, "create", user=frappe.session.user):
		return {"type": "none"}

	meta = frappe.get_meta(doctype)
	field_summary = [
		{"fieldname": df.fieldname, "label": df.label, "fieldtype": df.fieldtype}
		for df in meta.fields
		if df.fieldname not in _EXCLUDED_FIELDNAMES and df.fieldtype not in _EXCLUDED_FIELDTYPES
	]
	return {"type": "new_document", "doctype": doctype, "meta": field_summary}


def as_prompt_text(context: dict) -> str:
	"""Render the context dict into a short block for the system prompt."""
	ctx_type = context.get("type")

	if ctx_type == "document":
		lines = [f"The user is currently viewing {context['doctype']} '{context['docname']}'."]
		for field, value in context["fields"].items():
			lines.append(f"- {field}: {value}")
		return "\n".join(lines)

	if ctx_type == "new_document":
		field_list = ", ".join(f.get("label") or f.get("fieldname") for f in context["meta"])
		return (
			f"The user is creating a new {context['doctype']} record (not yet saved). "
			f"Available fields: {field_list}"
		)

	if ctx_type == "page":
		return f"The user is on desk route: {' / '.join(str(p) for p in context['route'])}"

	return "No specific page or document context is available for this conversation."
