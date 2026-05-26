# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class HearthAsset(Document):
	def validate(self):
		# Normalize legacy default values and keep a real user in the field.
		if not self.owner_user or self.owner_user == "__user__":
			self.owner_user = frappe.session.user

	def before_insert(self):
		if not self.owner_user or self.owner_user == "__user__":
			self.owner_user = frappe.session.user


@frappe.whitelist()
def transfer_now(name: str) -> None:
	"""Make a private (no-circle) record visible to the selected owner_user."""
	doc = frappe.get_doc("Hearth Asset", name)

	if doc.get("circle"):
		frappe.throw(frappe._("Transfer is only available when no Circle is selected."))
	if doc.owner != frappe.session.user:
		frappe.throw(frappe._("Only the creator can transfer this record."))
	if not doc.get("owner_user") or doc.owner_user == doc.owner:
		frappe.throw(frappe._("Select a different Owner to transfer this record."))

	if not frappe.db.table_exists("Hearth Asset") or not frappe.db.has_column(
		"Hearth Asset", "ownership_transferred"
	):
		frappe.throw(
			frappe._("Run bench migrate to enable ownership transfer."),
			title=frappe._("Migration Required"),
		)

	doc.db_set(
		{
			"ownership_transferred": 1,
			"transferred_on": now_datetime(),
		},
		update_modified=True,
	)
