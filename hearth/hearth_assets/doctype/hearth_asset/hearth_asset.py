# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document


class HearthAsset(Document):
	def before_insert(self):
		if not self.owner_user or self.owner_user == "__user__":
			self.owner_user = frappe.session.user
