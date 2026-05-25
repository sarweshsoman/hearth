# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Rename mistaken Hearth 'Asset' DocType that collided with ERPNext Asset."""

import frappe


def execute():
	hearth_module = "Hearth Assets"
	doctype_name = frappe.db.get_value("DocType", "Asset", "module")

	if doctype_name != hearth_module:
		_cleanup_orphan_hearth_asset_doctype()
		return

	_migrate_hearth_asset_records()
	_remove_hearth_asset_doctype_row()


def _migrate_hearth_asset_records():
	"""Move rows created with Hearth field layout into tabHearth Asset."""
	if not frappe.db.has_column("Asset", "asset_name"):
		return

	rows = frappe.db.sql(
		"""
		select name, asset_name, asset_type, owner_user, estimated_value,
			acquisition_date, circle, notes, owner, creation, modified, modified_by, docstatus
		from `tabAsset`
		where asset_name is not null and asset_name != ''
		""",
		as_dict=True,
	)

	for row in rows:
		if frappe.db.exists("Hearth Asset", row.name):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Hearth Asset",
				"name": row.name,
				"naming_series": "HEAR-AST-.#####",
				"asset_name": row.asset_name,
				"asset_type": row.asset_type or "Miscellaneous",
				"owner_user": row.owner_user or row.owner,
				"estimated_value": row.estimated_value,
				"acquisition_date": row.acquisition_date,
				"circle": row.circle,
				"notes": row.notes,
				"owner": row.owner,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_links=True)

		frappe.db.delete("Asset", row.name)


def _remove_hearth_asset_doctype_row():
	"""Remove Hearth's Asset DocType metadata so ERPNext can restore fixed Asset."""
	frappe.delete_doc("DocType", "Asset", force=True, ignore_missing=True)
	_restore_erpnext_asset_doctype()


def _restore_erpnext_asset_doctype():
	from frappe.modules.import_file import import_file_by_path

	path = frappe.get_app_path("erpnext", "assets", "doctype", "asset", "asset.json")
	import_file_by_path(path, force=True, ignore_version=True, reset_permissions=False)


def _cleanup_orphan_hearth_asset_doctype():
	"""Drop orphan DocType row if Hearth Asset already exists but old Asset row remains."""
	if frappe.db.exists("DocType", "Hearth Asset") and frappe.db.get_value("DocType", "Asset", "module") == "Hearth Assets":
		frappe.delete_doc("DocType", "Asset", force=True, ignore_missing=True)
