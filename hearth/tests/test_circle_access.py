# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from hearth.permissions.circle_access import (
	get_circle_recipients,
	has_permission,
	resolve_user_link,
)


class TestCircleAccess(FrappeTestCase):
	def test_resolve_user_link_placeholder(self):
		self.assertEqual(resolve_user_link("__user__", "alice@example.com"), "alice@example.com")
		self.assertEqual(resolve_user_link("bob@example.com"), "bob@example.com")
		self.assertIsNone(resolve_user_link(None))

	def test_private_record_visible_to_creator(self):
		doc = frappe._dict(
			doctype="Hearth Asset",
			owner="creator@example.com",
			owner_user="other@example.com",
			ownership_transferred=0,
			circle=None,
		)
		self.assertTrue(has_permission(doc, "read", "creator@example.com"))
		self.assertFalse(has_permission(doc, "read", "other@example.com"))

	def test_transferred_record_visible_to_holder(self):
		doc = frappe._dict(
			doctype="Hearth Asset",
			owner="creator@example.com",
			owner_user="holder@example.com",
			ownership_transferred=1,
			circle=None,
		)
		self.assertTrue(has_permission(doc, "read", "holder@example.com"))
		self.assertTrue(has_permission(doc, "write", "holder@example.com"))

	def test_circle_member_read_only(self):
		doc = frappe._dict(
			doctype="Policy",
			owner="creator@example.com",
			holder="creator@example.com",
			circle="Family Circle",
		)
		with patch("hearth.permissions.circle_access.get_accessible_circles", return_value=["Family Circle"]):
			self.assertTrue(has_permission(doc, "read", "member@example.com"))
			self.assertFalse(has_permission(doc, "write", "member@example.com"))
			self.assertTrue(has_permission(doc, "write", "creator@example.com"))

	def test_circle_owner_can_write_shared_record(self):
		doc = frappe._dict(
			doctype="Liability",
			owner="creator@example.com",
			owner_user="creator@example.com",
			circle="Family Circle",
		)
		with patch("hearth.permissions.circle_access.get_accessible_circles", return_value=["Family Circle"]):
			with patch(
				"hearth.permissions.circle_access.get_circle_owner",
				return_value="circle_owner@example.com",
			):
				self.assertTrue(has_permission(doc, "write", "circle_owner@example.com"))
				self.assertFalse(has_permission(doc, "write", "member@example.com"))

	def test_get_circle_recipients(self):
		if not frappe.db.table_exists("Circle"):
			self.skipTest("Circle table missing")

		circle_name = frappe.db.get_value("Circle", {"circle_name": "Hearth Test Circle"}, "name")
		if not circle_name:
			doc = frappe.get_doc(
				{
					"doctype": "Circle",
					"circle_name": "Hearth Test Circle",
					"owner_user": frappe.session.user,
					"visibility_level": "Shared",
				}
			)
			doc.insert(ignore_permissions=True)
			circle_name = doc.name

		recipients = get_circle_recipients(circle_name)
		self.assertIn(frappe.session.user, recipients)
