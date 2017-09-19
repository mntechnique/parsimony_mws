# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from .exceptions import MWSSetupError
from mws.orders import Orders

def is_mws_enabled():
	mws_settings = frappe.get_doc("MWS Settings")
	if not mws_settings.enable_mws:
		return False
	try:
		mws_settings.validate()
	except MWSSetupError:
		return False
	
	return True
	
def make_mws_log(title="Sync Log", status="Queued", method="sync_mws", message=None, exception=False, 
name=None, request_data={}):
	log.message = message if message else frappe.get_traceback()
	log.title = title[0:140]
	log.method = method
	log.status = status
	log.request_data= json.dumps(request_data)
	
	log.save(ignore_permissions=True)
	frappe.db.commit()

def setup_mws_orders():
	mws_settings = frappe.get_doc("MWS Settings", "MWS Settings")
	conn = Orders(mws_settings.mws_aws_access_key, 
		mws_settings.mws_aws_secret_key, 
		mws_settings.mws_sellder_id, 
		auth_token=mws_settings.mws_auth_token)
	return orders_api

def disable_mws_sync_on_exception()
        frappe.db.rollback()
        frappe.db.set_value("MWS Settings", None, "enable_mws", 0)
        frappe.db.commit()
