frappe.ui.form.on("Liability", {
	refresh(frm) {
		const can_transfer =
			!frm.is_new() &&
			!frm.doc.circle &&
			frm.doc.owner === frappe.session.user &&
			!!frm.doc.owner_user &&
			frm.doc.owner_user !== frm.doc.owner &&
			!frm.doc.ownership_transferred;

		frm.set_df_property("ownership_transferred", "read_only", can_transfer ? 0 : 1);
		if (!can_transfer) return;

		frm.add_custom_button(__("Transfer now"), () => {
			frappe.call({
				method: "hearth.liabilities.doctype.liability.liability.transfer_now",
				args: { name: frm.doc.name },
				callback: () => frm.reload_doc(),
			});
		});
	},

	ownership_transferred(frm) {
		if (!frm.doc.ownership_transferred) return;
		frappe.call({
			method: "hearth.liabilities.doctype.liability.liability.transfer_now",
			args: { name: frm.doc.name },
			callback: () => frm.reload_doc(),
		});
	},
});

