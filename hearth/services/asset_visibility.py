# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Dashboard totals and counts with circle / transfer visibility rules."""

import frappe

from hearth.permissions.circle_access import get_accessible_circles


def _has_ownership_transferred_field(doctype: str) -> bool:
	if not frappe.db.table_exists(doctype):
		return False
	try:
		return bool(frappe.db.has_column(doctype, "ownership_transferred"))
	except Exception:
		return False


def _owned_visibility_clause(
	user: str,
	circles: list[str],
	owner_field: str,
	has_transfer_field: bool,
) -> tuple[str, list]:
	"""SQL fragment for records that count toward a user's owned dashboard totals."""
	circle_placeholders = ", ".join(["%s"] * len(circles)) if circles else None
	parts: list[str] = []
	params: list = []

	if circles:
		parts.append(f"(r.circle in ({circle_placeholders}))")
		params.extend(circles)

	if has_transfer_field:
		private_clause = f"""
			(
				(r.circle is null or r.circle = '')
				and (
					(r.owner = %s and r.{owner_field} = %s)
					or (
						r.{owner_field} = %s
						and coalesce(r.ownership_transferred, 0) = 1
					)
				)
			)
		"""
		params.extend([user, user, user])
	else:
		private_clause = f"""
			(
				(r.circle is null or r.circle = '')
				and r.{owner_field} = %s
				and (r.owner = %s or r.{owner_field} = %s)
			)
		"""
		params.extend([user, user, user])

	parts.append(private_clause)
	return " or ".join(parts), params


def _count_visible_records(doctype: str, user: str, owner_field: str) -> int:
	if not frappe.db.table_exists(doctype):
		return 0
	if not frappe.db.has_column(doctype, owner_field):
		owner_field = "owner"

	circles = get_accessible_circles(user)
	has_transfer_field = _has_ownership_transferred_field(doctype)
	owned_where, params = _owned_visibility_clause(user, circles, owner_field, has_transfer_field)

	return frappe.db.sql(
		f"""
		select count(*)
		from `tab{doctype}` r
		where {owned_where}
		""",
		tuple(params),
	)[0][0]


def get_asset_dashboard_totals(user: str | None = None) -> dict:
	"""Return total_asset_value and transferable_assets_value for a user."""
	if not frappe.db.table_exists("Hearth Asset"):
		user = user or frappe.session.user
		return {
			"total_asset_value": 0,
			"transferable_assets_value": 0,
			"transferable_assets": [],
			"owned_assets": [],
			"asset_count": 0,
			"policy_count": _count_visible_records("Policy", user, "holder"),
			"liability_count": _count_visible_records("Liability", user, "owner_user"),
		}

	user = user or frappe.session.user
	circles = get_accessible_circles(user)
	has_transfer_field = _has_ownership_transferred_field("Hearth Asset")
	owned_where, owned_params = _owned_visibility_clause(user, circles, "owner_user", has_transfer_field)
	owned_where = owned_where.replace("r.", "ha.")
	total_asset_value = frappe.db.sql(
		f"""
		select coalesce(sum(ha.estimated_value), 0)
		from `tabHearth Asset` ha
		where {owned_where}
		""",
		tuple(owned_params),
	)[0][0]

	asset_count = frappe.db.sql(
		f"""
		select count(*)
		from `tabHearth Asset` ha
		where {owned_where}
		""",
		tuple(owned_params),
	)[0][0]

	owned_assets = frappe.db.sql(
		f"""
		select ha.name, ha.asset_name, ha.asset_type, ha.estimated_value, ha.circle
		from `tabHearth Asset` ha
		where {owned_where}
		order by ha.modified desc
		limit 20
		""",
		tuple(owned_params),
		as_dict=True,
	)

	transferable_assets_value = 0
	transferable_assets: list[dict] = []
	if has_transfer_field:
		transferable_assets = frappe.db.sql(
			"""
			select ha.name, ha.asset_name, ha.owner_user, ha.estimated_value
			from `tabHearth Asset` ha
			where (ha.circle is null or ha.circle = '')
				and ha.owner = %s
				and ha.owner_user is not null
				and ha.owner_user != %s
				and coalesce(ha.ownership_transferred, 0) = 0
			order by ha.modified desc
			limit 20
			""",
			(user, user),
			as_dict=True,
		)
		transferable_assets_value = sum((row.estimated_value or 0) for row in transferable_assets)

	policy_count = _count_visible_records("Policy", user, "holder")
	liability_count = _count_visible_records("Liability", user, "owner_user")

	return {
		"total_asset_value": total_asset_value,
		"transferable_assets_value": transferable_assets_value,
		"transferable_assets": transferable_assets,
		"owned_assets": owned_assets,
		"asset_count": asset_count,
		"policy_count": policy_count,
		"liability_count": liability_count,
	}
