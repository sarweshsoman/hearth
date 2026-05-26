# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import add_days, today

from hearth.services.asset_visibility import get_asset_dashboard_totals
from hearth.services.reminder_service import get_reminder_lead_days


@frappe.whitelist()
def get_dashboard_data() -> dict:
	lead_days = get_reminder_lead_days()
	horizon = add_days(today(), lead_days)

	upcoming_renewals = frappe.get_list(
		"Policy",
		filters={
			"status": ["in", ["Active", "Pending Renewal"]],
			"renewal_date": ["between", [today(), horizon]],
		},
		fields=["name", "policy_name", "renewal_date", "provider", "status"],
		order_by="renewal_date asc",
		limit_page_length=10,
	)

	expiring_policies = frappe.get_list(
		"Policy",
		filters={
			"status": "Active",
			"maturity_date": ["between", [today(), horizon]],
		},
		fields=["name", "policy_name", "maturity_date", "provider"],
		order_by="maturity_date asc",
		limit_page_length=10,
	)

	liabilities_due = frappe.get_list(
		"Liability",
		filters={"status": ["!=", "Closed"], "due_date": ["between", [today(), horizon]]},
		fields=["name", "liability_name", "due_date", "emi_amount", "lender"],
		order_by="due_date asc",
		limit_page_length=10,
	)

	asset_totals = get_asset_dashboard_totals()

	return {
		"upcoming_renewals": upcoming_renewals,
		"expiring_policies": expiring_policies,
		"liabilities_due": liabilities_due,
		**asset_totals,
	}
