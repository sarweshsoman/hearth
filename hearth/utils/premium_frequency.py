# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""Premium frequency helpers for Policy records."""

import frappe

PREMIUM_FREQUENCY_MONTHS: dict[str, int | None] = {
	"Monthly": 1,
	"Quarterly": 3,
	"Half-Yearly": 6,
	"Yearly": 12,
	"Every 2 Years": 24,
	"Every 3 Years": 36,
	"One-time": None,
}


def get_premium_frequency_months(
	frequency: str | None,
	interval: int | None = None,
	unit: str | None = None,
) -> int | None:
	"""Return premium cadence in months, or None for one-time / unknown."""
	if not frequency:
		return None
	if frequency == "Custom":
		if not interval or interval < 1:
			return None
		if unit == "Years":
			return interval * 12
		return interval
	return PREMIUM_FREQUENCY_MONTHS.get(frequency)


def format_premium_frequency(
	frequency: str | None,
	interval: int | None = None,
	unit: str | None = None,
) -> str:
	if not frequency:
		return ""
	if frequency == "Custom" and interval and unit:
		unit_label = "year" if unit == "Years" else "month"
		if interval != 1:
			unit_label += "s"
		return f"Every {interval} {unit_label}"
	return frequency


def validate_premium_frequency_fields(doc) -> None:
	if doc.premium_frequency == "Custom":
		if not doc.premium_frequency_interval or doc.premium_frequency_interval < 1:
			frappe.throw(
				frappe._("Enter how often the premium is due when using a custom frequency."),
				title=frappe._("Premium Frequency"),
			)
		if not doc.premium_frequency_unit:
			frappe.throw(
				frappe._("Select months or years for the custom premium frequency."),
				title=frappe._("Premium Frequency"),
			)
	known = set(PREMIUM_FREQUENCY_MONTHS) | {"Custom"}
	if doc.premium_frequency not in known:
		frappe.throw(
			frappe._("Unknown premium frequency: {0}").format(doc.premium_frequency),
			title=frappe._("Premium Frequency"),
		)
