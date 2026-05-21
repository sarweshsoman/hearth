# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

from frappe.utils import add_days, add_months, add_to_date, add_years, getdate


def reminder_window_start(days_before: int = 30):
	return add_days(getdate(), days_before)


def advance_reminder_date(current, recurrence: str):
	current = getdate(current)
	if recurrence == "Daily":
		return add_days(current, 1)
	if recurrence == "Weekly":
		return add_days(current, 7)
	if recurrence == "Monthly":
		return add_months(current, 1)
	if recurrence == "Yearly":
		return add_years(current, 1)
	return current
