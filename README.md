# Hearth

Hearth is a modular Frappe application for personal finance organization inside an existing bench. It stays isolated from ERPNext and Frappe core.

## Git repository root

**Initialize your Git repository here** (the Frappe app folder, not the whole bench):

```text
frappe-bench/apps/hearth/
```

| Path | Role |
|------|------|
| `frappe-bench/apps/hearth/` | **Repo root** — `README.md`, `pyproject.toml`, `.gitignore`, `license.txt` |
| `frappe-bench/apps/hearth/hearth/` | **Python package** — `hooks.py`, DocTypes, services (imported as `hearth`) |

Do **not** use `frappe-bench/apps/hearth/hearth/` as the repo root (that is only the inner package).

Do **not** commit `frappe-bench/`, `sites/`, or `env/` — those belong to the bench, not this app.

When installed on a bench, this app is placed at `apps/hearth/` and loaded with `bench get-app` / `bench install-app hearth`.

Hearth is **not** banking, investment advisory, payments, tax filing, or legal software. It focuses on policies, assets, liabilities, reminders, documents, and visibility through **Circles**.

## Philosophy

- **Isolation**: No edits to ERPNext or Frappe source; no core DocType patches.
- **Composition**: Extend behavior through hooks, services, and permission layers.
- **Maintainability**: Upgrade-safe patterns; overrides and monkey patches only when unavoidable, and only in dedicated modules.
- **Clarity**: Calm desk UI, structured data, explicit reminder rules.

## Architecture

```
apps/hearth/hearth/
├── api/              # Whitelisted desk APIs (dashboard, app permission)
├── adapters/         # Optional ERPNext wrappers (no tight coupling)
├── hearth_assets/    # Asset DocType module (label: Hearth Assets)
├── circles/          # Circle visibility module
├── dashboard/        # Workspace page & dashboard UI
├── fixtures/         # Exportable fixtures (optional)
├── scheduled_tasks/  # Scheduler entrypoints (not `hooks/` — avoids shadowing hooks.py)
├── liabilities/      # Liability DocType module
├── notifications/    # Desk notification config
├── overrides/        # DocType class overrides (empty by default)
├── patches/          # DB migration patches
├── permissions/      # Circle-based RBAC hooks
├── policies/         # Policy + document link child table
├── reminders/        # Reminder Rule infrastructure
├── services/         # Reminder, notification, document services
├── utils/            # Shared helpers
├── dashboard/workspace/  # Hearth desk workspace (must live inside a module folder)
└── public/           # CSS, JS, assets
```

### DocTypes

| DocType | Module | Purpose |
|---------|--------|---------|
| Circle | Circles | Visibility grouping (owner, members, level) |
| Circle Member | Circles | Child table for circle membership |
| Policy | Policies | Insurance, mediclaim, pension, obligations |
| Asset | Assets | Real estate, vehicles, deposits, gold, etc. |
| Liability | Liabilities | Loans and EMI tracking |
| Reminder Rule | Reminders | Scheduled reminders linked to records |
| Hearth Document Link | Policies | Child table for native File attachments |

### Reminders

- Policy saves sync **Renewal** reminder rules (lead window configurable via `hearth_reminder_days_before` in `site_config.json`, default 30 days).
- Liability saves sync **EMI Due** monthly reminders.
- Daily scheduler runs `hearth.hooks.scheduler.daily` → processes due rules and scans expiring policies.
- Notifications: email (`frappe.sendmail`) and in-app (`Notification Log`).

### Permissions

Circle-based visibility is implemented in `hearth.permissions.circle_access`:

- Record owner always has access.
- Records linked to a Circle are visible to circle owner and members.
- Write/delete on shared circle records is limited to record owner or circle owner.

Uses standard Frappe `permission_query_conditions` and `has_permission` hooks only.

### Extension strategy (preferred order)

1. `hooks.py` — scheduler, permissions, assets, install hooks  
2. `adapters/` — wrapper patterns for optional ERPNext touchpoints  
3. `override_doctype_class` — only when hooks are insufficient  
4. `override_whitelisted_methods` — API-level extension  
5. `doc_events` — document lifecycle  
6. `patches/` — isolated, documented, reversible data migrations  

No monkey patching is used in the initial scaffold.

## Setup

Prerequisites: existing Frappe bench with ERPNext (or Frappe only) and a site.

> **Site / app name collision:** If your site folder is also named `hearth`, Python may resolve the `hearth` package to `sites/hearth` before the app is on `PYTHONPATH`. Run `pip install -e apps/hearth` before `install-app`, or rename the site (e.g. `hearth.local`). `bench new-app hearth` also refuses to run when a site named `hearth` already exists — this app was bootstrapped via Frappe's boilerplate API.

> **ERPNext module collision:** The desk module **Assets** already exists in ERPNext. Hearth uses **Hearth Assets** as the module label (code package `hearth_assets/`) while the DocType remains **Asset**.

```bash
cd /path/to/frappe-bench

# App already at apps/hearth — install on site
bench --site <your-site> install-app hearth

bench build
bench --site <your-site> migrate
```

Assign roles on each **User**:

- **Hearth User** (required)
- **Desk User** (recommended)

The app auto-assigns the **Hearth User** module profile (blocks ERPNext modules, keeps Hearth visible). On save, users with **Hearth User** get **Module Profile** = `Hearth User`.

**User Permissions:** none — do not manually block Hearth modules on the user.

Optional site config:

```json
{
  "hearth_reminder_days_before": 30
}
```

## Development workflow

```bash
# After DocType JSON changes
bench --site <site> migrate

# Rebuild desk assets
bench build

# Run scheduler manually (debug)
bench --site <site> execute hearth.scheduled_tasks.scheduler.daily

# Console
bench --site <site> console
```

Use `pre-commit` in `apps/hearth` if you enable the generated config.

## Modules & navigation

Registered in `modules.txt`: Circles, Policies, Assets, Liabilities, Reminders, Dashboard.

Open **Hearth** workspace in the desk sidebar, or use the Hearth app tile → **Hearth Dashboard** page.

## License

MIT
