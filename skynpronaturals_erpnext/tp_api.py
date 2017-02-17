
from __future__ import unicode_literals
import frappe, json
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def sales_order(so=None):
	sales_order = None
	if validate_request_header() != 1:
		return "You are not authorized to make this request."
	
	if so :
		so = json.loads(so)  #sales_order 		
		if so.spn_tp_so_id:
			sales_order = frappe.get_doc("Sales Order", filters={"spn_tp_so_id":so.spn_tp_so_id})
			if sales_order.docstatus == 1:
				return "Cannot update submitted Sales Order" + str(so.spn_tp_so_id)
		else:
			sales_order = frappe.new_doc("Sales Order")
	
		sales_order.update(so)
		sales_order.save()
		frappe.db.commit()
	else:
		return "Please specify Sales Order"

	return sales_order

# @frappe.whitelist(allow_guest=True)

def validate_request_header():
	key_header = frappe.get_request_header("bzm-api-key")
	key_local = frappe.get_single("TechnoPurple Integration Settings").tp_api_key

	if key_header == "":
		return -1 #"Key header is blank"
	elif key_header != key_local:
		return 0 #"{0} != {1} : Key header does not match local key".format(key_header, key_local)
	else:
		return 1 #""