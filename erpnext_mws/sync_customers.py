from __future__ import unicode_literals
import frappe
from frappe import _
from .utils import make_mws_log


def create_customer(order):
	import frappe.utils.nestedset
	mws_settings = frappe.get_doc("MWS Settings", "MWS Settings")
	cust_name = order['BuyerName']['value']
	cust_id = order['BuyerEmail']['value']
	try:
		customer = frappe.get_doc({
			"doctype": "Customer",
			"name": cust_id,
			"customer_name" : cust_name,
			"sync_with_mws": 1,
			"territory": frappe.utils.nestedset.get_root_of("Territory"),
			"customer_type": _("Individual")
		})
		customer.flags.ignore_mandatory = True
		customer.insert()
		frappe.db.commit()
	except Exception, e:
		make_mws_log(title=e.message, status="Error", method="create_customer", message=frappe.get_traceback(),
			request_data=order, exception=True)
