app_name = "nra_integration"
app_title = "NRA Integration"
app_publisher = "Outpost Work LLP"
app_description = "NRA Integration"
app_email = "anas.outpost@gmail.com"
app_license = "mit"
required_apps = ["frappe/erpnext"]

# Apps
# ------------------
fixtures = [
    {
        "doctype": "HSN Code"
    },
    {
        "doctype": "State"
    },
    {
        "doctype": "Local Government List"
    }
]


after_install = [
    "nra_integration.customizations.item_custom.create_custom_fields",
    "nra_integration.customizations.company_custom.create_custom_fields",
    "nra_integration.customizations.address_custom.create_custom_fields",
    "nra_integration.customizations.customer_custom.create_custom_fields",
    "nra_integration.customizations.sales_invoice_custom.create_custom_fields"
]
after_uninstall = [
    "nra_integration.customizations.item_custom.delete_custom_fields",
    "nra_integration.customizations.company_custom.delete_custom_fields",
    "nra_integration.customizations.address_custom.delete_custom_fields",
    "nra_integration.customizations.customer_custom.delete_custom_fields",
    "nra_integration.customizations.sales_invoice_custom.delete_custom_fields"
]
after_migrate = [
    "nra_integration.customizations.item_custom.create_custom_fields",
    "nra_integration.customizations.company_custom.create_custom_fields",
    "nra_integration.customizations.address_custom.create_custom_fields",
    "nra_integration.customizations.customer_custom.create_custom_fields",
    "nra_integration.customizations.sales_invoice_custom.create_custom_fields"
]

doctype_js = {
    "Item": "public/js/item_custom.js",
    "Company": "public/js/company_custom.js",
    "Customer": "public/js/customer_custom.js",
    "Sales Invoice": "public/js/sales_invoice_custom.js"
}

doctype_list_js = {
    "Sales Invoice": "public/js/sales_invoice_list.js"
}

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "nra_integration",
# 		"logo": "/assets/nra_integration/logo.png",
# 		"title": "NRA Integration",
# 		"route": "/nra_integration",
# 		"has_permission": "nra_integration.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/nra_integration/css/nra_integration.css"
# app_include_js = "/assets/nra_integration/js/nra_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/nra_integration/css/nra_integration.css"
# web_include_js = "/assets/nra_integration/js/nra_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nra_integration/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "nra_integration/public/icons.svg"

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
# 	"methods": "nra_integration.utils.jinja_methods",
# 	"filters": "nra_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "nra_integration.install.before_install"
# after_install = "nra_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "nra_integration.uninstall.before_uninstall"
# after_uninstall = "nra_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "nra_integration.utils.before_app_install"
# after_app_install = "nra_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "nra_integration.utils.before_app_uninstall"
# after_app_uninstall = "nra_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nra_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
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

doc_events = {
    "Item": {
        "on_update": "nra_integration.integration.item_integration.sync_item_to_digitax"
    },
    "Company": {
        "on_update": "nra_integration.integration.company_integration.sync_company_to_digitax"
    },
    "Sales Invoice": {
        "on_submit": "nra_integration.integration.sales_invoice_integration.sync_sales_invoice_to_digitax"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"nra_integration.tasks.all"
# 	],
# 	"daily": [
# 		"nra_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"nra_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"nra_integration.tasks.weekly"
# 	],
# 	"monthly": [
# 		"nra_integration.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "nra_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "nra_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "nra_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["nra_integration.utils.before_request"]
# after_request = ["nra_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["nra_integration.utils.before_job"]
# after_job = ["nra_integration.utils.after_job"]

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
# 	"nra_integration.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

