"""
The NextAI Chat agent: a small, hand-rolled tool-calling (ReAct-style) loop.

chat.md requires an "agentic solution" that can grow to support future
workflow-style tool use, not a single prompt -> response call. `langgraph`
is not installed and no new package may be added, but that's not actually
a blocker: `ChatGoogleGenerativeAI.bind_tools()` (already available via
`langchain-google-genai`) is enough to hand-roll the standard loop:

    invoke -> model asks for tool(s) -> we execute them -> feed results
    back as ToolMessages -> invoke again -> ... -> model returns final text

This mirrors the resilience patterns already used by `NextAILLM` in
`next_ai/ai/__init__.py` (settings validation, RPM-triggered model
auto-switch, usage logging via frappe.enqueue) so the chat feature behaves
consistently with the rest of the app instead of introducing a second way
of doing the same thing.
"""

import mimetypes
import os

import frappe
from frappe import _
from google.api_core.exceptions import NotFound, ResourceExhausted
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from next_ai.ai.chat import context as chat_context
from next_ai.ai.chat.models import get_settings, validate_settings
from next_ai.ai.chat.tools import build_tools
from next_ai.ai.utils import nextai_usage_log_create

MAX_TOOL_ITERATIONS = 5
MAX_MESSAGE_CHARS = 8000
IMAGE_MIME_PREFIXES = ("image/",)
TEXT_READ_LIMIT_BYTES = 200_000  # don't try to decode huge/binary files as text


class NextAIChatAgent:
	def __init__(self, message: str, history: list, model_name: str | None, context: dict, attachments: list):
		self.user_input = message
		self._validate_message_length(message)

		self.history = history or []
		self.requested_model = model_name
		self.raw_context = context or {}
		self.raw_attachments = attachments or []

		self.settings = get_settings()
		validate_settings(self.settings)
		self.current_model = self.requested_model or self.settings.model_name

		self.page_context = chat_context.build_context(
			route=self.raw_context.get("route"),
			doctype=self.raw_context.get("doctype"),
			docname=self.raw_context.get("docname"),
		)
		self.resolved_attachments, self.image_parts = self._resolve_attachments(self.raw_attachments)

		self._is_error = False

	def _validate_message_length(self, message: str) -> None:
		if len(message) > MAX_MESSAGE_CHARS:
			frappe.throw(_("Message exceeds the maximum limit of {0} characters.").format(MAX_MESSAGE_CHARS))

	def _resolve_attachments(self, attachments: list) -> tuple[dict, list]:
		"""Permission-checks each attached File doc and reads text content
		up front (kept in-memory for this request only - never cached, never
		written anywhere). Images are prepared as multimodal message parts."""
		resolved = {}
		image_parts = []

		for file_name in attachments:
			if not file_name or not frappe.db.exists("File", file_name):
				continue
			if not frappe.has_permission("File", "read", doc=file_name, user=frappe.session.user):
				continue

			file_doc = frappe.get_doc("File", file_name)
			mime = mimetypes.guess_type(file_doc.file_name or "")[0] or ""
			is_image = mime.startswith(IMAGE_MIME_PREFIXES)

			label = file_doc.file_name or file_name
			entry = {"label": label, "is_image": is_image, "content": None}

			try:
				raw = file_doc.get_content()
			except Exception:
				raw = None

			if raw and is_image:
				import base64

				image_parts.append(
					{
						"type": "image_url",
						"image_url": f"data:{mime};base64,{base64.b64encode(raw).decode()}",
					}
				)
			elif raw and len(raw) <= TEXT_READ_LIMIT_BYTES:
				try:
					entry["content"] = raw.decode("utf-8", errors="ignore")
				except Exception:
					entry["content"] = None

			resolved[label] = entry

		return resolved, image_parts

	def _system_prompt(self) -> str:
		# The explicit "ALREADY accurate... never claim you don't know it"
		# wording below is load-bearing, not filler: gemini-2.5-flash-lite
		# (this app's default model) was empirically observed to ignore the
		# injected context and falsely claim it had no information about the
		# current page whenever tools were bound alongside a softer system
		# prompt - even though the same context worked fine without tools,
		# and gemini-2.5-flash (non-lite) handled the softer prompt
		# correctly by calling get_current_page_context on its own. This
		# stronger phrasing was verified live to fix flash-lite's behavior.
		return (
			"You are NextAI Chat, an assistant embedded inside a Frappe/ERPNext desk. "
			"The 'Current context' section below is ALREADY accurate, live information "
			"about exactly what the user is looking at right now - it is not a guess, "
			"and you must never claim you don't know it or don't have access to it. "
			"Answer directly from it. Only call get_current_page_context if you need to "
			"double-check it changed. You also have read-only tools to search/read other "
			"records and read files the user attached to this conversation - use them "
			"whenever you need real data beyond the current context instead of guessing. "
			"Be concise and use Markdown for structure when helpful.\n\n"
			f"Current context:\n{chat_context.as_prompt_text(self.page_context)}"
		)

	def _build_messages(self) -> list:
		messages = [SystemMessage(content=self._system_prompt())]

		for turn in self.history:
			role = (turn or {}).get("role")
			content = (turn or {}).get("content") or ""
			if not content:
				continue
			if role == "assistant":
				messages.append(AIMessage(content=content))
			else:
				messages.append(HumanMessage(content=content))

		if self.image_parts:
			messages.append(HumanMessage(content=[{"type": "text", "text": self.user_input}, *self.image_parts]))
		else:
			messages.append(HumanMessage(content=self.user_input))

		return messages

	def _get_llm(self, model_name: str):
		try:
			if self.settings.platform == "Gemini":
				os.environ["GOOGLE_API_KEY"] = self.settings.api_key
				return ChatGoogleGenerativeAI(model=model_name)
			frappe.throw(_("Unsupported platform: {0}").format(self.settings.platform))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Error in NextAIChatAgent._get_llm")
			frappe.throw(_("Error initializing the chat model: {0}").format(model_name))

	def _get_next_model(self, current_model: str) -> str:
		models = frappe.db.get_all(
			"NextAI Model Info",
			filters={"platform": self.settings.platform, "is_active": 1},
			fields=["model_name"],
			order_by="creation desc",
		)
		names = [m["model_name"] for m in models]
		if not names:
			frappe.throw(_("No active model info found for the platform {0}.").format(self.settings.platform))

		if current_model in names:
			idx = names.index(current_model)
			next_model = names[(idx + 1) % len(names)]
		else:
			next_model = names[0]

		if next_model == current_model:
			frappe.throw(_("<b>RPM limit</b> has been reached for all models. Please try again later."))
		return next_model

	def run(self) -> str:
		try:
			return self._run_loop(self.current_model)
		except (ResourceExhausted, NotFound) as e:
			if isinstance(e, NotFound):
				frappe.log_error(f"Model not found {self.current_model}\n{frappe.get_traceback()}", "NextAI Chat Model NotFound")
				frappe.db.set_value("NextAI Model Info", self.current_model, "is_active", 0)
			else:
				frappe.log_error(frappe.get_traceback(), f"RPM limit reached {self.current_model} in NextAIChatAgent.run")

			if self.settings.auto_switch_model_on_rpm:
				self.current_model = self._get_next_model(self.current_model)
				self._is_error = True
				return self.run()

			if isinstance(e, NotFound):
				frappe.throw(_("The selected model <b>{0}</b> is not active. Please choose another active model.").format(self.current_model))
			frappe.throw(_("RPM limit reached for the current model {0}. Please try again later.").format(self.current_model))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Critical NextAIChatAgent.run")
			frappe.throw(_("You have reached the limit or the system is too busy. Please try again later."))

	def _run_loop(self, model_name: str) -> str:
		tools = build_tools(self.page_context, self.resolved_attachments)
		tools_by_name = {t.name: t for t in tools}
		llm = self._get_llm(model_name).bind_tools(tools)

		messages = self._build_messages()
		final_text = ""

		for _iteration in range(MAX_TOOL_ITERATIONS):
			ai_message = llm.invoke(messages)
			messages.append(ai_message)

			if not ai_message.tool_calls:
				final_text = ai_message.content if isinstance(ai_message.content, str) else str(ai_message.content)
				break

			for call in ai_message.tool_calls:
				tool = tools_by_name.get(call["name"])
				try:
					result = tool.invoke(call["args"]) if tool else f"Unknown tool: {call['name']}"
				except Exception:
					frappe.log_error(frappe.get_traceback(), f"NextAI Chat tool failed: {call.get('name')}")
					result = f"Tool '{call['name']}' failed to run."
				messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
		else:
			# Loop exhausted without a final answer - ask the model to wrap up without more tools.
			final_message = llm.invoke(messages + [HumanMessage(content="Please answer now with what you know, without calling any more tools.")])
			final_text = final_message.content if isinstance(final_message.content, str) else str(final_message.content)

		if self._is_error:
			# We only get here after successfully recovering from a RPM/NotFound
			# error on another model - persist the working model, same recovery
			# behavior as NextAILLM.get_llm_response in next_ai/ai/__init__.py.
			settings_doc = frappe.get_doc("NextAI Settings")
			settings_doc.model_name = model_name
			settings_doc.save(ignore_permissions=True, ignore_version=True)

		frappe.enqueue(
			nextai_usage_log_create,
			queue="short",
			platform=self.settings.platform,
			user=frappe.session.user,
			model_name=model_name,
			sub_type="Chat",
			question=self.user_input,
			prompt=self._system_prompt(),
			response=final_text,
			ref_doctype=self.page_context.get("doctype"),
			field_name="/".join(str(p) for p in self.raw_context.get("route") or []),
		)

		return final_text
