
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
		if so.get("username"):
			so_name = frappe.db.get_value("Sales Order", {"spn_tp_so_id": so.get("username")}, "name")

			if so_name:
				for x in xrange(1,10):
				 	print "Existing sO"

				sales_order = frappe.get_doc("Sales Order", so_name)
				sales_order.customer = so.get("Salon Name")
				for i in so.get("Order Form"):

					# print "Item for ", i.get("skucode"), [si for si in sales_order.items if si.item_code == i.get("skucode")]
					so_item = [si for si in sales_order.items if si.item_code == i.get("skucode")]

					so_item[0].item_code = i.get("skucode")
					so_item[0].item_name = i.get("skuname")
					so_item[0].qty = i.get("Quantity")
					so_item[0].rate = i.get("MRP")
					so_item[0].discount_percentage = i.get("Discount Percentage")
					so_item[0].amount= i.get("Selling Price")

			else:
				sales_order = frappe.new_doc("Sales Order")
				sales_order.customer = so.get("Salon Name")
				sales_order.delivery_date = so.get("orderdate")
				sales_order.transaction_date = so.get("orderdate")
				sales_order.spn_tp_so_id = so.get("username")
				for i in so.get("Order Form"):
					sales_order.append("items", {
						"item_code": i.get("skucode"),
						"item_name": i.get("skuname"),
						"qty": i.get("Quantity"),
						"rate": i.get("MRP"),
						"discount_percentage" : i.get("Discount Percentage"),
						"amount": i.get("Selling Price"),
						"description": i.get("skuname"),
						"warehouse": "Stores - SPN"
						})

		sales_order.save(ignore_permissions=True)
		frappe.db.commit()
	else:
		return "Please specify Sales Order"
	return sales_order


@frappe.whitelist(allow_guest=True)
def create_salon(salon=None):
	spn_salon = None
	if validate_request_header() != 1:
		return "You are not authorized to make this request."

	if salon:
		salon = json.loads(salon)
		if salon.get("username"):
			salon_name = frappe.db.get_value("SPN Salon", {"owner_name": salon.get("username")}, "name")

			if salon_name:
				spn_salon = frappe.get_doc("SPN Salon", salon_name)
			else:
				spn_salon = frappe.new_doc("SPN Salon")

			if spn_salon:
				spn_salon.latitude = salon.get("latitude")
				spn_salon.longitude = salon.get("longitude")
				spn_salon.boundary= salon.get("boundary")

				for i in salon.get("Place Form"):
					spn_salon.owner_name = i.get("Owner Name")
					spn_salon.phone_number = i.get("Phone Number")
					spn_salon.distributor = i.get("Name of Distributor")
					spn_salon.image = i.get("Image")
					spn_salon.email = i.get("Email ID")



		# spn_salon.update(salon)
		spn_salon.save(ignore_permissions=True)
		frappe.db.commit()
	else:
		return "Please specify Salon"

	return spn_salon



# "Owner Name": "value",
# 		"Phone Number": 2123,
# 		"Email ID": "amc@asd.com",
# 		"Name of Distributor": "value",
# 		"Image": "uri of the image"




	# return "Salon is " + salon if salon else "inexistent"


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

