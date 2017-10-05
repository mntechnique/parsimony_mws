from __future__ import unicode_literals
import frappe
from frappe import _
import requests.exceptions
import StringIO
import csv
import time
from .exceptions import MWSError
from .utils import make_mws_log, disable_mws_sync_for_item, limit_text
from erpnext.stock.utils import get_bin
from frappe.utils import cstr, flt, cint, get_files_path
from .utils import setup_mws_products, setup_mws_reports, do_sync_timeout
from mws.utils import object_dict

def sync_products():
	mws_settings = frappe.get_doc("MWS Settings", "MWS Settings")
	reports = setup_mws_reports()
	result = reports.request_report("_GET_FLAT_FILE_OPEN_LISTINGS_DATA_", 
		start_date="2015-10-23T12:00:00Z", 
		end_date="2017-10-02T12:00:00Z", 
		marketplaceids=[mws_settings.mws_marketplace_id])
	response = result._response_dict['RequestReportResult']
	report = response['ReportRequestInfo']
	id = report['ReportRequestId']['value']
	while True:
		f_report = reports.get_report_list(requestids=(id,))
		response = f_report._response_dict['GetReportListResult']
		if "ReportInfo" in response.keys():
			report_info = response['ReportInfo']
			report = reports.get_report(report_info['ReportId']['value'])
			csv_text = report.original
			string_io = StringIO.StringIO(csv_text)
			csv_rows = list( csv.reader( string_io, delimiter=str( '\t' ) )	)
			create_items_if_needed( csv_rows, mws_settings )
			break
		do_sync_timeout()

def create_items_if_needed( csv_rows, mws_settings ):
	conn = setup_mws_products()
	## skip the headers from the csv
	asins = [ row[ 1 ] for row in csv_rows[1:] ] 
	response = conn.get_matching_product(mws_settings.mws_marketplace_id, asins)._response_dict
	results = response['GetMatchingProductResult']
        if type ( results ) is object_dict:
           results = [ results ]

	for index in range( 0, len( results ) ):
		sku = csv_rows[ index ][ 0 ]
		result = results[ index ]
		if not "Error" in result.keys():
			create_item_if_needed( sku, result, mws_settings )
			continue
		make_mws_log(status="Error", method="create_items_if_needed", message=result['Error']['Message']['value'],
				request_data=result, exception=False)
	
def create_item_if_needed(sku, result, mws_settings):
	product = result['Product']
	attributes = product['AttributeSets']['ItemAttributes']
	item_code = result['ASIN']['value']
	warehouse = mws_settings.warehouse

	item_dict = {
		"doctype": "Item",
		"mws_product_id": item_code,
		"sync_with_mws": 1,
		"is_stock_item": 1,
		"item_code": item_code,
		"item_name": limit_text(attributes['Title']['value']),
		"description": "",
		"mws_description": "",
		"item_group": get_item_group(attributes['ProductGroup']['value']),
		"has_variants": False,
		"attributes":[],
		"stock_uom": _("Nos"),
		"stock_keeping_unit": sku,
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
		item_details = get_item_details( item_code )
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

def get_item_details(asin):
	item_details = {}

	item_details = frappe.db.get_value("Item", {"mws_product_id": asin},
		["name", "stock_uom", "item_name"], as_dict=1)

	return item_details

def trigger_update_item_stock(doc, method):
	pass


