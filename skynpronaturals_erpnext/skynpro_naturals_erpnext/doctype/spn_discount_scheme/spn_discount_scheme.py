# -*- coding: utf-8 -*-
# Copyright (c) 2015, MN Technique and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class SPNDiscountScheme(Document):
	# def autoname(self):
	#  	self.name = "DSCH-" + frappe.utils.datetime.datetime.strftime(frappe.utils.getdate(self.scheme_month), "%m/%y") + "-"

	def validate(self):
		if self.scheme_month == "":
			frappe.throw(_("Please set Scheme Month."))

	# def after_insert(self):
	# 	if self.quantity_or_amount == "Item Quantity":
	# 		#Create campaign for discount scheme. Campaign will be set in Sales Invoice, against which item pricing rules can take effect.
	# 		cp = frappe.new_doc("Campaign")
	# 		cp.campaign_name = self.scheme_name
	# 		cp.insert()
	# 		frappe.db.commit()

	# 		frappe.db.set_value("SPN Discount Scheme", self.name, "campaign", self.scheme_name) 
	
	def add_discount_item(self, values):
		dsi = frappe.new_doc("SPN Discount Scheme Item")
		dsi.item = values.get("item")
		dsi.item_group = values.get("item_group")
		dsi.from_amount = values.get("from_amount")
		dsi.to_amount = values.get("to_amount")
		dsi.from_qty = values.get("from_qty")
		dsi.to_qty = values.get("to_qty")
		dsi.discount_pct = values.get("discount_pct")
		dsi.coupon_amount = values.get("coupon_amount")
		dsi.discount_scheme = self.name

		dsi.insert()
		frappe.db.commit()

		# if dsi.item: # or dsi.item_group:
		# 	pr = frappe.new_doc("Pricing Rule")
		# 	pr.title =  self.scheme_name + "/" + dsi.item

		# 	if dsi.item:
		# 		pr.apply_on = "Item Code" 
		# 		pr.item_code = dsi.item

		# 	pr.applicable_for = "Campaign"
		# 	pr.campaign = self.scheme_name
		# 	pr.min_qty = dsi.from_qty
		# 	pr.max_qty = dsi.to_qty
		# 	pr.priority = 10
		# 	pr.selling = 1
		# 	pr.valid_from = frappe.utils.get_datetime()
		# 	pr.price_or_discount = "Discount Percentage"
		# 	pr.discount_percentage = values.get("discount_pct")
		# 	pr.insert()
		# 	frappe.db.commit()


	def add_freebie(self, discount_item, values):
		fi = frappe.new_doc("SPN Discount Scheme Freebie")
		fi.freebie_item = values.get("freebie_item")
		fi.freebie_qty = values.get("freebie_qty")
		fi.against_scheme_item = discount_item
		fi.against_scheme = self.name
			
		fi.insert()
		frappe.db.commit()

	def get_discount_scheme_items(self):
		scheme_dtl_list = []
		discount_items = frappe.get_all("SPN Discount Scheme Item", filters={"discount_scheme":self.name}, fields=["*"], order_by="creation")

		for di in discount_items:
			scheme_detail = frappe._dict({
				"item": di,
				"freebies": frappe.get_all("SPN Discount Scheme Freebie", filters={"against_scheme_item": di.name}, fields=["*"])
			})
			scheme_dtl_list.append(scheme_detail)

			print scheme_detail
		
		return {"scheme_details": scheme_dtl_list}

	def delete_discount_item(self, discount_item):
		try:
			frappe.delete_doc("SPN Discount Scheme Item", discount_item)
		except Exception as e:
			return e.message
		else:
			return "Discount item '{0}'' deleted.".format(discount_item)



	def get_item_group_list(self, txt):
		"""Returns contacts (from autosuggest)"""
		txt = txt.replace('%', '')

		def get_item_groups():
			return filter(None, frappe.db.sql_list('select name from `tabItem Group` where name like %s',
				('%' + txt + '%')))
		try:
			out = filter(None, frappe.db.sql_list("""select distinct name from `tabItem Group` 
				where name like %(txt)s  order by
				if (locate( %(_txt)s, name), locate( %(_txt)s, name), 99999)""",
			        {'txt': "%%%s%%" % frappe.db.escape(txt),
		            '_txt': txt.replace("%", "")
			        })
			)
			if not out:
				out = get_item_groups()
		except Exception, e:
			if e.args[0]==1146:
				# no Contact, use User
				out = get_item_groups()
			else:
				raise

		return out
