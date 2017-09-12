# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from .exceptions import MWSError
from .sync_orders import sync_orders
from .sync_customers import sync_customers
from .sync_products import sync_products, update_item_stock_qty
from .utils import disable_mws_sync_on_exception, make_mws_log
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def sync_mws():
	"Enqueue longjob for syncing MWS"
	enqueue("erpnext_mws.api.sync_mws_resources", queue='long')
	frappe.msgprint(_("Queued for syncing. It may take a few minutes to an hour if this is your first sync."))

@frappe.whitelist()
def sync_mws_resources():
	mws_settings = frappe.get_doc("MWS Settings")

	make_mws_log(title="Sync Job Queued", status="Queued", method=frappe.local.form_dict.cmd, message="Sync Job Queued")
	
	if mws_settings.enable_mws:
		try :
			frappe.db.set_value("MWS Settings", None, "last_sync_datetime", now_time)
			
			make_mws_log(title="Sync Completed", status="Success", method=frappe.local.form_dict.cmd)
		except Exception, e:
			pass
	elif frappe.local.form_dict.cmd == "erpnext_mws.api.sync_mws":
		make_mws_log(
			title="MWS connector is disabled",
			status="Error",
			method="sync_mws_resources",
			message=_("""MWS connector is not enabled. Click on 'Connect to MWS' to connect ERPNext and your MWS Seller Account"""),
			exception=True)

def validate_mws_settings(mws_settings):
	"""
		This will validate mandatory fields and access token or app credentials 
		by calling validate() of MWSsettings.
	"""
	try:
		mws_settings.save()
	except MWSError:
		disable_mws_sync_on_exception()

@frappe.whitelist()
def get_log_status():
	log = frappe.db.sql("""select name, status from `tabMWS Log` 
		order by modified desc limit 1""", as_dict=1)
	if log:
		if log[0].status=="Queued":
			message = _("Last sync request is queued")
			alert_class = "alert-warning"
		elif log[0].status=="Error":
			message = _("Last sync request was failed")
			alert_class = "alert-danger"
		else:
			message = _("Last sync request was successful")
			alert_class = "alert-success"
			
		return {
			"text": message,
			"alert_class": alert_class
		}
		
