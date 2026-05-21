# Hearth hook extensions

Frappe app configuration lives in **`hearth/hooks.py`** (not this folder).

This directory is reserved for **documented extension hook modules** (event subscribers, request middleware) that you add over time. Do not name this package `hooks` at the Python package level — it would shadow `hooks.py` and break app loading.

Scheduled jobs live in `hearth/scheduled_tasks/`.
