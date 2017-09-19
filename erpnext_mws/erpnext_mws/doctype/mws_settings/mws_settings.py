# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import requests.exceptions
from frappe.model.document import Document

class MWSSettings(Document):
	def validate(self):
		if self.enable_mws == 1:
			self.validate_access_credentials()
			self.validate_access()

	def validate_access_credentials(self):
		pass

	def validate_access(self):
		try:
			pass
		except requests.exceptions.HTTPError:
			frappe.db.rollback()
			self.set("enable_mws", 0)
			frappe.db.commit()
			frappe.throw(_("""Invalid MWS app credentials or access token"""), MWSSetupError)


@frappe.whitelist()
def get_series():
		return {
			"sales_order_series" : frappe.get_meta("Sales Order").get_options("naming_series") or "SO-MWS-",
		}
