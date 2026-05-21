# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document

from hearth.services.reminder_service import sync_policy_renewal_reminder


class Policy(Document):
	def validate(self):
		if not self.holder:
			self.holder = frappe.session.user

	def on_update(self):
		sync_policy_renewal_reminder(self)
