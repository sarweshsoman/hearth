# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Backfill transfer metadata for records already marked as transferred."""

import frappe


def execute():
	if not frappe.db.table_exists("Hearth Asset"):
		return

	for doctype, owner_field in (
		("Hearth Asset", "owner_user"),
		("Liability", "owner_user"),
		("Policy", "holder"),
	):
		if not frappe.db.table_exists(doctype):
			continue
		if not frappe.db.has_column(doctype, "ownership_transferred"):
			continue

		frappe.db.sql(
			f"""
			update `tab{doctype}`
			set transferred_on = modified
			where coalesce(ownership_transferred, 0) = 1
				and transferred_on is null
			"""
		)
