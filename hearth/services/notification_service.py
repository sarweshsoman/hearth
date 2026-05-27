# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from hearth.permissions.circle_access import get_circle_recipients
from hearth.services.ownership_transfer import OWNER_FIELD_BY_DOCTYPE, get_current_holder, resolve_user


def send_reminder_notification(rule_name: str, subject: str, message: str) -> None:
	rule = frappe.get_doc("Reminder Rule", rule_name)
	recipients = resolve_reminder_recipients(rule.reference_doctype, rule.reference_name)

	if rule.delivery_channel in ("Email", "Both") and recipients:
		frappe.sendmail(recipients=recipients, subject=subject, message=message)

	if rule.delivery_channel in ("In-App", "Both"):
		for user in recipients:
			_create_in_app_notification(user, subject, message, rule)


def resolve_reminder_recipients(reference_doctype: str, reference_name: str) -> list[str]:
	"""Resolve users who should receive reminders for a Hearth record."""
	if not frappe.db.exists(reference_doctype, reference_name):
		return []

	ref = frappe.get_doc(reference_doctype, reference_name)
	recipients: set[str] = set()

	if ref.get("circle"):
		recipients.update(get_circle_recipients(ref.circle))
		recipients.add(ref.owner)
		owner_field = OWNER_FIELD_BY_DOCTYPE.get(reference_doctype)
		if owner_field:
			designated = resolve_user(ref.get(owner_field))
			if designated:
				recipients.add(designated)
		return _clean_recipients(recipients)

	holder = get_current_holder(ref)
	if holder:
		recipients.add(holder)

	if not ref.get("ownership_transferred"):
		recipients.add(ref.owner)

	return _clean_recipients(recipients)


def _clean_recipients(recipients: set[str]) -> list[str]:
	return sorted(user for user in recipients if user and user != "Guest")


def _resolve_recipients(rule) -> list[str]:
	return resolve_reminder_recipients(rule.reference_doctype, rule.reference_name)


def _create_in_app_notification(user: str, subject: str, message: str, rule) -> None:
	notification = frappe.new_doc("Notification Log")
	notification.for_user = user
	notification.type = "Alert"
	notification.subject = subject
	notification.email_content = message
	notification.document_type = rule.reference_doctype
	notification.document_name = rule.reference_name
	notification.insert(ignore_permissions=True)
