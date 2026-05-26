# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Structured attachment helpers using native Frappe File records."""

import frappe


def get_recent_linked_documents(limit: int = 10) -> list[dict]:
	"""Return recent document links across Hearth records visible to the user.

	We intentionally avoid raw SQL here because it bypasses Frappe permission
	query conditions (circle/owner visibility). We fetch a small candidate set
	and then filter by `frappe.has_permission` on the linked parent record.
	"""

	# Oversample a bit so we can filter down while keeping ordering.
	candidate_limit = max(int(limit) * 5, 25)
	rows = frappe.get_all(
		"Hearth Document Link",
		filters={"attachment": ["!=", ""]},
		fields=["title", "attachment", "notes", "parenttype", "parent", "modified"],
		order_by="modified desc",
		limit=candidate_limit,
	)

	visible: list[dict] = []
	for row in rows:
		parenttype = row.get("parenttype")
		parent = row.get("parent")
		if not parenttype or not parent:
			continue
		if not frappe.db.exists(parenttype, parent):
			continue
		if frappe.has_permission(parenttype, "read", doc=parent):
			visible.append(row)
			if len(visible) >= limit:
				break

	return visible
