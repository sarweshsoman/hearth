# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def send_reminder_notification(rule_name: str, subject: str, message: str) -> None:
	rule = frappe.get_doc("Reminder Rule", rule_name)
	recipients = _resolve_recipients(rule)

	if rule.delivery_channel in ("Email", "Both") and recipients:
		frappe.sendmail(recipients=recipients, subject=subject, message=message)

	if rule.delivery_channel in ("In-App", "Both"):
		for user in recipients:
			_create_in_app_notification(user, subject, message, rule)


def _resolve_recipients(rule) -> list[str]:
	ref = frappe.get_doc(rule.reference_doctype, rule.reference_name)
	owner = ref.owner
	if rule.reference_doctype == "Policy" and ref.get("holder"):
		return list({owner, ref.holder})
	if rule.reference_doctype == "Asset" and ref.get("owner_user"):
		return list({owner, ref.owner_user})
	return [owner]


def _create_in_app_notification(user: str, subject: str, message: str, rule) -> None:
	notification = frappe.new_doc("Notification Log")
	notification.for_user = user
	notification.type = "Alert"
	notification.subject = subject
	notification.email_content = message
	notification.document_type = rule.reference_doctype
	notification.document_name = rule.reference_name
	notification.insert(ignore_permissions=True)
