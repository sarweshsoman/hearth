# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from hearth.services.reminder_service import sync_liability_emi_reminder


class Liability(Document):
	def on_update(self):
		sync_liability_emi_reminder(self)
