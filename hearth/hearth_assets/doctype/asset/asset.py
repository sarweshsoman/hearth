# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document


class Asset(Document):
	def before_insert(self):
		if not self.owner_user:
			self.owner_user = frappe.session.user
