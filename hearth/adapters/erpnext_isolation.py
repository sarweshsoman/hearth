# Copyright (c) 2026, Hearth and contributors
# License: MIT. See license.txt

"""
ERPNext isolation notes
-----------------------
Hearth DocTypes must not reuse ERPNext DocType names (e.g. ``Asset``).
ERPNext registers global ``doc_events`` on those names; a name collision loads
ERPNext controllers and fields (``is_existing_asset``, etc.) on Hearth forms.

Use prefixed names: ``Hearth Asset``, not ``Asset``.
"""

HEARTH_DOCTYPE_PREFIX = "Hearth "

# DocType names that must never be used by Hearth (ERPNext core / hooks).
RESERVED_ERPNEXT_DOCTYPES = frozenset(
	{
		"Asset",
		"Asset Capitalization",
		"Asset Repair",
		"Customer",
		"Supplier",
		"Item",
	}
)
