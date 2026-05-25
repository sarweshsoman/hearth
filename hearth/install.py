# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe

from hearth.utils.modules import sync_hearth_module_profile
from hearth.utils.user_setup import (
	setup_hearth_user,
	should_apply_hearth_user_setup,
	sync_all_hearth_users,
	sync_hearth_role_profile,
	sync_hearth_workspace,
	verify_hearth_doctype_permissions,
)


def after_install():
	_ensure_hearth_role()
	_ensure_desk_user_role_exists()
	sync_hearth_module_profile()
	sync_hearth_role_profile()
	verify_hearth_doctype_permissions()
	sync_hearth_workspace()
	sync_all_hearth_users()


def after_migrate():
	sync_hearth_module_profile()
	sync_hearth_role_profile()
	verify_hearth_doctype_permissions()
	sync_hearth_workspace()
	sync_all_hearth_users()


def _ensure_hearth_role():
	if frappe.db.exists("Role", "Hearth User"):
		return

	role = frappe.get_doc({"doctype": "Role", "role_name": "Hearth User", "desk_access": 1})
	role.insert(ignore_permissions=True)


def _ensure_desk_user_role_exists():
	"""Desk User is required for desk access alongside Hearth User."""
	if not frappe.db.exists("Role", "Desk User"):
		frappe.get_doc({"doctype": "Role", "role_name": "Desk User", "desk_access": 1}).insert(
			ignore_permissions=True
		)


def validate_hearth_user_setup(doc, method=None):
	"""When Hearth User is assigned, apply role profile, Desk User, and module access."""
	if not should_apply_hearth_user_setup(doc):
		return

	setup_hearth_user(doc)


def on_update_hearth_user_setup(doc, method=None):
	"""Re-apply module blocks after save when roles/module profile change."""
	if not should_apply_hearth_user_setup(doc):
		return

	from hearth.utils.user_setup import apply_hearth_user_block_modules

	if doc.module_profile:
		apply_hearth_user_block_modules(doc.name)
