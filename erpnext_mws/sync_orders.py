from __future__ import unicode_literals
import frappe
from frappe import _
from .exceptions import MWSError
from .utils import make_mws_log
from .sync_products import make_item
from .sync_customers import create_customer
from frappe.utils import flt, nowdate, cint
from .utils import setup_mws_orders
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note, make_sales_invoice

def sync_orders():
	conn = setup_mws_orders()
	orders =  conn.list_orders( marketplaceids=[marketplaceId],created_after='2015-10-23T12:00:00Z')
	mws_settings = frappe.get_doc("MWS Settings", "MWS Settings")
	response = orders._response_dict['ListOrdersResult']
	orders =  response['Orders']['Order']
	for order in orders:
		    try:
				create_customer_if_needed( order )
				create_order(mws_order, shopify_settings)
				frappe.local.form_dict.count_dict["orders"] += 1

			except MWSError, e:
				make_mws_log(status="Error", method="sync_mws_orders", message=frappe.get_traceback(),
					request_data=order, exception=True)
			except Exception, e:
				make_mws_log(title=e.message, status="Error", method="sync_mws_orders", message=frappe.get_traceback(),
					request_data=order, exception=True)


def create_customer_if_needed( order ):
	buyer_email = order['BuyerEmail']['value']
	customer = frappe.db._get("Customer", {"mws_buyer_email": buyer_email}, "name")
	if not customer:
		create_customer( order )

def create_sales_order(mws_order, mws_settings, company=None):
	conn = setup_mws_orders()
	id = mws_order['AmazonOrderId']['value']
	customer_id = mws_order['BuyerEmail']['value']
	so = frappe.db.get_value("Sales Order", {"mws_order_id": id }, "name") 
	items = conn.list_order_items( id )
	if not so:
		so = frappe.get_doc({
			"doctype": "Sales Order",
			"naming_series": "SO-MWS-",
			"mws_order_id": id,
			"customer": frappe.db.get_value("Customer", {"mws_customer_id": customer_id}, "name"),
			"delivery_date": nowdate(),
			"company": mws_settings.company,
			"selling_price_list": mws_settings.price_list,
			"ignore_pricing_rule": 1,
			"items": get_order_items(items, mws_settings),
			##"taxes": get_order_taxes(mws_order, mws_settings),
			"apply_discount_on": "Grand Total",
		})
		
		if company:
			so.update({
				"company": company,
				"status": "Draft"
			})
		so.flags.ignore_mandatory = True
		so.save(ignore_permissions=True)
		so.submit()

	else:
		so = frappe.get_doc("Sales Order", so)
		
	frappe.db.commit()
	return so

def get_order_items(order_items, mws_settings):
	items = []
	for mws_item in order_items:
		item_code = get_item_code(mws_item)
		items.append({
			"item_code": item_code,
			"item_name": mws_item['Title']['value'],
			"rate": mws_item['Amount']['value'],
			"delivery_date": nowdate(),
			"qty":  mws_item['QuantityOrdered']['value'],
			"stock_uom": mws_item['SellerSKU']['value'],
			##"warehouse": mws_settings.warehouse
		})
	return items

def get_item_code(mws_item):
	asin = mws_item['ASIN']['value']
	item_code = frappe.db.get_value("Item", {"mws_product_id": asin}, "item_code")
	return item_code

def get_order_taxes(mws_order, mws_settings):
	item_tax = mws_order['ItemTax']['value']
	taxes.append({
		"charge_type": _("On Net Total"),
		"account_head": get_tax_account_head(tax),
		"description": "Amazon order tax",
		"rate": item_tax['Amount']['value'],
		##"included_in_print_rate": ,
		##"cost_center": mws_settings.cost_center
	})
	return taxes

def get_item_code(mws_item):
	item_code = frappe.db.get_value("Item", {"mws_product_id": shopify_item.get("mws_id")}, "item_code")
	return item_code



