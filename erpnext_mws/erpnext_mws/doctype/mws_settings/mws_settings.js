// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext_mws.mws_settings");

frappe.ui.form.on("MWS Settings", "onload", function(frm, dt, dn){
	frappe.call({
		method:"erpnext_mws.erpnext_mws.doctype.mws_settings.mws_settings.get_series",
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
	if(!frm.doc.__islocal && frm.doc.enable_mws === 1){
		frm.toggle_reqd("sales_invoice_series", frm.doc.sync_sales_invoice);

		frm.add_custom_button(__('Sync MWS'), function() {
			frappe.call({
				method:"erpnext_mws.api.sync_mws",
			})
		}).addClass("btn-primary");
	}
	frm.add_custom_button(__("MWS Log"), function(){
		frappe.set_route("List", "MWS Log");
	})
	
	frm.add_custom_button(__("Reset Last Sync Date"), function(){
		var dialog = new frappe.ui.Dialog({
			title: __("Reset Last Sync Date"),
			fields: [
				{"fieldtype": "Datetime", "label": __("Date"), "fieldname": "last_sync_date", "reqd": 1 },
				{"fieldtype": "Button", "label": __("Set last sync date"), "fieldname": "set_last_sync_date", "cssClass": "btn-primary"},
			]
		});

		dialog.fields_dict.set_last_sync_date.$input.click(function() {
			args = dialog.get_values();
			if(!args) return;

			frm.set_value("last_sync_datetime", args['last_sync_date']);
			frm.save();

			dialog.hide();
		});
		dialog.show();
	})


	frappe.call({
		method: "erpnext_mws.api.get_log_status",
		callback: function(r) {
			if(r.message){
				frm.dashboard.set_headline_alert(r.message.text, r.message.alert_class)
			}
		}
	})


})


$.extend(erpnext_mws.mws_settings, {
});
