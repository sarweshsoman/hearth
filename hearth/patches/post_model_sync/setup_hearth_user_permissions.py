# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe

from hearth.utils.user_setup import sync_all_hearth_users, verify_hearth_doctype_permissions


def execute():
	verify_hearth_doctype_permissions()
	sync_all_hearth_users()
