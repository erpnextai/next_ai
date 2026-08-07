"""
Cached access to NextAI Settings and the active NextAI Model Info list.

Restriction from chat.md: "avoid hitting the database multiple times, hit
only if requires" and "don't store secret key in JS window context - use
the cache data retrieve, instead of storing the api_key in front-end take
it from the cache."

Everything here is read through `frappe.cache()` (server-side Redis, never
reachable from the browser). The cache is invalidated by the `on_update` /
`on_trash` hooks wired in `hooks.py` for `NextAI Settings` and
`NextAI Model Info`, so a key/model change takes effect immediately instead
of waiting out a TTL.
"""

import frappe
from frappe import _

SETTINGS_CACHE_KEY = "nextai_chat:settings"
MODELS_CACHE_KEY = "nextai_chat:active_models"
CACHE_TTL = 60 * 30  # 30 min safety-net TTL, in case a doc is edited via a path that skips hooks (e.g. direct SQL)


def _load_settings() -> dict:
	doc = frappe.get_cached_doc("NextAI Settings")
	return {
		"platform": doc.platform,
		"model_name": doc.model_name,
		"auto_switch_model_on_rpm": doc.auto_switch_model_on_rpm,
		"api_key": doc.get_password("api_key", raise_exception=False),
	}


def _cached(key: str, generator) -> object:
	"""frappe.cache().get_value()'s own `generator` kwarg does not honor
	`expires_in_sec` (that parameter only exists on `set_value`), so a
	generated value would be cached forever. Do the get/generate/set-with-TTL
	steps explicitly instead."""
	value = frappe.cache().get_value(key, expires=True)
	if value is None:
		value = generator()
		frappe.cache().set_value(key, value, expires_in_sec=CACHE_TTL)
	return value


def get_settings() -> frappe._dict:
	"""Cached NextAI Settings, including the decrypted api_key. Server-side use only."""
	return frappe._dict(_cached(SETTINGS_CACHE_KEY, _load_settings))


def _load_active_models() -> list[dict]:
	settings = get_settings()
	return frappe.db.get_all(
		"NextAI Model Info",
		filters={"platform": settings.platform, "is_active": 1},
		fields=["model_name", "verbose", "platform", "knowledge_cutoff"],
		order_by="creation desc",
	)


def get_active_models() -> list[dict]:
	"""Cached, client-safe list of active models (no secrets)."""
	return _cached(MODELS_CACHE_KEY, _load_active_models)


def validate_settings(settings: frappe._dict) -> None:
	if not settings.model_name:
		frappe.throw(_("Model name is not set in NextAI Settings. Please configure the model name."))
	if not settings.platform:
		frappe.throw(_("Platform is not set in NextAI Settings. Please configure the platform."))
	if not settings.api_key:
		frappe.throw(_("API Key is not set in NextAI Settings. Please configure the API Key."))


def clear_cache(doc=None, method=None):
	"""Hooked to on_update/on_trash of NextAI Settings and NextAI Model Info."""
	frappe.cache().delete_value(SETTINGS_CACHE_KEY)
	frappe.cache().delete_value(MODELS_CACHE_KEY)
