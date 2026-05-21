# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe


def after_install():
	_ensure_hearth_role()


def _ensure_hearth_role():
	if frappe.db.exists("Role", "Hearth User"):
		return

	role = frappe.get_doc({"doctype": "Role", "role_name": "Hearth User", "desk_access": 1})
	role.insert(ignore_permissions=True)
