// Hearth global desk hooks
frappe.provide("hearth");

hearth.ready = function () {
	document.body.classList.add("hearth-app");
};

$(document).on("app_ready", function () {
	if (frappe.boot.active_app === "hearth" || frappe.get_route_str().includes("hearth")) {
		hearth.ready();
	}
});
