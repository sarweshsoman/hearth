# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document

from hearth.services.ownership_transfer import execute_transfer


class HearthAsset(Document):
	def validate(self):
		# Normalize legacy default values and keep a real user in the field.
		if not self.owner_user or self.owner_user == "__user__":
			self.owner_user = frappe.session.user

	def before_insert(self):
		if not self.owner_user or self.owner_user == "__user__":
			self.owner_user = frappe.session.user


@frappe.whitelist()
def transfer_now(name: str, owner_user: str | None = None) -> dict:
	"""Make a private (no-circle) record visible to the selected owner_user."""
	return execute_transfer("Hearth Asset", name, owner_user=owner_user)
