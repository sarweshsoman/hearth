// Hearth global desk hooks
frappe.provide("hearth");

hearth.TRANSFER_FORMS = [
	{
		doctype: "Hearth Asset",
		owner_field: "owner_user",
		method: "hearth.hearth_assets.doctype.hearth_asset.hearth_asset.transfer_now",
	},
	{
		doctype: "Policy",
		owner_field: "holder",
		method: "hearth.policies.doctype.policy.policy.transfer_now",
	},
	{
		doctype: "Liability",
		owner_field: "owner_user",
		method: "hearth.liabilities.doctype.liability.liability.transfer_now",
	},
];

hearth._is_empty = function (value) {
	return value === undefined || value === null || value === "";
};

hearth._current_holder = function (frm, owner_field) {
	if (frm.doc.ownership_transferred) {
		return frm.doc[owner_field];
	}
	return frm.doc.owner;
};

hearth._can_initiate_transfer = function (frm, owner_field) {
	if (frm.doc.owner === frappe.session.user) {
		return true;
	}
	return (
		!!frm.doc.ownership_transferred && frm.doc[owner_field] === frappe.session.user
	);
};

hearth.can_show_transfer_button = function (frm, owner_field) {
	if (frm.is_new()) {
		return false;
	}
	if (!hearth._is_empty(frm.doc.circle)) {
		return false;
	}

	const target = frm.doc[owner_field];
	if (hearth._is_empty(target)) {
		return false;
	}

	if (!hearth._can_initiate_transfer(frm, owner_field)) {
		return false;
	}

	const current = hearth._current_holder(frm, owner_field);
	if (target === current) {
		return false;
	}

	if (typeof frm.has_perm === "function" && frm.has_perm("write")) {
		return true;
	}
	if (frm.perm && frm.perm[0] && frm.perm[0].write) {
		return true;
	}

	return frm.doc.owner === frappe.session.user;
};

hearth.run_transfer = function (frm, owner_field, transfer_method) {
	const args = { name: frm.doc.name };
	args[owner_field] = frm.doc[owner_field];

	frappe.call({
		method: transfer_method,
		args,
		freeze: true,
		freeze_message: __("Transferring…"),
		callback(r) {
			if (r.message && r.message.owner) {
				frappe.show_alert({
					message: __("Ownership transferred to {0}", [r.message.owner]),
					indicator: "green",
				});
			}
			// Leave the form — the initiator may no longer have permission to open it.
			frappe.set_route("List", frm.doctype);
		},
		error(r) {
			frappe.msgprint({
				title: __("Transfer failed"),
				message: (r && r.message) || __("Could not transfer this record."),
				indicator: "red",
			});
		},
	});
};

hearth.setup_transfer_actions = function (frm, owner_field, transfer_method) {
	if (!frm || !frm.doc) {
		return;
	}

	if (frm.fields_dict.ownership_transferred) {
		frm.set_df_property("ownership_transferred", "hidden", 1);
	}

	if (frm.remove_custom_button) {
		frm.remove_custom_button(__("Transfer now"));
	}

	if (hearth._can_initiate_transfer(frm, owner_field) || (frm.has_perm && frm.has_perm("write"))) {
		frm.set_df_property(owner_field, "read_only", 0);
	}

	if (!hearth.can_show_transfer_button(frm, owner_field)) {
		return;
	}

	const btn = frm.add_custom_button(__("Transfer now"), () => {
		hearth.run_transfer(frm, owner_field, transfer_method);
	});

	if (btn && frm.change_custom_button_type) {
		frm.change_custom_button_type(__("Transfer now"), null, "primary");
	}

	hearth._bind_owner_field_change(frm, owner_field, transfer_method);
};

hearth._bind_owner_field_change = function (frm, owner_field, transfer_method) {
	const field = frm.fields_dict[owner_field];
	if (!field || !field.$input) {
		return;
	}

	const rerun = () => hearth.setup_transfer_actions(frm, owner_field, transfer_method);
	field.$input.off("change.hearth-transfer").on("change.hearth-transfer", rerun);
};

hearth.register_transfer_form = function (doctype, owner_field, transfer_method) {
	const update = (frm) => {
		hearth.setup_transfer_actions(frm, owner_field, transfer_method);
		// Toolbar can finish after refresh; run once more.
		setTimeout(() => hearth.setup_transfer_actions(frm, owner_field, transfer_method), 200);
	};

	const handlers = {
		refresh: update,
		circle: update,
		after_save: update,
	};
	handlers[owner_field] = update;

	frappe.ui.form.on(doctype, handlers);
};

hearth.ready = function () {
	document.body.classList.add("hearth-app");
};

// Register immediately so doctype forms always get handlers.
hearth.TRANSFER_FORMS.forEach((cfg) => {
	hearth.register_transfer_form(cfg.doctype, cfg.owner_field, cfg.method);
});

$(document).on("app_ready", function () {
	if (frappe.boot.active_app === "hearth" || frappe.get_route_str().includes("hearth")) {
		hearth.ready();
	}
});
