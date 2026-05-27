# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from hearth.services.ownership_transfer import (
	can_initiate_transfer,
	execute_transfer,
	get_current_holder,
	resolve_user,
)


class TestOwnershipTransfer(FrappeTestCase):
	def test_get_current_holder_before_transfer(self):
		doc = frappe._dict(
			doctype="Hearth Asset",
			owner="creator@example.com",
			owner_user="beneficiary@example.com",
			ownership_transferred=0,
			circle=None,
		)
		self.assertEqual(get_current_holder(doc), "creator@example.com")

	def test_get_current_holder_after_transfer(self):
		doc = frappe._dict(
			doctype="Hearth Asset",
			owner="creator@example.com",
			owner_user="beneficiary@example.com",
			ownership_transferred=1,
			circle=None,
		)
		self.assertEqual(get_current_holder(doc), "beneficiary@example.com")

	def test_can_initiate_transfer_creator_and_holder(self):
		pending = frappe._dict(
			doctype="Policy",
			owner="creator@example.com",
			holder="beneficiary@example.com",
			ownership_transferred=0,
			circle=None,
		)
		transferred = frappe._dict(
			doctype="Policy",
			owner="creator@example.com",
			holder="beneficiary@example.com",
			ownership_transferred=1,
			circle=None,
		)
		self.assertTrue(can_initiate_transfer(pending, "creator@example.com"))
		self.assertFalse(can_initiate_transfer(pending, "beneficiary@example.com"))
		self.assertTrue(can_initiate_transfer(transferred, "creator@example.com"))
		self.assertTrue(can_initiate_transfer(transferred, "beneficiary@example.com"))

	def test_resolve_user_placeholder(self):
		self.assertEqual(resolve_user("__user__", "alice@example.com"), "alice@example.com")

	def test_transfer_back_to_creator_resets_flag(self):
		if not frappe.db.table_exists("Hearth Asset"):
			self.skipTest("Hearth Asset table missing")

		asset = frappe.get_doc(
			{
				"doctype": "Hearth Asset",
				"naming_series": "HEAR-AST-.#####",
				"asset_name": "Transfer Test Asset",
				"asset_type": "Miscellaneous",
				"owner_user": "Guest",
			}
		)
		asset.insert(ignore_permissions=True)
		asset.db_set({"ownership_transferred": 1, "owner_user": "Guest"})

		frappe.set_user(asset.owner)
		result = execute_transfer("Hearth Asset", asset.name, owner_user=asset.owner)
		self.assertEqual(result["owner"], asset.owner)

		asset.reload()
		self.assertEqual(asset.owner_user, asset.owner)
		self.assertEqual(asset.ownership_transferred, 0)

		asset.delete(ignore_permissions=True)
		frappe.set_user("Administrator")
