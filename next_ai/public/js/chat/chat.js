// NextAI Chat - desk-wide Copilot-style chat panel.
//
// Everything lives under `nextai.chat.*` (frappe.provide), one file, arrow
// functions + async/await throughout, per docs/nextai/chat/chat.md.
//
// All custom CSS classes are prefixed `nextai-chat-*` (see
// public/css/chat/nextai_chat.css) so nothing here collides with Desk's
// own styles.

frappe.provide("nextai.chat");

(() => {
	const CHAT_ROLE = "NextAI Chat";
	// frappe.ui.keys.get_key() always builds the modifier string as
	// alt+shift+ctrl+<key> (alt is prepended last, making it outermost) -
	// registering "ctrl+alt+i" here would silently never match a real
	// Ctrl+Alt+I keydown. Confirmed live: the shortcut showed up in
	// frappe.ui.keys.standard_shortcuts but never fired until this matched
	// get_key()'s actual ordering.
	const SHORTCUT = "alt+ctrl+i";
	const MAX_MESSAGE_CHARS = 8000;

	// -----------------------------------------------------------------
	// Access
	//
	// Deliberately NOT `frappe.user.has_role(CHAT_ROLE)`: that reads
	// `frappe.boot.user.roles`, which Frappe populates via `get_roles()` -
	// and `get_roles()` special-cases Administrator to return every role in
	// the system. That would let Administrator open the chat client-side
	// even without the role actually assigned. Ask the server, which checks
	// the raw `Has Role` assignment (see permissions.has_chat_access), and
	// cache the answer for this page load only - re-checked on full reload.
	// -----------------------------------------------------------------

	let accessPromise = null;

	const hasChatAccess = async () => {
		if (!accessPromise) {
			accessPromise = frappe
				.call({ method: "next_ai.ai.chat.get_chat_access" })
				.then((r) => !!(r.message && r.message.has_access))
				.catch(() => false);
		}
		return accessPromise;
	};

	const showAccessDenied = () => {
		frappe.msgprint({
			title: __("Access Restricted"),
			indicator: "red",
			message: __(
				"You don't have access to the NextAI Chat. Please contact the administrator to enable the {0} role.",
				[`<b>${CHAT_ROLE}</b>`]
			),
		});
	};

	// -----------------------------------------------------------------
	// Context detection ("if in a page, take info from the page; if in a
	// doctype, take it from the doctype; otherwise keep as-is")
	// -----------------------------------------------------------------

	const getCurrentContext = () => {
		const route = frappe.get_route ? frappe.get_route() : [];
		let doctype = null;
		let docname = null;

		if (route && route[0] === "Form" && route[1]) {
			doctype = route[1];
			docname = window.cur_frm && window.cur_frm.doctype === doctype ? window.cur_frm.docname : route[2] || null;
		} else if (route && route[0] === "List" && route[1]) {
			doctype = route[1];
		}

		return { route, doctype, docname };
	};

	const describeContext = ({ route, doctype, docname }) => {
		if (doctype && docname && docname !== "new") return __("Using context from {0}: {1}", [doctype, docname]);
		if (doctype) return __("Using context from {0}", [doctype]);
		if (route && route.length) return __("Using context from current page");
		return __("No page context available");
	};

	// -----------------------------------------------------------------
	// State - created fresh on open(), fully discarded on close()
	// -----------------------------------------------------------------

	const createState = () => ({
		messages: [], // [{role: "user" | "assistant", content: str}]
		attachments: [], // [{file_name, label, is_image}]
		models: [],
		modelName: null,
		minimized: false,
		sending: false,
		$panel: null,
		$fab: null,
	});

	// -----------------------------------------------------------------
	// Rendering
	// -----------------------------------------------------------------

	const buildPanelMarkup = () => `
		<div class="nextai-chat-panel">
			<div class="nextai-chat-header">
				<div class="nextai-chat-header-title">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="nextai-chat-header-icon">
						<path d="M7.657 6.247c.11-.33.576-.33.686 0l.645 1.937a2.89 2.89 0 0 0 1.829 1.828l1.936.645c.33.11.33.576 0 .686l-1.937.645a2.89 2.89 0 0 0-1.828 1.829l-.645 1.936a.361.361 0 0 1-.686 0l-.645-1.937a2.89 2.89 0 0 0-1.828-1.828l-1.937-.645a.361.361 0 0 1 0-.686l1.937-.645a2.89 2.89 0 0 0 1.828-1.828z"/>
					</svg>
					<span>NextAI Chat</span>
				</div>
				<div class="nextai-chat-header-actions">
					<select class="nextai-chat-model-select" title="${__("Active model")}"></select>
					<button type="button" class="btn nextai-chat-icon-btn nextai-chat-minimize-btn" title="${__("Minimize")}">&#8211;</button>
					<button type="button" class="btn nextai-chat-icon-btn nextai-chat-close-btn" title="${__("Close")}">&times;</button>
				</div>
			</div>
			<div class="nextai-chat-context-indicator"></div>
			<div class="nextai-chat-messages"></div>
			<div class="nextai-chat-attachments"></div>
			<div class="nextai-chat-composer">
				<textarea class="form-control nextai-chat-input" rows="2" placeholder="${__("Ask NextAI about this page...")}"></textarea>
				<div class="nextai-chat-composer-actions">
					<button type="button" class="btn btn-default btn-sm nextai-chat-attach-btn">
						<i class="fa fa-paperclip"></i> ${__("Attach")}
					</button>
					<button type="button" class="btn btn-primary btn-sm nextai-chat-send-btn">${__("Send")}</button>
				</div>
			</div>
		</div>
	`;

	const buildFabMarkup = () => `
		<div class="nextai-chat-fab">
			<button type="button" class="nextai-chat-fab-close" title="${__("Close")}">&times;</button>
			<button type="button" class="nextai-chat-fab-open" title="${__("Open NextAI Chat")}">
				<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
					<path d="M7.657 6.247c.11-.33.576-.33.686 0l.645 1.937a2.89 2.89 0 0 0 1.829 1.828l1.936.645c.33.11.33.576 0 .686l-1.937.645a2.89 2.89 0 0 0-1.828 1.829l-.645 1.936a.361.361 0 0 1-.686 0l-.645-1.937a2.89 2.89 0 0 0-1.828-1.828l-1.937-.645a.361.361 0 0 1 0-.686l1.937-.645a2.89 2.89 0 0 0 1.828-1.828z"/>
				</svg>
			</button>
		</div>
	`;

	const appendMessage = (role, content) => {
		const state = nextai.chat.state;
		if (!state) return;
		state.messages.push({ role, content });

		const $messages = state.$panel.find(".nextai-chat-messages");
		const $row = $(`<div class="nextai-chat-message nextai-chat-message-${role}"></div>`);
		const $bubble = $(`<div class="nextai-chat-bubble"></div>`);

		if (role === "assistant") {
			$bubble.html(frappe.markdown(content || ""));
		} else {
			$bubble.text(content || "");
		}

		$row.append($bubble);
		$messages.append($row);
		$messages.scrollTop($messages[0].scrollHeight);
	};

	const setTyping = (isTyping) => {
		const state = nextai.chat.state;
		if (!state) return;
		const $messages = state.$panel.find(".nextai-chat-messages");
		state.$panel.find(".nextai-chat-typing").remove();
		if (isTyping) {
			$messages.append(
				`<div class="nextai-chat-message nextai-chat-message-assistant nextai-chat-typing">
					<div class="nextai-chat-bubble nextai-chat-typing-bubble">
						<span></span><span></span><span></span>
					</div>
				</div>`
			);
			$messages.scrollTop($messages[0].scrollHeight);
		}
	};

	const renderAttachments = () => {
		const state = nextai.chat.state;
		if (!state) return;
		const $wrap = state.$panel.find(".nextai-chat-attachments");
		$wrap.empty();
		state.attachments.forEach((att, idx) => {
			const $chip = $(`
				<span class="nextai-chat-attachment-chip">
					<i class="fa ${att.is_image ? "fa-file-image-o" : "fa-file-text-o"}"></i>
					<span class="nextai-chat-attachment-label"></span>
					<button type="button" class="nextai-chat-attachment-remove">&times;</button>
				</span>
			`);
			$chip.find(".nextai-chat-attachment-label").text(att.label);
			$chip.find(".nextai-chat-attachment-remove").on("click", () => {
				state.attachments.splice(idx, 1);
				renderAttachments();
			});
			$wrap.append($chip);
		});
	};

	const refreshContextIndicator = () => {
		const state = nextai.chat.state;
		if (!state) return;
		state.$panel.find(".nextai-chat-context-indicator").text(describeContext(getCurrentContext()));
	};

	// -----------------------------------------------------------------
	// Models
	// -----------------------------------------------------------------

	const loadModels = async () => {
		const state = nextai.chat.state;
		if (!state) return;
		try {
			const r = await frappe.call({ method: "next_ai.ai.chat.get_models" });
			const models = (r.message && r.message.message) || [];
			state.models = models;
			state.modelName = (models[0] && models[0].model_name) || null;

			const $select = state.$panel.find(".nextai-chat-model-select");
			$select.empty();
			models.forEach((m) => {
				$select.append(`<option value="${frappe.utils.escape_html(m.model_name)}">${frappe.utils.escape_html(m.verbose || m.model_name)}</option>`);
			});
			if (state.modelName) $select.val(state.modelName);
		} catch (e) {
			// Non-fatal: the backend will fall back to the default NextAI Settings model.
			console.error("NextAI Chat: failed to load active models", e);
		}
	};

	// -----------------------------------------------------------------
	// Attachments
	// -----------------------------------------------------------------

	const openAttachDialog = () => {
		new frappe.ui.FileUploader({
			allow_multiple: true,
			folder: "Home/Attachments",
			on_success: (file_doc) => {
				const state = nextai.chat.state;
				if (!state) return;
				state.attachments.push({
					file_name: file_doc.name,
					label: file_doc.file_name,
					is_image: frappe.utils.is_image_file(file_doc.file_url),
				});
				renderAttachments();
			},
		});
	};

	// -----------------------------------------------------------------
	// Send
	// -----------------------------------------------------------------

	const sendMessage = async () => {
		const state = nextai.chat.state;
		if (!state || state.sending) return;

		const $input = state.$panel.find(".nextai-chat-input");
		const text = ($input.val() || "").trim();
		if (!text) return;

		if (text.length > MAX_MESSAGE_CHARS) {
			frappe.show_alert({ message: __("Message is too long."), indicator: "red" });
			return;
		}

		const history = state.messages.slice();
		appendMessage("user", text);
		$input.val("");
		state.sending = true;
		setTyping(true);

		const attachmentNames = state.attachments.map((a) => a.file_name);

		try {
			const r = await frappe.call({
				method: "next_ai.ai.chat.send_message",
				args: {
					message: text,
					history: history,
					model_name: state.modelName,
					context: getCurrentContext(),
					attachments: attachmentNames,
				},
			});
			const reply = r.message && r.message.message;
			appendMessage("assistant", reply || __("Sorry, I couldn't generate a response."));
		} catch (e) {
			const errMessage = (e && e.message) || __("Something went wrong. Please try again.");
			appendMessage("assistant", `⚠️ ${errMessage}`);
		} finally {
			setTyping(false);
			state.sending = false;
		}
	};

	// -----------------------------------------------------------------
	// Layout: open / minimize / close
	// -----------------------------------------------------------------

	const mountPanel = async () => {
		nextai.chat.state = createState();
		const state = nextai.chat.state;

		state.$panel = $(buildPanelMarkup()).appendTo("body");
		state.$fab = $(buildFabMarkup()).appendTo("body").hide();

		$("body").addClass("nextai-chat-open").removeClass("nextai-chat-minimized");

		state.$panel.find(".nextai-chat-minimize-btn").on("click", nextai.chat.minimize);
		state.$panel.find(".nextai-chat-close-btn").on("click", nextai.chat.close);
		state.$panel.find(".nextai-chat-attach-btn").on("click", openAttachDialog);
		state.$panel.find(".nextai-chat-send-btn").on("click", sendMessage);
		state.$panel.find(".nextai-chat-input").on("keydown", (e) => {
			if (e.key === "Enter" && !e.shiftKey) {
				e.preventDefault();
				sendMessage();
			}
		});

		state.$fab.find(".nextai-chat-fab-open").on("click", nextai.chat.expand);
		state.$fab.find(".nextai-chat-fab-close").on("click", nextai.chat.close);

		refreshContextIndicator();
		await loadModels();
		state.$panel.find(".nextai-chat-input").trigger("focus");
	};

	nextai.chat.open = async () => {
		if (!(await hasChatAccess())) {
			showAccessDenied();
			return;
		}
		if (nextai.chat.state) {
			nextai.chat.expand();
			return;
		}
		mountPanel();
	};

	nextai.chat.minimize = () => {
		const state = nextai.chat.state;
		if (!state) return;
		state.minimized = true;
		state.$panel.hide();
		state.$fab.show();
		$("body").removeClass("nextai-chat-open").addClass("nextai-chat-minimized");
	};

	nextai.chat.expand = () => {
		const state = nextai.chat.state;
		if (!state) return;
		state.minimized = false;
		state.$panel.show();
		state.$fab.hide();
		$("body").addClass("nextai-chat-open").removeClass("nextai-chat-minimized");
		refreshContextIndicator();
	};

	nextai.chat.close = () => {
		const state = nextai.chat.state;
		if (!state) return;
		state.$panel.remove();
		state.$fab.remove();
		$("body").removeClass("nextai-chat-open nextai-chat-minimized");
		// Erase all state on close, per chat.md.
		nextai.chat.state = null;
	};

	nextai.chat.toggle = async () => {
		if (nextai.chat.state) {
			// Already open/minimized - closing doesn't need another access
			// check (they clearly opened it already this page load).
			nextai.chat.close();
			return;
		}
		if (!(await hasChatAccess())) {
			showAccessDenied();
			return;
		}
		nextai.chat.open();
	};

	// -----------------------------------------------------------------
	// Boot: shortcut + route-change context refresh
	// -----------------------------------------------------------------

	nextai.chat.state = null;

	$(document).on("app_ready", () => {
		frappe.ui.keys.add_shortcut({
			shortcut: SHORTCUT,
			description: __("Toggle NextAI Chat"),
			action: () => nextai.chat.toggle(),
			ignore_inputs: true,
		});
	});

	frappe.router.on("change", () => {
		if (nextai.chat.state && !nextai.chat.state.minimized) {
			refreshContextIndicator();
		}
	});
})();
