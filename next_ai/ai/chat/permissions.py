"""
Strict access control for NextAI Chat.

Deliberately does NOT use `frappe.only_for()` - that helper silently lets
`Administrator` (and, in some Frappe versions, System Manager) bypass the
check. chat.md is explicit: "Strictly the user should have this role even
if it's a System Manager can't access this - only the NextAI Chat role
users can use this feature." So this is a plain, unconditional role check.
"""

import frappe
from frappe import _

CHAT_ROLE = "NextAI Chat"


def has_chat_access(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False

	# Deliberately NOT `CHAT_ROLE in frappe.get_roles(user)`: Frappe's
	# get_roles() special-cases Administrator to return every role in the
	# system (see frappe.permissions.get_roles), which would silently let
	# Administrator through. chat.md requires an actual explicit
	# `NextAI Chat` role assignment, with no exception for Administrator or
	# System Manager - so check the raw `Has Role` assignment instead.
	return bool(frappe.db.exists("Has Role", {"parenttype": "User", "parent": user, "role": CHAT_ROLE}))


def assert_chat_access(user: str | None = None) -> None:
	"""Raise frappe.PermissionError with the exact message chat.md requires."""
	if not has_chat_access(user):
		frappe.throw(
			_(
				"You don't have access to the NextAI Chat. "
				"Please contact the administrator to enable the {0} role."
			).format(f"<b>{CHAT_ROLE}</b>"),
			exc=frappe.PermissionError,
			title=_("Access Restricted"),
		)
