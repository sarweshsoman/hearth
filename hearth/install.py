# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe

from hearth.utils.modules import (
	HEARTH_MODULE_PROFILE,
	apply_module_profile_to_hearth_users,
	should_use_hearth_module_profile,
	sync_hearth_module_profile,
)


def after_install():
	_ensure_hearth_role()
	sync_hearth_module_profile()
	apply_module_profile_to_hearth_users()


def after_migrate():
	sync_hearth_module_profile()
	apply_module_profile_to_hearth_users()


def _ensure_hearth_role():
	if frappe.db.exists("Role", "Hearth User"):
		return

	role = frappe.get_doc({"doctype": "Role", "role_name": "Hearth User", "desk_access": 1})
	role.insert(ignore_permissions=True)


def validate_hearth_user_modules(doc, method=None):
	"""Ensure Hearth User accounts can see Hearth workspaces (module profile)."""
	if not should_use_hearth_module_profile(doc):
		return

	if doc.module_profile != HEARTH_MODULE_PROFILE:
		doc.module_profile = HEARTH_MODULE_PROFILE
