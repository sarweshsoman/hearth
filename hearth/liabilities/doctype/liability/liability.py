# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document

from hearth.services.ownership_transfer import execute_transfer

from hearth.services.reminder_service import sync_liability_emi_reminder


class Liability(Document):
	def validate(self):
		if not self.owner_user or self.owner_user == "__user__":
			self.owner_user = frappe.session.user

	def on_update(self):
		sync_liability_emi_reminder(self)


@frappe.whitelist()
def transfer_now(name: str, owner_user: str | None = None) -> dict:
	"""Make a private (no-circle) record visible to the selected owner_user."""
	return execute_transfer("Liability", name, owner_user=owner_user)
