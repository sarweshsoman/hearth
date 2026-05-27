# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime, today

from hearth.services.notification_service import send_reminder_notification
from hearth.utils.dates import advance_reminder_date

DEFAULT_REMINDER_DAYS_BEFORE = 30


def get_reminder_lead_days() -> int:
	return int(frappe.conf.get("hearth_reminder_days_before") or DEFAULT_REMINDER_DAYS_BEFORE)


def cancel_active_reminders(
	reference_doctype: str,
	reference_name: str,
	reminder_type: str | None = None,
) -> None:
	"""Cancel active reminder rules for a reference record."""
	filters = {
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"status": "Active",
	}
	if reminder_type:
		filters["reminder_type"] = reminder_type

	for name in frappe.get_all("Reminder Rule", filters=filters, pluck="name"):
		frappe.db.set_value("Reminder Rule", name, "status", "Cancelled", update_modified=True)


def _upsert_reminder_rule(
	reference_doctype: str,
	reference_name: str,
	reminder_type: str,
	reminder_date,
	recurrence: str = "Yearly",
) -> None:
	if not reminder_date:
		return

	reminder_date = add_days(getdate(reminder_date), -get_reminder_lead_days())
	existing = frappe.db.exists(
		"Reminder Rule",
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"reminder_type": reminder_type,
			"status": "Active",
		},
	)

	if existing:
		doc = frappe.get_doc("Reminder Rule", existing)
		doc.reminder_date = reminder_date
		doc.recurrence = recurrence
		doc.save(ignore_permissions=True)
		return

	doc = frappe.get_doc(
		{
			"doctype": "Reminder Rule",
			"naming_series": "HEAR-REM-.#####",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"reminder_type": reminder_type,
			"reminder_date": reminder_date,
			"recurrence": recurrence,
			"delivery_channel": "Both",
			"status": "Active",
		}
	)
	doc.insert(ignore_permissions=True)


def sync_policy_renewal_reminder(policy) -> None:
	if not policy.renewal_date or policy.status in ("Expired", "Cancelled"):
		cancel_active_reminders("Policy", policy.name, "Renewal")
		return
	_upsert_reminder_rule("Policy", policy.name, "Renewal", policy.renewal_date)


def sync_liability_emi_reminder(liability) -> None:
	if not liability.due_date or liability.status == "Closed":
		cancel_active_reminders("Liability", liability.name, "EMI Due")
		return
	_upsert_reminder_rule("Liability", liability.name, "EMI Due", liability.due_date, recurrence="Monthly")


def process_due_reminders() -> None:
	"""Daily scheduler entry: dispatch active reminders due today or earlier."""
	rules = frappe.get_all(
		"Reminder Rule",
		filters={"status": "Active", "reminder_date": ["<=", today()]},
		fields=["name", "reference_doctype", "reference_name", "reminder_type", "recurrence", "reminder_date"],
	)

	for rule in rules:
		if not frappe.db.exists(rule.reference_doctype, rule.reference_name):
			frappe.db.set_value("Reminder Rule", rule.name, "status", "Cancelled")
			continue

		subject = _("Hearth Reminder: {0}").format(rule.reminder_type)
		message = _("Reminder for {0} {1}").format(rule.reference_doctype, rule.reference_name)
		send_reminder_notification(rule.name, subject, message)

		doc = frappe.get_doc("Reminder Rule", rule.name)
		doc.last_sent_on = now_datetime()

		if doc.recurrence and doc.recurrence != "None":
			doc.reminder_date = advance_reminder_date(doc.reminder_date, doc.recurrence)
		else:
			doc.status = "Completed"

		doc.save(ignore_permissions=True)


def scan_expiring_policies() -> None:
	"""Mark policies past maturity as expired and create expiry reminders."""
	for policy in frappe.get_all(
		"Policy",
		filters={"status": "Active", "maturity_date": ["<=", today()]},
		pluck="name",
	):
		doc = frappe.get_doc("Policy", policy)
		cancel_active_reminders("Policy", doc.name, "Renewal")
		doc.status = "Expired"
		doc.save(ignore_permissions=True)
		if doc.maturity_date:
			_upsert_reminder_rule("Policy", doc.name, "Expiry", doc.maturity_date, recurrence="None")
