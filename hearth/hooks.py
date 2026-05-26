app_name = "hearth"
app_title = "Hearth"
app_publisher = "Hearth"
app_description = "Personal finance organization, policy management, and asset tracking"
app_email = "dev@hearth.local"
app_license = "mit"

add_to_apps_screen = [
	{
		"name": "hearth",
		"logo": "/assets/hearth/images/hearth.svg",
		"title": "Hearth",
		"route": "/app/hearth",
		"has_permission": "hearth.api.permission.has_app_permission",
	}
]

app_include_css = ["/assets/hearth/css/hearth.css", "/assets/hearth/css/hearth_dashboard.css"]
app_include_js = "/assets/hearth/js/hearth.js"

after_install = "hearth.install.after_install"
after_migrate = "hearth.install.after_migrate"

doc_events = {
	"User": {
		"validate": "hearth.install.validate_hearth_user_setup",
		"on_update": "hearth.install.on_update_hearth_user_setup",
	},
}

notification_config = "hearth.notifications.config.get_notification_config"

permission_query_conditions = {
	"Circle": "hearth.permissions.circle_access.get_circle_query_conditions",
	"Policy": "hearth.permissions.circle_access.get_policy_query_conditions",
	"Hearth Asset": "hearth.permissions.circle_access.get_hearth_asset_query_conditions",
	"Liability": "hearth.permissions.circle_access.get_liability_query_conditions",
	"Reminder Rule": "hearth.permissions.circle_access.get_reminder_rule_query_conditions",
}

has_permission = {
	"Circle": "hearth.permissions.circle_access.circle_has_permission",
	"Policy": "hearth.permissions.circle_access.policy_has_permission",
	"Hearth Asset": "hearth.permissions.circle_access.hearth_asset_has_permission",
	"Liability": "hearth.permissions.circle_access.liability_has_permission",
	"Reminder Rule": "hearth.permissions.circle_access.reminder_rule_has_permission",
}

scheduler_events = {
	"daily": ["hearth.scheduled_tasks.scheduler.daily"],
}

# override_doctype_class = {}
# override_whitelisted_methods = {}
# doc_events = {}
