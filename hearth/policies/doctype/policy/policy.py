# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document

from hearth.services.ownership_transfer import execute_transfer
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
def transfer_now(name: str, holder: str | None = None) -> dict:
	"""Make a private (no-circle) record visible to the selected holder."""
	return execute_transfer("Policy", name, holder=holder)
