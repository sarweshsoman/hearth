# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe

from hearth.install import apply_module_profile_to_hearth_users, sync_hearth_module_profile


def execute():
	frappe.flags.in_install = True
	sync_hearth_module_profile()
	apply_module_profile_to_hearth_users()
	frappe.flags.in_install = False
