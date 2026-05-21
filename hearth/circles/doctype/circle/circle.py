# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Circle(Document):
	def validate(self):
		if self.owner_user == frappe.session.user:
			return
		if not self.is_new() and frappe.db.get_value("Circle", self.name, "owner_user") != frappe.session.user:
			if frappe.session.user not in {m.member_user for m in self.members}:
				frappe.throw(_("Only the circle owner can modify circle membership."))

	def before_insert(self):
		if not self.owner_user:
			self.owner_user = frappe.session.user
