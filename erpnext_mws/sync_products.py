from __future__ import unicode_literals
import frappe
from frappe import _
import requests.exceptions
from .exceptions import MWSError
from .utils import make_mws_log, disable_mws_sync_for_item
from erpnext.stock.utils import get_bin
from frappe.utils import cstr, flt, cint, get_files_path
from .utils import setup_mws_products

def create_item_if_needed(mws_item, mws_settings):
	conn = setup_mws_products()
	item_code =  mws_item['ASIN']['value']
	response = conn.get_matching_product(mws_settings.mws_marketplace_id, [mws_item['ASIN']['value']])._response_dict
	product = response['GetMatchingProductResult']['Product']
	attributes = product['AttributeSets']['ItemAttributes']
	warehouse = mws_settings.warehouse

	item_dict = {
		"doctype": "Item",
		"mws_product_id": item_code,
		"sync_with_mws": 1,
		"is_stock_item": 1,
		"item_code": item_code,
		"item_name": mws_item['Title']['value'],
		"description": "",
		"mws_description": "",
		"item_group": get_item_group(attributes['ProductGroup']['value']),
		"has_variants": False,
		"attributes":[],
		"stock_uom": _("Nos"),
		"stock_keeping_unit": mws_item['SellerSKU']['value'],
		"default_warehouse": warehouse,
		"image": attributes['SmallImage']['URL']['value'],
		"weight_uom": _("Nos"),
		"net_weight": attributes['PackageDimensions']['Weight']['value']
	}
	item_dict["web_long_description"] = ""
	current_item = frappe.db.get_value("Item", item_code, "item_code")
	if not current_item:
		new_item = frappe.get_doc(item_dict)
		new_item.insert()
		name = new_item.name

	else:
		item_details = get_item_details(mws_item)
		update_item(item_details, item_dict)
	frappe.db.commit()

def get_item_group(product_type=None):
	import frappe.utils.nestedset
	parent_item_group = frappe.utils.nestedset.get_root_of("Item Group")

	if product_type:
		if not frappe.db.get_value("Item Group", product_type, "name"):
			item_group = frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": product_type,
				"parent_item_group": parent_item_group,
				"is_group": "No"
			}).insert()
			return item_group.name
		else:
			return product_type
	else:
		return parent_item_group

def update_item(item_details, item_dict):
	item = frappe.get_doc("Item", item_details.name)
	item_dict["stock_uom"] = item_details.stock_uom

	if not item_dict["web_long_description"]:
		del item_dict["web_long_description"]

	del item_dict["description"]
	del item_dict["item_code"]
	del item_dict["item_name"]

	item.update(item_dict)
	item.flags.ignore_mandatory = True
	item.save()

def get_item_details(mws_item):
	item_details = {}

	item_details = frappe.db.get_value("Item", {"mws_product_id": mws_item['ASIN']['value']},
		["name", "stock_uom", "item_name"], as_dict=1)

	return item_details

def trigger_update_item_stock(doc, method):
	pass


