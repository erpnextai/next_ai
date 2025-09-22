app_name = "next_ai"
app_title = "Next AI"
app_publisher = "Antony Praveenkumar Moses"
app_description = "Next AI is an AI-enabled application designed for seamless content generation and enhancement. With the power of advanced language models, it helps users create high-quality content and intelligently improve existing text, making writing faster, smarter, and more effective."
app_email = "antonykumar15898@gmail.com"
app_license = "Custom Non-Commercial License"

fixtures = [
    {"dt": "NextAI Model Info"},
    {
        "dt": "Role",
        "filters": [
            ["name", "in", ["NextAI User"]]
        ]
    },
    {
        "dt": "Custom HTML Block",
        "filters": [
            ["name", "in", ["NextAI Header", "NextAI Header 2"]]
        ]
    }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/next_ai/css/next_ai.css"
app_include_js = "/assets/next_ai/js/next_ai.js"

# include js, css files in header of web template
# web_include_css = "/assets/next_ai/css/next_ai.css"
# web_include_js = "/assets/next_ai/js/next_ai.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "next_ai/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "next_ai.utils.jinja_methods",
# 	"filters": "next_ai.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "next_ai.install.before_install"
# after_install = "next_ai.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "next_ai.uninstall.before_uninstall"
# after_uninstall = "next_ai.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "next_ai.utils.before_app_install"
# after_app_install = "next_ai.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "next_ai.utils.before_app_uninstall"
# after_app_uninstall = "next_ai.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "next_ai.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"NextAI Prompt": "next_ai.next_ai.doctype.nextai_prompt.nextai_prompt.get_permission_query_conditions"
	# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
}
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"next_ai.tasks.all"
# 	],
	"daily": [
		"next_ai.ai.scheduler.delete_old_nextai_usage_logs"
	],
# 	"hourly": [
# 		"next_ai.tasks.hourly"
# 	],
# 	"weekly": [
# 		"next_ai.tasks.weekly"
# 	],
# 	"monthly": [
# 		"next_ai.tasks.monthly"
# 	],
}

# Testing
# -------

# before_tests = "next_ai.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "next_ai.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "next_ai.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["next_ai.utils.before_request"]
# after_request = ["next_ai.utils.after_request"]

# Job Events
# ----------
# before_job = ["next_ai.utils.before_job"]
# after_job = ["next_ai.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"next_ai.auth.validate"
# ]
