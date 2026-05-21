# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Structured attachment helpers using native Frappe File records."""

import frappe


def get_recent_linked_documents(limit: int = 10) -> list[dict]:
	"""Return recent document links across Hearth records visible to the user."""
	rows = frappe.db.sql(
		"""
		select
			hdl.title,
			hdl.attachment,
			hdl.category,
			hdl.parenttype,
			hdl.parent,
			hdl.modified
		from `tabHearth Document Link` hdl
		where hdl.attachment is not null and hdl.attachment != ''
		order by hdl.modified desc
		limit %s
		""",
		limit,
		as_dict=True,
	)
	return rows
