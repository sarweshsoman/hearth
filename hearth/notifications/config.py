# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt


def get_notification_config():
	return {
		"for_doctype": {
			"Reminder Rule": {"status": "Active"},
			"Policy": {"status": "Pending Renewal"},
		}
	}
