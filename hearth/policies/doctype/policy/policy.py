# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from hearth.services.reminder_service import sync_policy_renewal_reminder
from hearth.utils.premium_frequency import validate_premium_frequency_fields


class Policy(Document):
	def validate(self):
		if not self.holder:
			self.holder = frappe.session.user
		validate_premium_frequency_fields(self)

	def on_update(self):
		sync_policy_renewal_reminder(self)


@frappe.whitelist()
def transfer_now(name: str) -> None:
	"""Make a private (no-circle) record visible to the selected holder."""
	doc = frappe.get_doc("Policy", name)

	if doc.get("circle"):
		frappe.throw(frappe._("Transfer is only available when no Circle is selected."))
	if doc.owner != frappe.session.user:
		frappe.throw(frappe._("Only the creator can transfer this record."))
	if not doc.get("holder") or doc.holder == doc.owner:
		frappe.throw(frappe._("Select a different Holder to transfer this record."))

	if not frappe.db.table_exists("Policy") or not frappe.db.has_column("Policy", "ownership_transferred"):
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
