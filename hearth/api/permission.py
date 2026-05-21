# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe


@frappe.whitelist()
def has_app_permission() -> bool:
	if frappe.session.user == "Guest":
		return False
	return frappe.has_permission("Policy", "read") or "Hearth User" in frappe.get_roles()
