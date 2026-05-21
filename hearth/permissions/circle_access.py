# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Circle-based visibility for Hearth records.

Uses composition over ERPNext internals: only standard Frappe RBAC hooks.
"""

import frappe

HEARTH_CIRCLE_DOCTYPES = ("Circle", "Policy", "Asset", "Liability", "Reminder Rule")
HEARTH_LINKED_DOCTYPES = ("Policy", "Asset", "Liability", "Reminder Rule")


def _escape(value: str) -> str:
	return frappe.db.escape(value)


def get_accessible_circles(user: str | None = None) -> list[str]:
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return frappe.get_all("Circle", pluck="name")

	owned = frappe.get_all("Circle", filters={"owner_user": user}, pluck="name")
	member_circles = frappe.db.sql(
		"""
		select distinct parent
		from `tabCircle Member`
		where member_user = %s
		""",
		user,
		pluck=True,
	)
	return list(set(owned + member_circles))


def get_permission_query_conditions(doctype: str, user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return None

	if doctype == "Circle":
		circles = get_accessible_circles(user)
		if not circles:
			return "1=0"
		return f"`tabCircle`.name in ({', '.join(_escape(c) for c in circles)})"

	if doctype == "Reminder Rule":
		return f"(`tabReminder Rule`.owner = {_escape(user)})"

	if doctype in HEARTH_LINKED_DOCTYPES:
		circles = get_accessible_circles(user)
		circle_list = ", ".join(_escape(c) for c in circles) if circles else "''"
		return (
			f"(`tab{doctype}`.owner = {_escape(user)} "
			f"or (`tab{doctype}`.circle in ({circle_list})) "
			f"or (`tab{doctype}`.circle is null and `tab{doctype}`.owner = {_escape(user)}))"
		)

	return None


def _record_owner(doc) -> str:
	if doc.doctype == "Policy":
		return doc.get("holder") or doc.owner
	if doc.doctype == "Asset":
		return doc.get("owner_user") or doc.owner
	return doc.owner


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	if doc.doctype == "Circle":
		if doc.owner_user == user:
			return True
		return any(m.member_user == user for m in doc.members)

	if doc.doctype in HEARTH_LINKED_DOCTYPES:
		owner = _record_owner(doc)
		if owner == user:
			return True
		if not doc.get("circle"):
			return owner == user
		if doc.circle not in get_accessible_circles(user):
			return False
		if ptype in ("write", "create", "delete") and owner != user:
			circle_owner = frappe.db.get_value("Circle", doc.circle, "owner_user")
			return user == circle_owner
		return True

	return False


def get_circle_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Circle", user)


def get_policy_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Policy", user)


def get_asset_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Asset", user)


def get_liability_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Liability", user)


def get_reminder_rule_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Reminder Rule", user)


def circle_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def policy_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def asset_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def liability_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def reminder_rule_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)
