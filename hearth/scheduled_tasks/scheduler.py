# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

from hearth.services.reminder_service import process_due_reminders, scan_expiring_policies


def daily():
	process_due_reminders()
	scan_expiring_policies()
