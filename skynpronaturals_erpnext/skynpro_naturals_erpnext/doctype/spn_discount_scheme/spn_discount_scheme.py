# -*- coding: utf-8 -*-
# Copyright (c) 2015, MN Technique and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class SPNDiscountScheme(Document):
	def autoname(self):
	 	self.name = "DSCH-" + frappe.utils.datetime.datetime.strftime(frappe.utils.getdate(self.scheme_month), "%m/%y")

	def validate(self):
		if self.scheme_month == "":
			frappe.throw(_("Please set Scheme Month."))
	
	def add_discount_item(self, values):
		dsi = frappe.new_doc("SPN Discount Scheme Item")
		dsi.from_amount = values.get("from_amount")
		dsi.to_amount = values.get("to_amount")
		dsi.from_qty = values.get("from_qty")
		dsi.to_qty = values.get("to_qty")
		dsi.discount_pct = values.get("discount_pct")
		dsi.coupon_amount = values.get("coupon_amount")
		dsi.discount_scheme = self.name

		dsi.insert()
		frappe.db.commit()

	def add_freebie(self, discount_item, values):
		fi = frappe.new_doc("SPN Discount Scheme Freebie")
		fi.freebie_item = values.get("freebie_item")
		fi.freebie_qty = values.get("freebie_qty")
		fi.against_scheme_item = discount_item
		fi.against_scheme = self.name
			
		# for x in xrange(1,10):
		# 	print "Freebie Item: ", fi.freebie_item, "qty: ", fi.freebie_qty
			
		fi.insert()
		frappe.db.commit()

	def get_discount_scheme_items(self):
		scheme_dtl_list = []
		discount_items = frappe.get_all("SPN Discount Scheme Item", filters={"discount_scheme":self.name}, fields=["*"])

		for di in discount_items:
			scheme_detail = frappe._dict({
				"item": di,
				"freebies": frappe.get_all("SPN Discount Scheme Freebie", filters={"against_scheme_item": di.name}, fields=["*"])
			})
			scheme_dtl_list.append(scheme_detail)

			print scheme_detail
		

		return {"scheme_details": scheme_dtl_list}



