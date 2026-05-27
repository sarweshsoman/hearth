# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Private (no-circle) ownership handoff between users."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

OWNER_FIELD_BY_DOCTYPE = {
	"Hearth Asset": "owner_user",
	"Liability": "owner_user",
	"Policy": "holder",
}


def owner_field_for(doctype: str) -> str:
	field = OWNER_FIELD_BY_DOCTYPE.get(doctype)
	if not field:
		frappe.throw(frappe._("Ownership transfer is not supported for {0}.").format(doctype))
	return field


def resolve_user(value: str | None, user: str | None = None) -> str | None:
	if not value:
		return None
	if value == "__user__":
		return user or frappe.session.user
	return value


def get_current_holder(doc) -> str:
	"""User who currently holds the private record for transfer purposes."""
	owner_field = owner_field_for(doc.doctype)
	designated = resolve_user(doc.get(owner_field))
	if doc.get("circle"):
		return designated or doc.owner
	if doc.get("ownership_transferred") and designated:
		return designated
	return doc.owner


def can_initiate_transfer(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if doc.owner == user:
		return True
	if doc.get("ownership_transferred"):
		owner_field = owner_field_for(doc.doctype)
		return resolve_user(doc.get(owner_field), user) == user
	return False


def _ensure_transfer_fields(doctype: str) -> None:
	if not frappe.db.table_exists(doctype) or not frappe.db.has_column(doctype, "ownership_transferred"):
		frappe.throw(
			frappe._("Run bench migrate to enable ownership transfer."),
			title=frappe._("Migration Required"),
		)


def execute_transfer(doctype: str, name: str, **kwargs) -> dict:
	"""Transfer a private record to the user in the owner/holder field (or kwargs)."""
	doc = frappe.get_doc(doctype, name)
	owner_field = owner_field_for(doctype)

	if doc.get("circle"):
		frappe.throw(frappe._("Transfer is only available when no Circle is selected."))

	_ensure_transfer_fields(doctype)

	user = frappe.session.user
	if not can_initiate_transfer(doc, user):
		frappe.throw(frappe._("Only the creator or current owner can transfer this record."))

	target_user = resolve_user(kwargs.get(owner_field) or doc.get(owner_field))
	current_holder = get_current_holder(doc)

	if not target_user or target_user == current_holder:
		label = "Holder" if doctype == "Policy" else "Owner"
		frappe.throw(frappe._("Select a different {0} to transfer this record.").format(label))

	updates: dict = {
		owner_field: target_user,
		"transferred_on": now_datetime(),
	}
	if target_user == doc.owner:
		updates["ownership_transferred"] = 0
	else:
		updates["ownership_transferred"] = 1

	doc.db_set(updates, update_modified=True)
	return {"owner": target_user}
