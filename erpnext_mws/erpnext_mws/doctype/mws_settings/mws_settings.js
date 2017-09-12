// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext_mws.mws_settings");

frappe.ui.form.on("MWS Settings", "onload", function(frm, dt, dn){
	frappe.call({
		method:"erpnext_mws.erpnext_mws.doctype.mws_settings.mwsy_settings.get_series",
		callback:function(r){
			$.each(r.message, function(key, value){
				set_field_options(key, value)
			})
		}
	})
	erpnext_mws.mws_settings.setup_queries(frm);
})

frappe.ui.form.on("MWS Settings", "app_type", function(frm, dt, dn) {
	frm.toggle_reqd("api_key", (frm.doc.app_type == "Private"));
	frm.toggle_reqd("password", (frm.doc.app_type == "Private"));
})

frappe.ui.form.on("MWS Settings", "refresh", function(frm){
})


$.extend(erpnext_mws.mws_settings, {
});
