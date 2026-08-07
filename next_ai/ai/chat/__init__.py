"""
NextAI Chat.

All chat-related backend functions and methods live under this package,
kept fully isolated from the rest of `next_ai.ai` so this feature can
never affect the existing field-level AI / parsing features.

    permissions.py  -> strict `NextAI Chat` role gate
    models.py       -> cached NextAI Settings + active model listing
    context.py      -> page/doctype context extraction
    tools.py        -> read-only tool registry used by the agent
    agent.py         -> the tool-calling agent loop

This file only exposes the whitelisted HTTP endpoints the frontend calls
(`public/js/chat/chat.js`). Business logic itself stays in the modules above.
"""

import frappe
from frappe import _

# NOTE: get_chat_access/get_models are read-only but still accept POST -
# frappe.call() sends POST by default unless the caller passes
# `type: "GET"` explicitly, and chat.js doesn't. A GET-only whitelist here
# caused every call to 403 with "Not permitted" (frappe.handler.is_valid_http_method),
# confirmed via a live browser test.

from next_ai.ai.chat.permissions import assert_chat_access, has_chat_access
from next_ai.ai.chat.models import get_active_models, clear_cache as _clear_cache  # noqa: F401 (re-export)
from next_ai.ai.chat.agent import NextAIChatAgent


@frappe.whitelist(methods=["GET", "POST"])
def get_chat_access():
	"""
	Used by chat.js on desk load / shortcut press to decide whether the
	panel is allowed to open at all. Never throws - returns a flag instead,
	so the frontend can show the exact "please contact the administrator"
	message required by chat.md instead of a generic error toast.

	Deliberately calls `has_chat_access()` (raw `Has Role` check) rather than
	`frappe.get_roles()` membership - the latter special-cases Administrator
	to return every role in the system, which would incorrectly let
	Administrator open the chat without the role actually being assigned.
	"""
	return {"has_access": has_chat_access()}


@frappe.whitelist(methods=["GET", "POST"])
def get_models():
	"""Return the cached list of active models. Never includes the api_key."""
	assert_chat_access()
	return {"status_code": 200, "status": "success", "message": get_active_models()}


@frappe.whitelist(methods=["POST"])
def send_message(**kwargs):
	"""
	Single turn of the chat. The client resends the running in-memory
	transcript on every call (nothing is persisted server-side), along with
	the current page/doctype context and any attached file urls.

	Expected kwargs:
		message: str                 - the new user message
		history: list[dict] | str    - prior turns of THIS conversation only: [{role, content}, ...]
		model_name: str | None       - explicitly selected model (optional)
		context: dict | str | None   - {route: [...], doctype, docname} describing where the user is
		attachments: list[str] | str - list of File doc names/urls attached to this message
	"""
	assert_chat_access()

	data = frappe._dict(kwargs)
	message = (data.get("message") or "").strip()
	if not message:
		frappe.throw(_("Message cannot be empty."))

	# frappe.call() JSON-encodes non-primitive args client-side; since these
	# endpoints take **kwargs (no per-field type hints), they arrive here as
	# raw JSON strings and must be parsed back explicitly.
	agent = NextAIChatAgent(
		message=message,
		history=frappe.parse_json(data.get("history")) or [],
		model_name=data.get("model_name") or None,
		context=frappe.parse_json(data.get("context")) or {},
		attachments=frappe.parse_json(data.get("attachments")) or [],
	)
	response = agent.run()
	return {"status_code": 200, "status": "success", "message": response}
