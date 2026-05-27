# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from hearth.services.notification_service import resolve_reminder_recipients
from hearth.services.reminder_service import cancel_active_reminders, sync_policy_renewal_reminder


class TestReminderService(FrappeTestCase):
	def test_cancel_active_reminders(self):
		if not frappe.db.table_exists("Policy"):
			self.skipTest("Policy table missing")

		policy = frappe.get_doc(
			{
				"doctype": "Policy",
				"naming_series": "HEAR-POL-.#####",
				"policy_name": "Reminder Cancel Test",
				"provider": "Test Provider",
				"policy_type": "Insurance",
				"holder": frappe.session.user,
				"status": "Active",
				"renewal_date": "2026-12-01",
				"premium_frequency": "Yearly",
			}
		)
		policy.insert(ignore_permissions=True)

		sync_policy_renewal_reminder(policy)
		rule_name = frappe.db.get_value(
			"Reminder Rule",
			{
				"reference_doctype": "Policy",
				"reference_name": policy.name,
				"reminder_type": "Renewal",
				"status": "Active",
			},
		)
		self.assertTrue(rule_name)

		policy.status = "Cancelled"
		sync_policy_renewal_reminder(policy)
		self.assertEqual(frappe.db.get_value("Reminder Rule", rule_name, "status"), "Cancelled")

		frappe.delete_doc("Reminder Rule", rule_name, ignore_permissions=True, force=True)
		frappe.delete_doc("Policy", policy.name, ignore_permissions=True, force=True)

	def test_private_transferred_recipients_exclude_creator(self):
		doc = frappe._dict(
			doctype="Hearth Asset",
			owner="creator@example.com",
			owner_user="holder@example.com",
			ownership_transferred=1,
			circle=None,
		)
		with patch("hearth.services.notification_service.frappe.get_doc", return_value=doc):
			with patch("hearth.services.notification_service.frappe.db.exists", return_value=True):
				recipients = resolve_reminder_recipients("Hearth Asset", "TEST-ASSET")
		self.assertEqual(recipients, ["holder@example.com"])

	def test_cancel_without_matching_rules_is_safe(self):
		cancel_active_reminders("Policy", "non-existent-policy", "Renewal")
