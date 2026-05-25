# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Apply full desk permissions for Hearth User accounts."""

import frappe
from frappe.utils import now

HEARTH_ROLE = "Hearth User"
DESK_ROLE = "Desk User"
HEARTH_ROLE_PROFILE = "Hearth User"

HEARTH_DOCTYPES = (
	"Circle",
	"Policy",
	"Hearth Asset",
	"Liability",
	"Reminder Rule",
)

from hearth.utils.modules import HEARTH_MODULE_PROFILE, apply_module_profile_to_hearth_users, sync_hearth_module_profile

REQUIRED_ROLES = (HEARTH_ROLE, DESK_ROLE)


def sync_hearth_role_profile() -> None:
	"""Role Profile bundles roles assigned when selected on a User."""
	if not frappe.db.exists("Role Profile", HEARTH_ROLE_PROFILE):
		frappe.db.sql(
			"""
			INSERT INTO `tabRole Profile`
				(name, role_profile, creation, modified, modified_by, owner, docstatus)
			VALUES (%s, %s, %s, %s, 'Administrator', 'Administrator', 0)
			""",
			(HEARTH_ROLE_PROFILE, HEARTH_ROLE_PROFILE, now(), now()),
		)

	frappe.db.delete(
		"Has Role",
		{"parent": HEARTH_ROLE_PROFILE, "parenttype": "Role Profile"},
	)
	for role in REQUIRED_ROLES:
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": HEARTH_ROLE_PROFILE,
				"parenttype": "Role Profile",
				"parentfield": "roles",
				"role": role,
			}
		).insert(ignore_permissions=True)


def should_apply_hearth_user_setup(user_doc) -> bool:
	if user_doc.name in ("Administrator", "Guest"):
		return False
	roles = {r.role for r in user_doc.roles}
	if HEARTH_ROLE in roles:
		return True
	if user_doc.get("role_profile_name") == HEARTH_ROLE_PROFILE:
		return True
	return False


def ensure_hearth_roles_on_user(user_doc) -> None:
	roles = {r.role for r in user_doc.roles}
	for role in REQUIRED_ROLES:
		if role not in roles:
			user_doc.append("roles", {"role": role})


def setup_hearth_user(user_doc) -> None:
	"""Apply roles, module profile, and blocked-module list for a Hearth user."""
	if not should_apply_hearth_user_setup(user_doc):
		return

	ensure_hearth_roles_on_user(user_doc)

	if not user_doc.get("role_profile_name"):
		user_doc.role_profile_name = HEARTH_ROLE_PROFILE

	user_doc.module_profile = HEARTH_MODULE_PROFILE


def apply_hearth_user_block_modules(user_name: str) -> None:
	"""Refresh block_modules from module profile (same as User.validate_allowed_modules)."""
	from hearth.utils.modules import get_blocked_module_rows

	if not frappe.db.get_value("User", user_name, "module_profile"):
		return

	blocked = get_blocked_module_rows()
	frappe.db.delete("Block Module", {"parent": user_name, "parenttype": "User"})
	for row in blocked:
		frappe.get_doc(
			{
				"doctype": "Block Module",
				"parent": user_name,
				"parenttype": "User",
				"parentfield": "block_modules",
				"module": row["module"],
			}
		).insert(ignore_permissions=True)
	frappe.clear_cache(user=user_name)


def sync_all_hearth_users() -> None:
	"""Run full Hearth User permission setup for every eligible user."""
	sync_hearth_module_profile()
	sync_hearth_role_profile()
	verify_hearth_doctype_permissions()
	sync_hearth_workspace()
	apply_module_profile_to_hearth_users()

	for user in frappe.get_all(
		"Has Role",
		filters={"role": HEARTH_ROLE, "parenttype": "User"},
		pluck="parent",
	):
		if user in ("Administrator", "Guest"):
			continue
		doc = frappe.get_doc("User", user)
		if "System Manager" in {r.role for r in doc.roles}:
			continue
		setup_hearth_user(doc)
		doc.flags.ignore_permissions = True
		doc.save()


def verify_hearth_doctype_permissions() -> None:
	"""Ensure DocPerm rows exist for Hearth User on all Hearth DocTypes."""
	standard_perms = {
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"export": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"share": 1,
	}

	for doctype in HEARTH_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue

		existing = frappe.db.exists(
			"DocPerm",
			{"parent": doctype, "role": HEARTH_ROLE, "permlevel": 0},
		)
		if existing:
			frappe.db.set_value("DocPerm", existing, standard_perms, update_modified=False)
			continue

		perm = frappe.get_doc(
			{
				"doctype": "DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": HEARTH_ROLE,
				"permlevel": 0,
				**standard_perms,
			}
		)
		perm.insert(ignore_permissions=True)

	frappe.clear_cache(doctype="DocType")

	_ensure_erpnext_coexistence_permissions()


def _ensure_erpnext_coexistence_permissions() -> None:
	"""When ERPNext is on the same site, allow read/select on Company only.

	Needed if a desk link still resolves to ERPNext Asset (Company is mandatory there).
	Hearth forms do not use Company.
	"""
	if "erpnext" not in frappe.get_installed_apps():
		return
	if not frappe.db.exists("DocType", "Company"):
		return

	perm = {
		"read": 1,
		"select": 1,
		"write": 0,
		"create": 0,
		"delete": 0,
		"export": 0,
		"print": 0,
		"email": 0,
		"report": 0,
		"share": 0,
	}

	existing = frappe.db.exists(
		"DocPerm",
		{"parent": "Company", "role": HEARTH_ROLE, "permlevel": 0},
	)
	if existing:
		frappe.db.set_value("DocPerm", existing, perm, update_modified=False)
		return

	frappe.get_doc(
		{
			"doctype": "DocPerm",
			"parent": "Company",
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": HEARTH_ROLE,
			"permlevel": 0,
			**perm,
		}
	).insert(ignore_permissions=True)


def sync_hearth_workspace() -> None:
	"""Re-import Hearth workspace and fix any stale links to ERPNext Asset."""
	from frappe.modules.import_file import import_file_by_path

	path = frappe.get_app_path("hearth", "dashboard", "workspace", "hearth", "hearth.json")
	import_file_by_path(path, force=True, ignore_version=True, reset_permissions=False)

	# Fix cached child rows that still point at ERPNext Asset
	for table in ("Workspace Link", "Workspace Shortcut"):
		frappe.db.sql(
			f"""
			update `tab{table}`
			set label = 'Hearth Asset', link_to = 'Hearth Asset'
			where parent = 'Hearth' and link_to = 'Asset'
			"""
		)

	frappe.clear_cache(doctype="Workspace")
