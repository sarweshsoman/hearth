# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Module access helpers for Hearth User desk visibility."""

import frappe
from frappe.utils import now

HEARTH_MODULE_PROFILE = "Hearth User"

HEARTH_MODULES = frozenset(
	{
		"Circles",
		"Policies",
		"Hearth Assets",
		"Liabilities",
		"Reminders",
		"Dashboard",
	}
)

# Minimal Frappe modules required for desk shell, auth, and notifications.
DESK_MODULES = frozenset(
	{
		"Core",
		"Desk",
		"Email",
		"Custom",
		"Geo",
		"Integrations",
		"Printing",
		"Workflow",
	}
)


def get_allowed_modules() -> frozenset[str]:
	return HEARTH_MODULES | DESK_MODULES


def get_blocked_module_rows() -> list[dict]:
	allowed = get_allowed_modules()
	return [{"module": name} for name in frappe.get_all("Module Def", pluck="name") if name not in allowed]


def sync_hearth_module_profile() -> None:
	"""Create/update Module Profile that hides ERPNext modules but keeps Hearth visible."""
	blocked = get_blocked_module_rows()
	now_ts = now()

	if not frappe.db.exists("Module Profile", HEARTH_MODULE_PROFILE):
		frappe.db.sql(
			"""
			INSERT INTO `tabModule Profile`
				(name, module_profile_name, creation, modified, modified_by, owner, docstatus)
			VALUES (%s, %s, %s, %s, 'Administrator', 'Administrator', 0)
			""",
			(HEARTH_MODULE_PROFILE, HEARTH_MODULE_PROFILE, now_ts, now_ts),
		)

	frappe.db.delete(
		"Block Module",
		{"parent": HEARTH_MODULE_PROFILE, "parenttype": "Module Profile"},
	)
	for row in blocked:
		frappe.get_doc(
			{
				"doctype": "Block Module",
				"parent": HEARTH_MODULE_PROFILE,
				"parenttype": "Module Profile",
				"parentfield": "block_modules",
				"module": row["module"],
			}
		).insert(ignore_permissions=True)


def apply_module_profile_to_hearth_users() -> None:
	"""Assign the Hearth module profile to users with Hearth User (non-admin)."""
	sync_hearth_module_profile()
	blocked = get_blocked_module_rows()

	for user in frappe.get_all(
		"Has Role",
		filters={"role": "Hearth User", "parenttype": "User"},
		pluck="parent",
	):
		if user in ("Administrator", "Guest"):
			continue

		doc = frappe.get_doc("User", user)
		if "System Manager" in {r.role for r in doc.roles}:
			continue

		if doc.module_profile == HEARTH_MODULE_PROFILE and len(doc.block_modules) == len(blocked):
			continue

		frappe.db.set_value("User", user, "module_profile", HEARTH_MODULE_PROFILE, update_modified=False)
		frappe.db.delete("Block Module", {"parent": user, "parenttype": "User"})
		for row in blocked:
			frappe.get_doc(
				{
					"doctype": "Block Module",
					"parent": user,
					"parenttype": "User",
					"parentfield": "block_modules",
					"module": row["module"],
				}
			).insert(ignore_permissions=True)

		frappe.clear_cache(user=user)


def should_use_hearth_module_profile(user_doc) -> bool:
	from hearth.utils.user_setup import should_apply_hearth_user_setup

	return should_apply_hearth_user_setup(user_doc)
