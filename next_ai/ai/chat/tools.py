"""
Read-only tool registry for the NextAI Chat agent.

v1 intentionally ships **read-only** tools only ("this feature strictly
should not affect the other features" - chat.md). New tools (including,
later, write/workflow-style tools) can be added by writing one more
function here and adding it to the list returned by `build_tools()` -
nothing else in `agent.py` needs to change, which is the extensibility
chat.md asks for ("lots of new workflow approaches will come").

Tools are built per-request (`build_tools`) rather than as module-level
singletons because they close over the *current* user's permissions and
the specific attachments/context of this one conversation turn - nothing
here is shared or cached across requests/users.
"""

import frappe
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from next_ai.ai.chat.context import RESTRICTED_DOCTYPES, document_context, as_prompt_text

_MAX_SEARCH_LIMIT = 20
_MAX_ATTACHMENT_CHARS = 6000


def build_tools(current_context: dict, resolved_attachments: dict) -> list:
	"""
	current_context: dict produced by context.build_context() for this turn.
	resolved_attachments: {file_name: {"label": str, "content": str | None, "is_image": bool}}
	                        already permission-checked in agent.py.
	"""

	def get_current_page_context() -> str:
		"""Get the page or DocType record the user currently has open in Frappe Desk.
		Use this whenever the user refers to "this", "the current record", "this page",
		or asks something that depends on where they are right now."""
		return as_prompt_text(current_context)

	class SearchDoctypeArgs(BaseModel):
		doctype: str = Field(description="Exact Frappe DocType name, e.g. 'Sales Invoice'.")
		filters: dict = Field(
			default_factory=dict,
			description="Optional Frappe filter dict, e.g. {\"status\": \"Open\"}.",
		)
		fields: list[str] = Field(
			default_factory=list,
			description="Fields to return. Defaults to ['name', 'modified'] if empty.",
		)
		limit: int = Field(default=10, description=f"Max rows to return (capped at {_MAX_SEARCH_LIMIT}).")

	def search_doctype(doctype: str, filters: dict = None, fields: list[str] = None, limit: int = 10) -> str:
		"""Search records of a DocType the user has read access to. Respects the
		user's normal Frappe permissions - never returns data they couldn't
		otherwise see in the Desk UI. Use this to look up records referenced by
		the user (e.g. "find open Sales Orders for Acme")."""
		if doctype in RESTRICTED_DOCTYPES or not frappe.db.exists("DocType", doctype):
			return f"'{doctype}' is not available to search."

		fields = fields or ["name", "modified"]
		meta = frappe.get_meta(doctype)
		safe_fields = [f for f in fields if f in ("name", "modified", "creation", "owner") or meta.has_field(f)]
		safe_fields = [f for f in safe_fields if meta.get_field(f) is None or meta.get_field(f).fieldtype not in ("Password", "Attach", "Attach Image", "Signature")]
		if not safe_fields:
			safe_fields = ["name", "modified"]

		rows = frappe.get_list(
			doctype,
			filters=filters or {},
			fields=safe_fields,
			limit_page_length=min(int(limit or 10), _MAX_SEARCH_LIMIT),
			order_by="modified desc",
		)
		return frappe.as_json(rows)

	class ReadDocumentArgs(BaseModel):
		doctype: str = Field(description="Exact Frappe DocType name.")
		docname: str = Field(description="The document's `name` (id), usually found via search_doctype first.")

	def read_document(doctype: str, docname: str) -> str:
		"""Read the full field values of one specific document, respecting the
		user's read permission on it. Use after search_doctype to inspect a
		specific record in detail."""
		result = document_context(doctype, docname)
		if result.get("type") != "document":
			return f"Could not read {doctype} '{docname}' - it may not exist or you may not have access."
		return as_prompt_text(result)

	def list_attachments() -> str:
		"""List the files the user attached to this conversation (name + type),
		without their full content. Use this before read_attachment if you're
		not sure which attachment to read."""
		if not resolved_attachments:
			return "No files were attached to this conversation."
		return "\n".join(
			f"- {name} ({'image' if meta['is_image'] else 'text'})"
			for name, meta in resolved_attachments.items()
		)

	class ReadAttachmentArgs(BaseModel):
		file_name: str = Field(description="The attachment's file name, exactly as given by list_attachments.")

	def read_attachment(file_name: str) -> str:
		"""Read the text content of a file the user attached to this
		conversation. Only works for files actually attached to THIS chat -
		it cannot read arbitrary files from the system. Image attachments are
		already visible to you directly and don't need this tool."""
		meta = resolved_attachments.get(file_name)
		if not meta:
			return f"'{file_name}' was not attached to this conversation."
		if meta["is_image"]:
			return f"'{file_name}' is an image and is already provided to you directly - no need to read it as text."
		content = meta.get("content") or ""
		if len(content) > _MAX_ATTACHMENT_CHARS:
			content = content[:_MAX_ATTACHMENT_CHARS] + "\n... (truncated)"
		return content or "(file appears to be empty or unreadable as text)"

	return [
		StructuredTool.from_function(func=get_current_page_context, name="get_current_page_context"),
		StructuredTool.from_function(func=search_doctype, name="search_doctype", args_schema=SearchDoctypeArgs),
		StructuredTool.from_function(func=read_document, name="read_document", args_schema=ReadDocumentArgs),
		StructuredTool.from_function(func=list_attachments, name="list_attachments"),
		StructuredTool.from_function(func=read_attachment, name="read_attachment", args_schema=ReadAttachmentArgs),
	]
