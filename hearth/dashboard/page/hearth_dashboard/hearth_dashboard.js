frappe.pages["hearth-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Hearth Dashboard"),
		single_column: true,
	});

	page.main.addClass("hearth-dashboard-page");
	new HearthDashboard(page);
};

class HearthDashboard {
	constructor(page) {
		this.page = page;
		this.render();
	}

	render() {
		this.page.main.html(`<div class="hearth-dashboard-loading text-muted">${__("Loading…")}</div>`);
		frappe.call({
			method: "hearth.api.dashboard.get_dashboard_data",
			callback: (r) => {
				if (!r.message) return;
				this.page.main.html(this.build_html(r.message));
			},
		});
	}

	build_html(data) {
		return `
			<div class="hearth-dashboard">
				<div class="hearth-dashboard-summary">
					<div class="hearth-stat-card">
						<div class="hearth-stat-label">${__("Total Asset Value")}</div>
						<div class="hearth-stat-value">${format_currency(data.total_asset_value)}</div>
					</div>
					<div class="hearth-stat-card">
						<div class="hearth-stat-label">${__("Reminder Window")}</div>
						<div class="hearth-stat-value">${data.reminder_lead_days} ${__("days")}</div>
					</div>
				</div>
				<div class="hearth-dashboard-grid">
					${this.section(__("Upcoming Renewals"), data.upcoming_renewals, (row) =>
						`${row.policy_name} · ${row.renewal_date || ""}`
					)}
					${this.section(__("Expiring Policies"), data.expiring_policies, (row) =>
						`${row.policy_name} · ${row.maturity_date || ""}`
					)}
					${this.section(__("Liabilities Due"), data.liabilities_due, (row) =>
						`${row.liability_name} · ${row.due_date || ""}`
					)}
					${this.section(__("Assets Overview"), data.assets_overview, (row) =>
						`${row.asset_name} · ${format_currency(row.estimated_value || 0)}`
					)}
					${this.section(__("Recent Documents"), data.recent_documents, (row) =>
						`${row.title || row.attachment} · ${row.parenttype}`
					)}
				</div>
			</div>
		`;
	}

	section(title, rows, formatter) {
		const items =
			rows && rows.length
				? rows.map((row) => `<li class="hearth-list-item">${frappe.utils.escape_html(formatter(row))}</li>`).join("")
				: `<li class="hearth-list-item text-muted">${__("Nothing scheduled")}</li>`;
		return `
			<div class="hearth-panel">
				<h4>${title}</h4>
				<ul class="hearth-list">${items}</ul>
			</div>
		`;
	}
}
