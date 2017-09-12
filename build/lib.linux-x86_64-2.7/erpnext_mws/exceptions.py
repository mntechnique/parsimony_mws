from __future__ import unicode_literals
import frappe

class MWSError(frappe.ValidationError): pass
class MWSSetupError(frappe.ValidationError): pass
