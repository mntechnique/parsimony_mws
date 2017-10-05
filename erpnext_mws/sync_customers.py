from __future__ import unicode_literals
import frappe
from frappe import _
from .utils import make_mws_log


def create_customer_if_needed(order):
	import frappe.utils.nestedset
	mws_settings = frappe.get_doc("MWS Settings", "MWS Settings")
	cust_name = order['BuyerName']['value']
	cust_id = order['BuyerEmail']['value']
	try:
		current_customer = frappe.db.get_value("Customer", cust_id, "name")
		if not current_customer is None:
			return
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
		if customer:
			create_customer_address(customer, order)
		frappe.db.commit()
	except Exception, e:
		make_mws_log(title=e.message, status="Error", method="create_customer", message=frappe.get_traceback(),
			request_data=order, exception=True)

def create_customer_address(customer, order):
	try :
		address_type = _("Billing")
		address_title = order['BuyerName']['value']
		shipping_address = order['ShippingAddress']
		frappe.get_doc({
			"doctype": "Address",
			##"mws_address_id": "",
			"address_title": address_title,
			"address_type": address_type,
			"address_line1": shipping_address['AddressLine1']['value'],
			"address_line2": "",
			"city": shipping_address['City']['value'],
			"state": shipping_address['StateOrRegion']['value'],
			"pincode": shipping_address['PostalCode']['value'],
			"country":  shipping_address['CountryCode']['value'],
			#"phone": "",
			"email_id": order['BuyerEmail']['value'],
			"links": [{
				"link_doctype": "Customer",
				"link_name": customer.name
			}]
		}).insert()
		
	except Exception, e:
		make_mws_log(title=e.message, status="Error", method="create_customer_address", message=frappe.get_traceback(),
			request_data=order, exception=True)
		

