# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Circle-based visibility for Hearth records.

Uses composition over ERPNext internals: only standard Frappe RBAC hooks.
"""

import frappe

HEARTH_CIRCLE_DOCTYPES = ("Circle", "Policy", "Hearth Asset", "Liability", "Reminder Rule")
HEARTH_LINKED_DOCTYPES = ("Policy", "Hearth Asset", "Liability", "Reminder Rule")


def _escape(value: str) -> str:
	return frappe.db.escape(value)


def _has_field(doctype: str, fieldname: str) -> bool:
	if not frappe.db.table_exists(doctype):
		return False
	try:
		return bool(frappe.db.has_column(doctype, fieldname))
	except Exception:
		return False


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
		base = (
			f"(`tab{doctype}`.owner = {_escape(user)} "
			f"or (`tab{doctype}`.circle in ({circle_list}))"
		)

		# Private records (circle is NULL) remain visible only to creator (doc.owner),
		# unless explicitly transferred to the target user.
		if doctype == "Policy" and _has_field("Policy", "ownership_transferred"):
			transferred_clause = (
				f"or (`tabPolicy`.circle is null and coalesce(`tabPolicy`.ownership_transferred, 0) = 1 "
				f"and `tabPolicy`.holder = {_escape(user)})"
			)
		elif doctype in ("Hearth Asset", "Liability") and _has_field(doctype, "ownership_transferred"):
			transferred_clause = (
				f"or (`tab{doctype}`.circle is null and coalesce(`tab{doctype}`.ownership_transferred, 0) = 1 "
				f"and `tab{doctype}`.owner_user = {_escape(user)})"
			)
		else:
			transferred_clause = ""

		return f"{base} {transferred_clause})"

	return None


def resolve_user_link(value: str | None, user: str | None = None) -> str | None:
	"""Resolve Frappe Link-to-User placeholders used as field defaults."""
	if not value:
		return None
	if value == "__user__":
		return user or frappe.session.user
	return value


def _resolve_user_link(value: str | None, user: str | None = None) -> str | None:
	return resolve_user_link(value, user)


def get_circle_recipients(circle_name: str) -> list[str]:
	"""Return circle owner and member users for notifications."""
	if not circle_name or not frappe.db.exists("Circle", circle_name):
		return []

	circle = frappe.get_doc("Circle", circle_name)
	recipients: set[str] = set()
	owner = resolve_user_link(circle.owner_user)
	if owner:
		recipients.add(owner)
	for member in circle.members:
		if member.member_user:
			recipients.add(member.member_user)
	return sorted(recipients)


def get_circle_owner(circle_name: str | None, user: str | None = None) -> str | None:
	if not circle_name:
		return None
	owner_user = frappe.db.get_value("Circle", circle_name, "owner_user")
	return resolve_user_link(owner_user, user)


def _can_write_circle_record(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if doc.owner == user:
		return True
	return get_circle_owner(doc.get("circle"), user) == user


def _has_circle_read_access(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	return bool(doc.get("circle") and doc.circle in get_accessible_circles(user))


def _record_owner(doc, user: str | None = None) -> str:
	user = user or frappe.session.user
	if doc.doctype == "Policy":
		# For private records, do not treat holder as owner until transferred.
		if not doc.get("circle") and not doc.get("ownership_transferred") and doc.get("holder") and doc.holder != doc.owner:
			return doc.owner
		return _resolve_user_link(doc.get("holder"), user) or doc.owner
	if doc.doctype == "Hearth Asset":
		if (
			not doc.get("circle")
			and not doc.get("ownership_transferred")
			and doc.get("owner_user")
			and _resolve_user_link(doc.owner_user, user) != doc.owner
		):
			return doc.owner
		return _resolve_user_link(doc.get("owner_user"), user) or doc.owner
	if doc.doctype == "Circle":
		return _resolve_user_link(doc.get("owner_user"), user) or doc.owner
	if doc.doctype == "Liability":
		if (
			not doc.get("circle")
			and not doc.get("ownership_transferred")
			and doc.get("owner_user")
			and _resolve_user_link(doc.owner_user, user) != doc.owner
		):
			return doc.owner
		return _resolve_user_link(doc.get("owner_user"), user) or doc.owner
	return doc.owner


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	if doc.doctype == "Circle":
		if _resolve_user_link(doc.owner_user, user) == user:
			return True
		return any(m.member_user == user for m in doc.members)

	if doc.doctype in HEARTH_LINKED_DOCTYPES:
		# Circle sharing: members can read; write/delete limited to record or circle owner.
		if doc.get("circle"):
			if not _has_circle_read_access(doc, user):
				return False
			if ptype in ("write", "delete", "submit", "cancel", "amend"):
				return _can_write_circle_record(doc, user)
			return True

		# No-circle records are private to creator (doc.owner) until transferred.
		if doc.owner == user:
			return True

		if not doc.get("ownership_transferred"):
			return False

		# After transfer, allow the target user to access the record even if they did not create it.
		if doc.doctype == "Policy":
			return doc.get("holder") == user
		if doc.doctype in ("Hearth Asset", "Liability"):
			return _resolve_user_link(doc.get("owner_user"), user) == user

		return False

	return False


def get_circle_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Circle", user)


def get_policy_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Policy", user)


def get_hearth_asset_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Hearth Asset", user)


def get_asset_query_conditions(user: str | None = None) -> str | None:
	return get_hearth_asset_query_conditions(user)


def get_liability_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Liability", user)


def get_reminder_rule_query_conditions(user: str | None = None) -> str | None:
	return get_permission_query_conditions("Reminder Rule", user)


def circle_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def policy_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def hearth_asset_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def asset_has_permission(doc, ptype=None, user=None):
	return hearth_asset_has_permission(doc, ptype, user)


def liability_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)


def reminder_rule_has_permission(doc, ptype=None, user=None):
	return has_permission(doc, ptype, user)
