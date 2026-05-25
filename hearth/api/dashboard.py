# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import add_days, today

from hearth.services.document_service import get_recent_linked_documents
from hearth.services.reminder_service import get_reminder_lead_days


@frappe.whitelist()
def get_dashboard_data() -> dict:
	lead_days = get_reminder_lead_days()
	horizon = add_days(today(), lead_days)

	upcoming_renewals = frappe.get_all(
		"Policy",
		filters={
			"status": ["in", ["Active", "Pending Renewal"]],
			"renewal_date": ["between", [today(), horizon]],
		},
		fields=["name", "policy_name", "renewal_date", "provider", "status"],
		order_by="renewal_date asc",
		limit=10,
	)

	expiring_policies = frappe.get_all(
		"Policy",
		filters={
			"status": "Active",
			"maturity_date": ["between", [today(), horizon]],
		},
		fields=["name", "policy_name", "maturity_date", "provider"],
		order_by="maturity_date asc",
		limit=10,
	)

	liabilities_due = frappe.get_all(
		"Liability",
		filters={"status": ["!=", "Closed"], "due_date": ["between", [today(), horizon]]},
		fields=["name", "liability_name", "due_date", "emi_amount", "lender"],
		order_by="due_date asc",
		limit=10,
	)

	assets_overview = frappe.get_all(
		"Hearth Asset",
		fields=["name", "asset_name", "asset_type", "estimated_value"],
		order_by="modified desc",
		limit=10,
	)

	total_asset_value = frappe.db.sql(
		"""select coalesce(sum(estimated_value), 0) from `tabHearth Asset`""",
	)[0][0]

	return {
		"upcoming_renewals": upcoming_renewals,
		"expiring_policies": expiring_policies,
		"liabilities_due": liabilities_due,
		"recent_documents": get_recent_linked_documents(8),
		"assets_overview": assets_overview,
		"total_asset_value": total_asset_value,
		"reminder_lead_days": lead_days,
	}
