# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

from hearth.utils.user_setup import sync_hearth_workspace, verify_hearth_doctype_permissions


def execute():
	verify_hearth_doctype_permissions()
	sync_hearth_workspace()
