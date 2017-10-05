from __future__ import unicode_literals
import frappe
import time
import dateutil.parser
from frappe import _
from .exceptions import MWSError
from .utils import make_mws_log, limit_text, do_sync_timeout
from .sync_customers import create_customer_if_needed
from .sync_products import create_item_if_needed
from frappe.utils import flt, nowdate, cint
from .utils import setup_mws_orders
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note, make_sales_invoice
from mws.utils import object_dict

def sync_orders():
	conn = setup_mws_orders()
	mws_settings = frappe.get_doc("MWS Settings", "MWS Settings")
	orders =  conn.list_orders( marketplaceids=[mws_settings.mws_marketplace_id],created_after='2015-10-23T12:00:00Z')
	response = orders._response_dict['ListOrdersResult']
	while True:
		orders =  response['Orders']['Order']
		for order in orders:
			    try:
					if not order['OrderStatus']['value'] in ['Unshipped', 'PartiallyShipped', 'Shipped']:
						continue
					create_customer_if_needed( order )
					create_sales_order(order, mws_settings)
			    except MWSError, e:
					make_mws_log(status="Error", method="sync_mws_orders", message=frappe.get_traceback(),
						request_data=order, exception=True)
			    except Exception, e:
					make_mws_log(title=e.message, status="Error", method="sync_mws_orders", message=frappe.get_traceback(),
						request_data=order, exception=True)
		if not "NextToken" in response.keys():
			break
		do_sync_timeout()
		orders =  conn.list_orders_by_next_token( response['NextToken']['value'] )
		response = orders._response_dict['ListOrdersByNextTokenResult']


def create_sales_order(mws_order, mws_settings, company=None):
	conn = setup_mws_orders()
	id = mws_order['AmazonOrderId']['value']
	customer_id = mws_order['BuyerEmail']['value']
	so = frappe.db.get_value("Sales Order", {"mws_order_id": id }, "name") 
	items = conn.list_order_items( id )
	response = items._response_dict['ListOrderItemsResult']
	items = response['OrderItems']['OrderItem']
	## python-amazon-mws will turn into a dict if only one "OrderItem" element
	## is there. Set to a list always.
	if type ( items ) is object_dict:
	   items = [ items ]

	if not so:
		ship_date = mws_order['LatestShipDate']['value']
	   	delivery_date = dateutil.parser.parse(ship_date).strftime("%Y-%m-%d")
		so = frappe.get_doc({
			"doctype": "Sales Order",
			"naming_series": "SO-MWS-",
			"mws_order_id": id,
			"customer": frappe.db.get_value("Customer", {"mws_customer_id": customer_id}, "name"),
			"delivery_date": delivery_date,
			##"company": mws_settings.company,
			#"selling_price_list": mws_settings.price_list,
			"ignore_pricing_rule": 1,
			"items": get_order_items(items, mws_settings),
			"taxes": get_order_taxes(items, mws_settings),
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
			"item_name": limit_text(mws_item['Title']['value']),
			"description": "",
			"rate": mws_item['ItemPrice']['Amount']['value'],
			"delivery_date": nowdate(),
			"qty": mws_item['QuantityOrdered']['value'],
			"stock_uom": mws_item['SellerSKU']['value'],
			"warehouse": mws_settings.warehouse
		})
		time.sleep( 1 )

	return items

def get_item_code(mws_item):
	asin = mws_item['ASIN']['value']
	item_code = frappe.db.get_value("Item", {"mws_product_id": asin}, "item_code")
	return item_code

def get_order_taxes(order_items, mws_settings):
	taxes = []
	for mws_item in order_items:
		item_tax = mws_item['ItemTax']['Amount']['value']
		taxes.append({
			"charge_type": _("On Net Total"),
			##"account_head": get_tax_account_head(tax),
			"description": "Amazon order tax",
			"rate": item_tax,
			##"included_in_print_rate": ,
			##"cost_center": mws_settings.cost_center
		})
	return taxes



