
from __future__ import unicode_literals
import frappe, json
import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond
from erpnext.controllers.queries import get_filters_cond
from frappe.utils import add_days, nowdate
from frappe.model.rename_doc import rename_doc

from frappe.utils.pdf import get_pdf
import pdfkit
import os


@frappe.whitelist()
def validate_sales_invoice(self, method):

	spn_warehouse = frappe.db.get_value("Sales Invoice","spn_warehouse")
	cust_ter = frappe.db.get_value("Sales Invoice","territory")
	cust_group = frappe.db.get_value("Sales Invoice","customer_group")

	if not self.naming_series:
		self.naming_series = get_naming_series(spn_warehouse,cust_ter,cust_group)

	#Disallow back-dated sales invoices
	# if frappe.utils.getdate(self.posting_date) < frappe.utils.datetime.date.today():
	# 	frappe.throw("Please set the posting date to either today's date or a future date.<br> Back-dated invoices are not allowed.")

@frappe.whitelist()
def validate_stock_entry(self, method):
	if self.spn_linked_transit_entry:
		#linked_entry = frappe.get_doc("Stock Entry","spn_linked_transit_entry")
		for d in self.get('items'):
			linked_entry_item_qty = frappe.db.get_value("Stock Entry Detail", filters={"parent": self.spn_linked_transit_entry, "item_code": d.item_code}, fieldname= "qty")
			if linked_entry_item_qty < d.qty-((d.spn_rejected_qty or 0.0) + (d.spn_qty_lost or 0.0)):
				 frappe.throw(_(" Item Qty should not exceed quantity in transit" ))


@frappe.whitelist()
def validate_purchase_receipt(self, method):
		#linked_entry = frappe.get_doc("Stock Entry","spn_linked_transit_entry")
		for d in self.get('items'):
			# linked_entry_item_qty = frappe.db.get_value("Stock Entry Detail", filters={"parent": self.spn_linked_transit_entry, "item_code": d.item_code}, fieldname= "qty")
			if d.rejected_qty != d.spn_rejected_qty + d.spn_transit_loss_qty:
				 frappe.throw(_("Row #{0}: Item Qty should not exceed quantity in transit {1}").format(d.idx, d.item_code))


@frappe.whitelist()
def get_naming_series(spn_warehouse, cust_ter, cust_group):

	warehouse_state = frappe.db.get_value("Warehouse", spn_warehouse, "state")

	if warehouse_state.lower() == "assam":
		if cust_group=="Assam Registered Distributor" and cust_ter == "Assam":
			return "GV-.#####"
		elif cust_group=="Assam Unregistered Distributor":
			return "GU-.#####"
		else:
			return "GC-.#####"
	elif warehouse_state.lower() == "maharashtra":
		if cust_group=="Maharashtra Registered Distributor" and cust_ter == "Maharashtra":
			return "BV-.#####"
		elif cust_group=="Maharashtra Unregistered Distributor":
			return "BU-.#####"
		else:
			return "BC-.#####"
	elif warehouse_state.lower() == "west bengal":
		if cust_group=="West Bengal Registered Distributor" and cust_ter == "West Bengal":
			return "WBV-.#####"
		elif cust_group=="West Bengal Unregistered Distributor":
			return "WBU-.#####"
		else:
			return "WBC-.#####"


	# for x in xrange(1,10):
	# 	#print "WAREHOUSE: ", spn_warehouse, " CUST_TER: ", cust_ter, "CUST_GROUP: ", cust_group
	# 	print warehouse_state.lower()

	# elif warehouse_state.lower() == "west bengal"
	# 	if cust_group=="West Bengal Registered Distributor" and cust_ter == "West Bengal":
	# 		return "WBV-.#####"
	# 	elif cust_group=="West Bengal Unregistered Distributor":
	# 		return "WBU-.#####"
	# 	else:
	# 		return "WBC-.#####"


@frappe.whitelist()
def get_terms_by_warehouse_state(spn_warehouse):

	warehouse_state = frappe.db.get_value("Warehouse", spn_warehouse, "state")
	existing_territory = frappe.db.get_value("Territory", warehouse_state)

	if not existing_territory:
		frappe.throw("Could not find corresponding Territory for Warehouse State {0}".format(warehouse_state))

	tc_name = frappe.db.get_value("Terms and Conditions", {"spn_territory": warehouse_state})

	# frappe.msgprint({"Warehouse State": warehouse_state, "Existing Territory": existing_territory, "TC Name": tc_name})
	return tc_name


@frappe.whitelist()
def get_spn_letter_head(spn_warehouse):
	return frappe.db.get_value("Warehouse",spn_warehouse,"spn_letterhead")
	# if spn_warehouse == "Bellezimo Professionale Products Pvt. Ltd. - SPN":
	#     if cust_group=="Assam Registered Distributor" and cust_ter == "Assam":
	#         return "GV-.#####"
	#     elif cust_group=="Assam Unregistered Distributor":
	#         return "GU-.#####"
	#     else:
	#         return "GC-.#####"
	# elif spn_warehouse == "Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN":
	#     if cust_group=="Maharashtra Registered Distributor" and cust_ter == "Maharashtra":
	#         return "BV-.#####"
	#     elif cust_group=="Maharashtra Unregistered Distributor":
	#         return "BU-.#####"
	#     else:
	#         return "BC-.#####"



@frappe.whitelist()
def get_details_from_transit_entry(transit_entry_name):
	#from frappe.model.mapper import get_mapped_doc
	transit_entry = frappe.get_doc("Stock Entry", transit_entry_name)
	return {"destination_warehouse": transit_entry.spn_to_warehouse, "items": transit_entry.items}


@frappe.whitelist()
def create_transit_loss_stock_entry(transit_entry_name):
	pass

def stock_entry_on_submit(self, method):
	make_new_stock_entry(self, method)
	make_new_reject_entry(self, method)

#Make material issue instead of transfer as the loss entry:
def make_new_stock_entry(self, method):
	items_with_loss_qty = [i for i in self.get('items') if i.spn_qty_lost > 0.0]
	if len(items_with_loss_qty) > 0:

		wh_src = frappe.db.get_value("SPN Settings","SPN Settings","spn_transit_warehouse")

		if self.spn_linked_transit_entry and self.from_warehouse == wh_src: #and self.to_warehouse != wh_loss:
			s = frappe.new_doc("Stock Entry")
			s.posting_date = self.posting_date
			s.posting_time = self.posting_time

			if not self.company:
				if self.source:
					self.company = frappe.db.get_value('Warehouse', self.from_warehouse, 'company')

			s.purpose = "Material Issue"# Transfer"
			s.spn_linked_transit_entry = self.name

			s.company = self.company or erpnext.get_default_company()
			for item in [item for item in self.items if (item.spn_qty_lost > 0)]:

				s.append("items", {
					"item_code": item.item_code,
					"s_warehouse": wh_src,
					"qty": item.spn_qty_lost,
					"basic_rate": item.basic_rate,
					"conversion_factor": 1.0,
					"serial_no": item.serial_no,
					'cost_center': item.cost_center,
					'expense_account': item.expense_account
				})

			s.save()
			s.submit()
			frappe.db.commit()

def make_new_reject_entry(self, method):

	for x in xrange(1,5):
		print "REJECT"

	items_with_loss_qty = [i for i in self.get('items') if i.spn_rejected_qty> 0.0]
	if len(items_with_loss_qty) > 0:

		wh_src = frappe.db.get_value("SPN Settings","SPN Settings","spn_transit_warehouse")

		if self.spn_linked_transit_entry and self.from_warehouse == wh_src: #and self.to_warehouse != wh_loss:
			s = frappe.new_doc("Stock Entry")
			s.posting_date = self.posting_date
			s.posting_time = self.posting_time

			if not self.company:
				if self.source:
					self.company = frappe.db.get_value('Warehouse', self.from_warehouse, 'company')

			s.purpose = "Material Transfer"
			s.spn_linked_transit_entry = self.name

			s.company = self.company or erpnext.get_default_company()
			for item in [item for item in self.items if (item.spn_rejected_qty > 0)]:
				print "SRC", wh_src, "FROM", item.spn_rejected_warehouse
				s.append("items", {
					"item_code": item.item_code,
					"s_warehouse": wh_src,
					"t_warehouse": item.spn_rejected_warehouse,
					"qty": item.spn_rejected_qty,
					"basic_rate": item.basic_rate,
					"conversion_factor": 1.0,
					"serial_no": item.serial_no,
					'cost_center': item.cost_center,
					'expense_account': item.expense_account
				})

			s.save()
			s.submit()
			frappe.db.commit()


#Change material transfer to material issue for loss.
def pr_on_submit(self, method):

	# for d in self.get('items'):
	#     loss_qty = frappe.db.get_value("Purchase Receipt Item", filters={"parent": self.naming_series, "item_code": d.item_code}, fieldname= "spn_transit_loss_qty")
	#wh_loss = frappe.db.get_value("SPN Settings","SPN Settings","spn_transit_loss_warehouse")
	# if not wh_loss:
	#     frappe.throw(_("Set default loss warehouse in SPN Settings"))

	items_with_loss_qty = [i for i in self.get('items') if i.spn_transit_loss_qty > 0.0]

	if len(items_with_loss_qty) > 0:
		p = frappe.new_doc("Stock Entry")
		p.posting_date = self.posting_date
		p.posting_time = self.posting_time
		p.purpose = "Material Issue"
		p.spn_stock_entry_type = "Default"
		p.company = self.company or erpnext.get_default_company()

		for item in items_with_loss_qty:
			p.append("items", {
				"item_code": item.item_code,
				"s_warehouse": item.warehouse,
				#"t_warehouse": wh_loss,
				"qty": item.spn_transit_loss_qty,
				"basic_rate": item.rate,
				"conversion_factor": 1.0,
				"serial_no": item.serial_no,
				'cost_center': item.cost_center,
			})

		p.save()
		p.submit()

		self.spn_stock_entry = p.name

		frappe.db.commit()


		# #frappe.db.set_value(self.doctype, self.name, "spn_stock_entry", p.name)
		# frappe.db.commit()

def pr_on_cancel(self, method):
	if self.spn_stock_entry:
		d = frappe.get_doc("Stock Entry",self.spn_stock_entry)
		d.cancel()
		frappe.db.commit()

	# tle = frappe.new_doc("Stock Entry")

	# orig_entry = frappe.get_doc("Stock Entry", transit_entry_name)

	# tle.purpose = "Material Transfer"
	# tle.posting_date = orig_entry.posting_date
	# tle.posting_time = orig_entry.posting_time

#Spec change: 170103: Show transit loss as material issue instead of material transfer.

def se_get_allowed_warehouses(doctype, txt, searchfield, start, page_len, filters):
	conditions = []

	wh_map_names = frappe.get_all("SPN User Warehouse Map", {"name":frappe.session.user})
	warehouse_clause = ""

	if len(wh_map_names) > 0:
		wh_map = frappe.get_doc("SPN User Warehouse Map", wh_map_names[0])
		if wh_map and len(wh_map.warehouses) > 0:
			warehouse_clause = "and name in (" + ",".join([("'" + wh.warehouse + "'") for wh in wh_map.warehouses]) + ")"

	return frappe.db.sql("""select name, warehouse_name from `tabWarehouse`
		where ({key} like %(txt)s or name like %(txt)s) {fcond} {mcond} {whcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			idx desc, name
		limit %(start)s, %(page_len)s""".format(**{
			'key': searchfield,
			'fcond': get_filters_cond(doctype, filters, conditions),
			'mcond': get_match_cond(doctype),
			'whcond': warehouse_clause
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

def csv_to_json(path, column_headings_row_idx=1, start_parsing_from_idx=2):
	import csv

	file_rows = []
	out_rows = []

	csv_path = frappe.utils.get_site_path() + path #'/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_si.csv' #frappe.utils.get_site_path() + settlement_csv
	#outfile_name = '/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_si_out.csv'

	#with open('/home/gaurav/Downloads/25a4cbe4397b494a_2016-12-03_2017-01-02.csv', 'rb') as csvfile:
	with open(csv_path, 'rb') as csvfile:
		rdr = csv.reader(csvfile, delimiter=str(','), quotechar=str('"'))

		for row in rdr:
			file_rows.append(row)

		final_json = {}
		json_data = final_json.setdefault("data", [])
		column_headings_row = file_rows[column_headings_row_idx]

		#Handle repeating columns
		processed_headings_row = []
		for col in column_headings_row:
			count = len([x for x in processed_headings_row if x == col])
			if count > 0:
				col = col + "_" + str(count)
			processed_headings_row.append(col)

		for i in xrange(start_parsing_from_idx, len(file_rows)):
			record_core = ""

			if len(file_rows[i]) == len(processed_headings_row):
				for j in range(0, len(processed_headings_row)):
					record_core += '"' +  processed_headings_row[j] + '" : "' + file_rows[i][j] + '", '

				record_json_string = "{" + record_core[:-2] + "}"
				json_data.append(json.loads(record_json_string))

		return final_json

		#print "FINAL JSON", final_json

#------
# def process_invoices(debit_to="Debtors - SPN", income_ac="Sales - SPN", cost_center="Main - SPN"):
# 	def process_voucher_no(voucher_no):


# 		naming_series = voucher_no[:-4] + "-#####"
# 		processed_voucher_no = voucher_no[:-4] + "-" + voucher_no[-4:].zfill(5)
# 		warehouse = ""

# 		#print "naming series", voucher_no[:-4].lower()

# 		if voucher_no[:-4].lower() in ["bc","bv","bu"]:
# 			warehouse = "(MAHARASHTRA, Bhiwandi) Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN"
# 		elif voucher_no[:-4].lower() in ["gv","gc", "gu"]:
# 			warehouse = "(ASSAM, Guwahati) Bellezimo Professionale Products Pvt. Ltd. C/o. Siddhi Vinayak Agencies - SPN"
# 		elif voucher_no[:-4].lower() in ["wbc","wbv","wbu"]:
# 			warehouse = "(WEST BENGAL, Kolkata) Bellezimo Professionale Products Pvt. Ltd. C/o. Alloy Associates - SPN"
# 		else:
# 			warehouse = ""

# 		#print "Voucher No: ", processed_voucher_no, "Naming Series: ", naming_series, "Warehouse: ", warehouse

# 		return processed_voucher_no, naming_series, warehouse

# 	def percentage_by_voucher_no(voucher_no):
# 		if "bc" in voucher_no.lower():
# 			return 2.0
# 		elif "bv" in voucher_no.lower():
# 			return 13.5
# 		elif "gv" in voucher_no.lower():
# 			return 15.0
# 		elif "gc" in voucher_no.lower():
# 			return 2.0
# 		elif "wbv" in voucher_no.lower():
# 			return 15.0
# 		else:
# 			return None

# 	def price_list_by_territory(territory):
# 		# if territory == "West Bengal":
# 		# 	return "West Bengal"
# 		# elif territory == "Gujarat":
# 		# 	return "Gujarat Registered Distributor"
# 		# else:
# 		return territory

# 	def account_head_by_territory(territory):
# 		return territory #+ " VAT - SPN"

# 	def stc_template_by_territory(territory):
# 		return territory #+ " VAT"

# 	out = []

# 	final_json = csv_to_json(path='/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_si.csv')
# 	rows = final_json["data"]

# 	unique_vouchers = list(set([v.get("Voucher No") for v in rows]))
# 	#unique_vouchers = []

# 	processed_recs = 0
# 	for uv in unique_vouchers:

# 		net_total = sum([float(i.get("Quantity")) * float(i.get("Rate")) for i in rows if i.get("Voucher No") == uv])
# 		grand_total = sum([
# 					(float(i.get("Quantity")) * float(i.get("Rate"))) +
# 					((float(i.get("Quantity")) * float(i.get("Rate"))) * (percentage_by_voucher_no(i.get("Voucher No")) if i.get("Percentage") == "null" else float(i.get("Percentage")) / 100)) for i in rows if i.get("Voucher No") == uv])

# 		#print "Voucher", uv, "NET TOTAL", net_total, "GRAND TOTAL", grand_total

# 		if net_total > 0:
# 			newrow = {}
# 			voucher_no, naming_series, warehouse = process_voucher_no(uv)
# 			newrow.update({"name": voucher_no})
# 			newrow.update({"naming_series": naming_series})

# 			voucher_items = [i for i in rows if i.get("Voucher No") == uv]

# 			percentage = (float(voucher_items[0]["Percentage"] if voucher_items[0]["Percentage"] != "null" else 0.0))
# 			#warehouse = frappe.db.sql("""select name from tabWarehouse where LOWER(state) = "{0}" """.format(voucher_items[0]["State"].lower()), as_dict=True)

# 			#print "WAREHOUSE", warehouse

# 			newrow.update({"posting_date" : frappe.utils.getdate(voucher_items[0]["Date"]),
# 			"company": "Bellezimo Professionale Products Pvt. Ltd.",
# 			"customer": voucher_items[0]["Party Name"],
# 			"currency": "INR",
# 			"conversion_rate": 1.0,
# 			"selling_price_list": price_list_by_territory(voucher_items[0]["State_1"]),
# 			"price_list_currency":"INR",
# 			"plc_conversion_rate" :1.0,
# 			"base_net_total": net_total,
# 			"base_grand_total": grand_total,
# 			"grand_total": grand_total,
# 			"debit_to": debit_to,
# 			"c_form_applicable": "Yes" if (voucher_items[0].get("Form Name") == "C") else "No",
# 			"is_return": 1 if (grand_total < 0) else 0,
# 			"due_date": frappe.utils.getdate(voucher_items[0]["Date"]),
# 			"territory": voucher_items[0]["State_1"],
# 			"taxes_and_charges": stc_template_by_territory(voucher_items[0]["State_1"]),
# 			"spn_warehouse": warehouse, #frappe.db.get_value("Warehouse", {"state": voucher_items[0]["State"]}),
# 			"~": "",
# 			"item_code": voucher_items[0]["Stock Item Alias"],
# 			"item_name": voucher_items[0]["Item Name"],
# 			"item_description": voucher_items[0]["Item Name"],
# 			"item_qty": voucher_items[0]["Quantity"],
# 			"item_rate": float(voucher_items[0]["Rate"]),
# 			"amount": float(voucher_items[0]["Quantity"]) * float(voucher_items[0]["Rate"]),
# 			"base_rate": float(voucher_items[0]["Rate"]),
# 			"base_amount": float(voucher_items[0]["Quantity"]) * float(voucher_items[0]["Rate"]),
# 			"income_account": income_ac,
# 			"cost_center": cost_center,
# 			"price_list_rate": frappe.db.get_value("Item Price", {"price_list":price_list_by_territory(voucher_items[0]["State_1"]), "item_name": voucher_items[0]["Stock Item Alias"] }, "price_list_rate"),
# 			"warehouse": warehouse,
# 			"~": "",
# 			"charge_type": "On Net Total",
# 			"account_head": account_head_by_territory(voucher_items[0]["State_1"]),
# 			"description": account_head_by_territory(voucher_items[0]["State_1"]),
# 			"row_id": "",
# 			"cost_center": cost_center,
# 			"rate": percentage,
# 			"tax_amount": net_total * (percentage/100),
# 			"total": grand_total,
# 			"tax_amount_after_discount_amount": grand_total,
# 			"base_tax_amount": net_total * percentage,
# 			"base_total": grand_total,
# 			"base_tax_amount_after_discount_amount": net_total * (percentage/100)
# 			})

# 			out.append(newrow)

# 			for x in xrange(1,len(voucher_items)):
# 				item_row = {}
# 				item_row.update({
# 					"item_code": voucher_items[x]["Stock Item Alias"],
# 					"item_name": voucher_items[x]["Item Name"],
# 					"item_description": voucher_items[x]["Item Name"],
# 					"item_qty": float(voucher_items[x]["Quantity"]),
# 					"item_rate":float(voucher_items[x]["Rate"]),
# 					"amount":float(voucher_items[x]["Quantity"]) * float(voucher_items[x]["Rate"]),
# 					"base_rate":float(voucher_items[x]["Rate"]),
# 					"base_amount": float(voucher_items[x]["Quantity"]) * float(voucher_items[x]["Rate"]),
# 					"income_account": income_ac,
# 					"cost_center": cost_center,
# 					"price_list_rate": frappe.db.get_value("Item Price", {"price_list" : price_list_by_territory(voucher_items[x]["State_1"]), "item_name": voucher_items[0]["Stock Item Alias"] }, "price_list_rate"),
# 					"warehouse": warehouse
# 					#"DO NOT Delete"
# 					# "~": "",
# 					# "charge_type": "On Net Total",
# 					# "account_head": account_head_by_territory(voucher_items[0]["State"]),
# 					# "description": account_head_by_territory(voucher_items[0]["State"]),
# 					# "row_id": "",
# 					# "cost_center": cost_center,
# 					# "rate": percentage,
# 					# "tax_amount": net_total * (percentage/100),
# 					# "total": grand_total,
# 					# "tax_amount_after_discount_amount": grand_total,
# 					# "base_tax_amount": net_total * percentage,
# 					# "base_total": grand_total,
# 					# "base_tax_amount_after_discount_amount": net_total * (percentage/100)
# 				})
# 				out.append(item_row)

# 			processed_recs += 1


# 	print "Total records processed:", processed_recs
# 	return out

# def prepsheet_si():
# 	import csv

# 	rows = process_invoices()
# 	column_headings_row = ["name", "naming_series", "posting_date", "company", "customer", "currency", "conversion_rate", "selling_price_list", "price_list_currency", "plc_conversion_rate", "base_net_total", "base_grand_total", "grand_total", "debit_to", "c_form_applicable", "is_return", "due_date", "territory", "taxes_and_charges", "spn_warehouse",
# 			"~", "item_code", "item_name", "item_description", "item_qty","item_rate", "amount", "base_rate", "base_amount", "income_account", "cost_center", "price_list_rate", "warehouse",
# 			"~", "charge_type", "account_head", "description", "row_id", "cost_center", "rate", "tax_amount", "total", "tax_amount_after_discount_amount", "base_tax_amount", "base_total", "base_tax_amount_after_discount_amount"]

# 	with open('/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_si_out.csv', 'w') as csvfile:
# 		fieldnames = column_headings_row #['last_name', 'first_name']
# 		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

# 		writer.writeheader()
# 		for row in rows:
# 			writer.writerow(row)


#Stock entry
def process_stock_entries():

	def get_processed_txn_no_and_series(txn_no):
		return {
				"txn_no": txn_no[:-4] + "-" + txn_no[-4:].zfill(5),
				"naming_series": txn_no[:-4] + "-#####",
			}


	def get_warehouses(godown_name):
		warehouse = ""
		reject_warehouse = ""

		if godown_name == "Guwahati":
			warehouse = "(ASSAM, Guwahati) Bellezimo Professionale Products Pvt. Ltd. C/o. Siddhi Vinayak Agencies - SPN"
			reject_warehouse = "Re"
		elif godown_name == "Bhiwandi":
			warehouse = "(MAHARASHTRA, Bhiwandi) Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN"
		elif godown_name == "Kolkata":
			warehouse = "(WEST BENGAL, Kolkata) Bellezimo Professionale Products Pvt. Ltd. C/o. Alloy Associates - SPN"
		elif godown_name == "Paonta Sahib":
			warehouse = godown_name

		return {
			"warehouse": warehouse,
			"reject_warehouse": reject_warehouse
		}

	final_json = csv_to_json('/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_stockentry.csv', 0, 1)
	rows = final_json["data"]

	unique_stnnos = list(set([v.get("STN No.") for v in rows]))

	out = []

	processed_recs = 0
	for stn_no in unique_stnnos:
		stn_items = [x for x in rows if x["STN No."] == stn_no]

		# print "STN No", stn_no
		# print "GRN No", stn_items[0]["GRN No."]
		# print "-----"
		# for item in stn_items:
		# 	print item
		# print "-----"

		newrow_stn = {
			"name": get_processed_txn_no_and_series(stn_no)["txn_no"],
			"naming_series": get_processed_txn_no_and_series(stn_no)["naming_series"],
			"purpose": "Material Issue",
			"company": "Bellezimo Professionale Products Pvt. Ltd.",
			"posting_date": frappe.utils.getdate(stn_items[0]["STN Date"]),
			"posting_time": frappe.utils.get_time("00:00:00"),
			"~": "",
			"item_code": stn_items[0]["Item Alias"],
			"qty": stn_items[0]["Quantity"],
			"uom": "Nos",
			"conversion_factor": 1.0,
			"stock_uom": "Nos",
			"transfer_qty": stn_items[0]["Quantity"],
			"s_warehouse": get_warehouses(stn_items[0]["Godown Name_1"])["warehouse"],
			"description": stn_items[0]["Item Name"],
			"~": ""
		}
		out.append(newrow_stn)

		for x in xrange(1, len(stn_items)):
			item_row = {
				"item_code": stn_items[x]["Item Alias"],
				"qty": stn_items[x]["Quantity"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"stock_uom": "Nos",
				"transfer_qty": stn_items[x]["Quantity"],
				"s_warehouse": get_warehouses(stn_items[x]["Godown Name_1"])["warehouse"],
				"description": stn_items[x]["Item Name"],
				"~": ""
			}
			out.append(item_row)



		newrow_grn = {
			"name": get_processed_txn_no_and_series(stn_items[0]["GRN No."])["txn_no"],
			"naming_series": get_processed_txn_no_and_series(stn_items[0]["GRN No."])["naming_series"],
			"purpose": "Material Receipt",
			"company": "Bellezimo Professionale Products Pvt. Ltd.",
			"posting_date": frappe.utils.getdate(stn_items[0]["Date"]),
			"posting_time": frappe.utils.get_time("00:00:00"),
			"~": "",
			"item_code": stn_items[0]["Item Alias_1"],
			"qty": stn_items[0]["Quantity_1"],
			"uom": "Nos",
			"conversion_factor": 1.0,
			"stock_uom": "Nos",
			"transfer_qty": stn_items[0]["Quantity_1"],
			"t_warehouse": get_warehouses(stn_items[0]["Godown Name"])["warehouse"],
			"description": stn_items[0]["Item Name_1"],
			"~": ""
		}
		out.append(newrow_grn)

		for x in xrange(1, len(stn_items)):
			grn_item_row = {
				"item_code": stn_items[x]["Item Alias_1"],
				"qty": stn_items[x]["Quantity_1"],
				"uom": "Nos",
				"conversion_factor": 1.0,
				"stock_uom": "Nos",
				"transfer_qty": stn_items[x]["Quantity_1"],
				"t_warehouse": get_warehouses(stn_items[x]["Godown Name"])["warehouse"],
				"description": stn_items[x]["Item Name_1"],
				"~": ""
			}
			out.append(grn_item_row)

		# processed_recs += 1
		# if processed_recs == 5:
		# 	break
	#print processed_recs
	return out

def prepsheet_stock_entry():
	import csv

	rows = process_stock_entries()
	column_headings_row = ["name", "naming_series", "purpose", "company", "posting_date", "posting_time", "~", "item_code", "description", "qty", "uom", "conversion_factor", "stock_uom", "transfer_qty", "s_warehouse", "t_warehouse", "~"]

	with open('/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_stockentry_out.csv', 'w') as csvfile:
		fieldnames = column_headings_row
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

		writer.writeheader()
		for row in rows:
			writer.writerow(row)

# @frappe.whitelist()
# def process_sheet_and_create_si(path_to_sheet, path_to_returns_map, debit_to="Debtors - SPN", income_ac="Sales - SPN", cost_center="Main - SPN"):
# 	from frappe.model.rename_doc import rename_doc

# 	def process_voucher_no(voucher_no):
# 		naming_series = voucher_no[:-4] + "-.#####"
# 		processed_voucher_no = voucher_no[:-4] + "-" + voucher_no[-4:].zfill(5)
# 		warehouse = ""

# 		#print "naming series", voucher_no[:-4].lower()

# 		if voucher_no[:-4].lower() in ["bc","bv","bu"]:
# 			warehouse = "(MAHARASHTRA, Bhiwandi) Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN"
# 		elif voucher_no[:-4].lower() in ["gv","gc", "gu"]:
# 			warehouse = "(ASSAM, Guwahati) Bellezimo Professionale Products Pvt. Ltd. C/o. Siddhi Vinayak Agencies - SPN"
# 		elif voucher_no[:-4].lower() in ["wbc","wbv","wbu"]:
# 			warehouse = "(WEST BENGAL, Kolkata) Bellezimo Professionale Products Pvt. Ltd. C/o. Alloy Associates - SPN"
# 		else:
# 			warehouse = ""

# 		#print "Voucher No: ", processed_voucher_no, "Naming Series: ", naming_series, "Warehouse: ", warehouse

# 		return processed_voucher_no, naming_series, warehouse

# 	def percentage_by_voucher_no(voucher_no):
# 		if "bc" in voucher_no.lower():
# 			return 2.0
# 		elif "bv" in voucher_no.lower():
# 			return 13.5
# 		elif "gv" in voucher_no.lower():
# 			return 15.0
# 		elif "gc" in voucher_no.lower():
# 			return 2.0
# 		elif "wbv" in voucher_no.lower():
# 			return 15.0
# 		elif "wbc" in voucher_no.lower():
# 			return 2.0
# 		else:
# 			return None

# 	def stc_template_by_naming_series_tax_percentage(voucher_no, tax_pct):
# 		if "bc" in voucher_no.lower():
# 			return "Maharashtra CST {0}%".format(tax_pct).replace(".0","")
# 		elif ("wbv" in voucher_no.lower()) or ("wbu" in voucher_no.lower()):
# 			return "West Bengal VAT {0}%".format(tax_pct).replace(".0","")
# 		elif "wbc" in voucher_no.lower():
# 			return "West Bengal CST {0}%".format(tax_pct).replace(".0","")
# 		elif ("bv" in voucher_no.lower()) or ("bu" in voucher_no.lower()):
# 			return "Maharashtra VAT {0}%".format(tax_pct).replace(".0","")
# 		elif ("gv" in voucher_no.lower()) or ("gu" in voucher_no.lower()):
# 			return "Assam VAT {0}%".format(tax_pct).replace(".0","")
# 		elif "gc" in voucher_no.lower():
# 			return "Assam CST {0}%".format(tax_pct).replace(".0","")
# 		else:
# 			return None

# 	def account_head_by_naming_series(voucher_no):
# 		if "bc" in voucher_no.lower():
# 			return "Maharashtra CST - SPN"
# 		elif ("wbv" in voucher_no.lower()) or ("wbu" in voucher_no.lower()):
# 			return "West Bengal VAT - SPN"
# 		elif "wbc" in voucher_no.lower():
# 			return "West Bengal CST - SPN"
# 		elif ("bv" in voucher_no.lower()) or ("bu" in voucher_no.lower()):
# 			return "Maharashtra VAT - SPN"
# 		elif ("gv" in voucher_no.lower()) or ("gu" in voucher_no.lower()):
# 			return "Assam VAT - SPN"
# 		elif "gc" in voucher_no.lower():
# 			return "Assam CST - SPN"
# 		else:
# 			return None

# 	def price_list_by_customer_or_net_total(customer, net_total):

# 		cg = frappe.db.get_value("Customer", {"name": customer}, "customer_group")

# 		if net_total <= 5.0: ##Less than two means memo invoice.
# 			return "MEMO/ZERO INVOICING"

# 		print "Customer Group", cg

# 		if ("maharashtra" in cg.lower()) or ("maharastra" in cg.lower()):
# 			return "Maharashtra"
# 		elif "west bengal" in cg.lower():
# 			return "West Bengal (VAT)"
# 		elif "assam" in cg.lower():
# 			return "Assam"
# 		elif "gujarat" in cg.lower():
# 			if "registered" in cg.lower():
# 				return "Gujarat Registered Distributor"
# 			elif "unregistered" in cg.lower():
# 				return "Gujarat Unregistered Distributor"
# 		else:
# 			return cg

# 	def get_corrected_territory(territory):
# 		if "maha" in territory.lower():
# 			return "Maharashtra"
# 		elif "delhi" in territory.lower():
# 			return "Delhi"
# 		else:
# 			return territory

# 	msgs = []

# 	returns = []

# 	out = []

# 	final_json = csv_to_json(path=path_to_sheet) #'/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_si.csv'
# 	rows = final_json["data"]


# 	returns_map_dict = csv_to_json(path_to_returns_map, 0, 1)

# 	unique_vouchers = list(set([v.get("Voucher No") for v in rows]))

# 	processed_recs = 0
# 	for uv in unique_vouchers:
# 		rowmsg = []
# 		rowmsg.append("-----")
# 		net_total = sum([float(i.get("Quantity")) * float(i.get("Rate")) for i in rows if i.get("Voucher No") == uv])
# 		grand_total = sum([
# 					(float(i.get("Quantity")) * float(i.get("Rate"))) +
# 					((float(i.get("Quantity")) * float(i.get("Rate"))) * (percentage_by_voucher_no(i.get("Voucher No")) if i.get("Percentage") == "null" else float(i.get("Percentage")) / 100)) for i in rows if i.get("Voucher No") == uv])


# 		if net_total < 0:
# 			rowmsg.append("{0} identified as return. Net Total: {1}".format(uv, net_total))
# 			returns.append(uv + "\n")
# 			#continue

# 		voucher_no, naming_series, warehouse = process_voucher_no(uv)

# 		#rowmsg.append("Voucher No: {0}".format(uv))
# 		print "Voucher No: ", uv, "Processed voucher no: ", voucher_no

# 		if frappe.db.get_value("Sales Invoice", {"name": voucher_no}, "name"):
# 			rowmsg.append("{0} already exists".format(voucher_no))
# 			print voucher_no, " already exists."
# 			continue

# 		#newrow.update({"name": voucher_no})
# 		#newrow.update({"naming_series": naming_series})

# 		voucher_items = [i for i in rows if i.get("Voucher No") == uv]

# 		if not frappe.db.get_value("Customer", {"name": voucher_items[0]["Party Name"]}, "name"):
# 			rowmsg.append("Customer '{0}' not found".format(voucher_items[0]["Party Name"]))
# 			print "Customer ", voucher_items[0]["Party Name"], " not found."
# 			continue

# 		percentage = (float(voucher_items[0]["Percentage"] if voucher_items[0]["Percentage"] != "null" else 0.0))
# 		#warehouse = frappe.db.sql("""select name from tabWarehouse where LOWER(state) = "{0}" """.format(voucher_items[0]["State"].lower()), as_dict=True)

# 		#print "WAREHOUSE", warehouse

# 		si = frappe.new_doc("Sales Invoice")
# 		si.naming_series = naming_series
# 		si.posting_date = frappe.utils.getdate(voucher_items[0]["Date"])
# 		si.company = "Bellezimo Professionale Products Pvt. Ltd."
# 		si.customer = voucher_items[0]["Party Name"]
# 		si.currency = "INR"
# 		si.conversion_rate = 1.0
# 		si.selling_price_list = price_list_by_customer_or_net_total(voucher_items[0]["Party Name"], net_total)

# 		# rowmsg.append("Selling Price List: {0}".format(si.selling_price_list))
# 		# print "Selling Price List", si.selling_price_list

# 		si.price_list_currency = "INR"
# 		si.plc_conversion_rate = 1.0
# 		si.base_net_total = net_total
# 		si.base_grand_total = grand_total
# 		si.grand_total = grand_total
# 		si.debit_to = debit_to
# 		si.c_form_applicable = "Yes" if (voucher_items[0].get("Form Name") == "C") else "No"
# 		si.is_return = 1 if (grand_total < 0) else 0
# 		si.due_date = frappe.utils.getdate(voucher_items[0]["Date"])
# 		si.territory = get_corrected_territory(voucher_items[0]["State_1"])
# 		si.taxes_and_charges = stc_template_by_naming_series_tax_percentage(voucher_no, percentage)
# 		si.spn_warehouse = warehouse #frappe.db.get_value("Warehouse", {"state": voucher_items[0]["State"]})

# 		if net_total < 0:
# 			si.is_return = "Yes"
# 			return_against = [r['Original Invoice'] for r in returns_map_dict["data"] if r["Cancelled Invoice"] == uv]

# 			if len(return_against) > 0:
# 				processed_voucher_no = process_voucher_no(return_against[0])[0]

# 				rowmsg.append("Return against: {0}".format(processed_voucher_no))

# 				si.return_against = processed_voucher_no

# 		for item in voucher_items:

# 			si.append("items", {
# 				"item_code": item["Stock Item Alias"],
# 				"item_name": item["Item Name"],
# 				"description": item["Item Name"],
# 				"qty": float(item["Quantity"]),
# 				"rate": float(item["Rate"]),
# 				"amount": float(item["Quantity"]) * float(item["Rate"]),
# 				"base_rate": float(item["Rate"]),
# 				"base_amount": float(item["Quantity"]) * float(item["Rate"]),
# 				"income_account": income_ac,
# 				"cost_center": cost_center,
# 				"price_list_rate": frappe.db.get_value("Item Price", {"price_list": si.selling_price_list, "item_name": item["Stock Item Alias"] }, "price_list_rate"),
# 				"warehouse": warehouse,
# 			})

# 		si.append("taxes", {
# 			"charge_type": "On Net Total",
# 			"account_head": account_head_by_naming_series(voucher_no),
# 			"description": account_head_by_naming_series(voucher_no),
# 			"cost_center": cost_center,
# 			"rate": percentage,
# 			"tax_amount": net_total * (percentage/100),
# 			"total": grand_total,
# 			"tax_amount_after_discount_amount": grand_total,
# 			"base_tax_amount": net_total * percentage,
# 			"base_total": grand_total,
# 			"base_tax_amount_after_discount_amount": net_total * (percentage/100)
# 		})

# 		try:
# 			si.save()
# 			frappe.db.commit()
# 			print "Saved as", si.name
# 			rowmsg.append("Invoice Saved. ({0})".format(si.name))
# 			rename_doc("Sales Invoice", si.name, voucher_no, force=True)
# 			print "Renamed to", voucher_no
# 			rowmsg.append("Renamed to {0}".format(voucher_no))
# 		except Exception as e:
# 			print "SI '" + voucher_no + "' not saved. {0}".format(e)
# 			rowmsg.append("Invoice '{0}' not saved: {1}".format(voucher_no, e))

# 		processed_recs += 1

# 		rowmsg.append("-----")
# 		#rowmsg.append("Records processed {0}".format(processed_recs))
# 		msgs.append("\n".join(rowmsg))

# 	msgs.append("------\n" + "Returns" + "------\n" + "\n".join(returns))

# 		# if processed_recs == 5:
# 		# 	break

# 	print "Total records processed:", processed_recs
# 	msgs.append("Total records processed: {0}".format(processed_recs))

# 	content = "\n".join(msgs)

# 	# frappe.local.response.filename = "{filename}.pdf".format(filename="si_log_{0}".format(frappe.utils.get_datetime()))
# 	# frappe.local.response.filecontent = get_log_dump(content)
# 	# frappe.local.response.type = "download"

# 	# #Print rowmsg
# 	# with open("/home/frappe/si_log.txt", "w") as txtfile:
# 	#
# 	# 	txtfile.write(content)

# 	return content



# def get_log_dump(filecontent):
# 	fname = os.path.join("/tmp", "si-import-log-{0}.pdf".format(frappe.generate_hash()))

# 	try:
# 		pdfkit.from_string(filecontent, fname, options=options or {})

# 		with open(fname, "rb") as fileobj:
# 			filedata = fileobj.read()

# 	except IOError, e:
# 		if ("ContentNotFoundError" in e.message
# 			or "ContentOperationNotPermittedError" in e.message
# 			or "UnknownContentError" in e.message
# 			or "RemoteHostClosedError" in e.message):

# 			# allow pdfs with missing images if file got created
# 			if os.path.exists(fname):
# 				with open(fname, "rb") as fileobj:
# 					filedata = fileobj.read()

# 			else:
# 				frappe.throw(_("PDF generation failed because of broken image links"))
# 		else:
# 			raise

# 	finally:
# 		cleanup(fname)


# 	return filedata


# @frappe.whitelist()
# def process_sheet_and_create_si(path_to_sheet, path_to_returns_map, debit_to="Debtors - SPN", income_ac="Sales - SPN", cost_center="Main - SPN"):
# 	from frappe.model.rename_doc import rename_doc

# 	def process_voucher_no(voucher_no):
# 		naming_series = voucher_no[:-4] + "-.#####"
# 		processed_voucher_no = voucher_no[:-4] + "-" + voucher_no[-4:].zfill(5)
# 		warehouse = ""

# 		#print "naming series", voucher_no[:-4].lower()

# 		if voucher_no[:-4].lower() in ["bc","bv","bu"]:
# 			warehouse = "(MAHARASHTRA, Bhiwandi) Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN"
# 		elif voucher_no[:-4].lower() in ["gv","gc", "gu"]:
# 			warehouse = "(ASSAM, Guwahati) Bellezimo Professionale Products Pvt. Ltd. C/o. Siddhi Vinayak Agencies - SPN"
# 		elif voucher_no[:-4].lower() in ["wbc","wbv","wbu"]:
# 			warehouse = "(WEST BENGAL, Kolkata) Bellezimo Professionale Products Pvt. Ltd. C/o. Alloy Associates - SPN"
# 		else:
# 			warehouse = ""

# 		#print "Voucher No: ", processed_voucher_no, "Naming Series: ", naming_series, "Warehouse: ", warehouse

# 		return processed_voucher_no, naming_series, warehouse

# 	def percentage_by_voucher_no(voucher_no):
# 		if "bc" in voucher_no.lower():
# 			return 2.0
# 		elif "bv" in voucher_no.lower():
# 			return 13.5
# 		elif "gv" in voucher_no.lower():
# 			return 15.0
# 		elif "gc" in voucher_no.lower():
# 			return 2.0
# 		elif "wbv" in voucher_no.lower():
# 			return 15.0
# 		elif "wbc" in voucher_no.lower():
# 			return 2.0
# 		else:
# 			return None

# 	def stc_template_by_naming_series_tax_percentage(voucher_no, tax_pct):
# 		if "bc" in voucher_no.lower():
# 			return "Maharashtra CST {0}%".format(tax_pct).replace(".0","")
# 		elif ("wbv" in voucher_no.lower()) or ("wbu" in voucher_no.lower()):
# 			return "West Bengal VAT {0}%".format(tax_pct).replace(".0","")
# 		elif "wbc" in voucher_no.lower():
# 			return "West Bengal CST {0}%".format(tax_pct).replace(".0","")
# 		elif ("bv" in voucher_no.lower()) or ("bu" in voucher_no.lower()):
# 			return "Maharashtra VAT {0}%".format(tax_pct).replace(".0","")
# 		elif ("gv" in voucher_no.lower()) or ("gu" in voucher_no.lower()):
# 			return "Assam VAT {0}%".format(tax_pct).replace(".0","")
# 		elif "gc" in voucher_no.lower():
# 			return "Assam CST {0}%".format(tax_pct).replace(".0","")
# 		else:
# 			return None

# 	def account_head_by_naming_series(voucher_no):
# 		if "bc" in voucher_no.lower():
# 			return "Maharashtra CST - SPN"
# 		elif ("wbv" in voucher_no.lower()) or ("wbu" in voucher_no.lower()):
# 			return "West Bengal VAT - SPN"
# 		elif "wbc" in voucher_no.lower():
# 			return "West Bengal CST - SPN"
# 		elif ("bv" in voucher_no.lower()) or ("bu" in voucher_no.lower()):
# 			return "Maharashtra VAT - SPN"
# 		elif ("gv" in voucher_no.lower()) or ("gu" in voucher_no.lower()):
# 			return "Assam VAT - SPN"
# 		elif "gc" in voucher_no.lower():
# 			return "Assam CST - SPN"
# 		else:
# 			return None

# 	def price_list_by_customer_or_net_total(customer, net_total):

# 		cg = frappe.db.get_value("Customer", {"name": customer}, "customer_group")

# 		if net_total <= 5.0: ##Less than two means memo invoice.
# 			return "MEMO/ZERO INVOICING"

# 		print "Customer Group", cg

# 		if ("maharashtra" in cg.lower()) or ("maharastra" in cg.lower()):
# 			return "Maharashtra"
# 		elif "west bengal" in cg.lower():
# 			return "West Bengal (VAT)"
# 		elif "assam" in cg.lower():
# 			return "Assam"
# 		elif "gujarat" in cg.lower():
# 			if "registered" in cg.lower():
# 				return "Gujarat Registered Distributor"
# 			elif "unregistered" in cg.lower():
# 				return "Gujarat Unregistered Distributor"
# 		else:
# 			return cg

# 	def get_corrected_territory(territory):
# 		if "maha" in territory.lower():
# 			return "Maharashtra"
# 		elif "delhi" in territory.lower():
# 			return "Delhi"
# 		else:
# 			return territory


# 	#Returns map.
# 	returns_map_dict = csv_to_json(path_to_returns_map, 0, 1)

# 	msgs = []

# 	returns = []

# 	out = []

# 	final_json = csv_to_json(path=path_to_sheet)
# 	rows = final_json["data"]

# 	unique_vouchers = list(set([v.get("Voucher No") for v in rows]))

# 	processed_recs = 0
# 	for uv in unique_vouchers:
# 		rowmsg = []
# 		net_total = sum([float(i.get("Quantity")) * float(i.get("Rate")) for i in rows if i.get("Voucher No") == uv])
# 		grand_total = sum([
# 					(float(i.get("Quantity")) * float(i.get("Rate"))) +
# 					((float(i.get("Quantity")) * float(i.get("Rate"))) * (percentage_by_voucher_no(i.get("Voucher No")) if i.get("Percentage") == "null" else float(i.get("Percentage")) / 100)) for i in rows if i.get("Voucher No") == uv])


# 		if net_total < 0: #Handle only returns. Do not process normal records
# 			returns.append(uv + "\n")
# 			#continue

# 		voucher_no, naming_series, warehouse = process_voucher_no(uv)

# 		rowmsg.append("Voucher No: {0}".format(uv))
# 		print "Voucher No: ", uv, "Processed voucher no: ", voucher_no


# 		if frappe.db.get_value("Sales Invoice", {"name": voucher_no}, "name"):
# 			rowmsg.append("{0} already exists".format(voucher_no))
# 			print voucher_no, " already exists."
# 			continue

# 		voucher_items = [i for i in rows if i.get("Voucher No") == uv]

# 		if not frappe.db.get_value("Customer", {"name": voucher_items[0]["Party Name"]}, "name"):
# 			rowmsg.append("Customer '{0}' not found".format(voucher_items[0]["Party Name"]))
# 			print "Customer ", voucher_items[0]["Party Name"], " not found."
# 			continue

# 		percentage = (float(voucher_items[0]["Percentage"] if voucher_items[0]["Percentage"] != "null" else 0.0))

# 		si = frappe.new_doc("Sales Invoice")
# 		si.naming_series = naming_series
# 		si.posting_date = frappe.utils.getdate(voucher_items[0]["Date"])
# 		si.company = "Bellezimo Professionale Products Pvt. Ltd."
# 		si.customer = voucher_items[0]["Party Name"]
# 		si.currency = "INR"
# 		si.conversion_rate = 1.0
# 		si.selling_price_list = price_list_by_customer_or_net_total(voucher_items[0]["Party Name"], net_total)
# 		si.price_list_currency = "INR"
# 		si.plc_conversion_rate = 1.0
# 		si.base_net_total = net_total
# 		si.base_grand_total = grand_total
# 		si.grand_total = grand_total
# 		si.debit_to = debit_to
# 		si.c_form_applicable = "Yes" if (voucher_items[0].get("Form Name") == "C") else "No"
# 		si.is_return = 1 if (grand_total < 0) else 0
# 		si.due_date = frappe.utils.getdate(voucher_items[0]["Date"])
# 		si.territory = get_corrected_territory(voucher_items[0]["State_1"])
# 		si.taxes_and_charges = stc_template_by_naming_series_tax_percentage(voucher_no, percentage)
# 		si.spn_warehouse = warehouse #frappe.db.get_value("Warehouse", {"state": voucher_items[0]["State"]})

# 		if net_total < 0:
# 			si.is_return = "Yes"
# 			return_against = [r['Original Invoice'] for r in returns_map_dict["data"] if r["Cancelled Invoice"] == uv][0]

# 			if len(return_against) > 0:
# 				si.return_against = process_voucher_no(return_against)[0]

# 		for item in voucher_items:

# 			si.append("items", {
# 				"item_code": item["Stock Item Alias"],
# 				"item_name": item["Item Name"],
# 				"description": item["Item Name"],
# 				"qty": float(item["Quantity"]),
# 				"rate": float(item["Rate"]),
# 				"amount": float(item["Quantity"]) * float(item["Rate"]),
# 				"base_rate": float(item["Rate"]),
# 				"base_amount": float(item["Quantity"]) * float(item["Rate"]),
# 				"income_account": income_ac,
# 				"cost_center": cost_center,
# 				"price_list_rate": frappe.db.get_value("Item Price", {"price_list": si.selling_price_list, "item_name": item["Stock Item Alias"] }, "price_list_rate"),
# 				"warehouse": warehouse
# 			})

# 		si.append("taxes", {
# 			"charge_type": "On Net Total",
# 			"account_head": account_head_by_naming_series(voucher_no),
# 			"description": account_head_by_naming_series(voucher_no),
# 			"cost_center": cost_center,
# 			"rate": percentage,
# 			"tax_amount": net_total * (percentage/100),
# 			"total": grand_total,
# 			"tax_amount_after_discount_amount": grand_total,
# 			"base_tax_amount": net_total * percentage,
# 			"base_total": grand_total,
# 			"base_tax_amount_after_discount_amount": net_total * (percentage/100)
# 		})

# 		try:
# 			si.save()
# 			frappe.db.commit()
# 			print "Saved as", si.name
# 			rowmsg.append("Invoice Saved. ({0})".format(si.name))
# 			rename_doc("Sales Invoice", si.name, voucher_no, force=True)
# 			print "Renamed to", voucher_no
# 			rowmsg.append("Renamed to {0}".format(voucher_no))
# 		except Exception as e:
# 			print "SI '" + voucher_no + "' not saved. {0}".format(e)
# 			rowmsg.append("Invoice '{0}' not saved: {1}".format(voucher_no, e))

# 		processed_recs += 1

# 		msgs.append("\n".join(rowmsg))

# 	print "Total records processed:", processed_recs
# 	msgs.append("Total records processed: {0}".format(processed_recs))

# 	content = "\n".join(msgs)

# 	return content

@frappe.whitelist()
def get_spn_discount(discount=None, total_to_compare=None):
	if discount and total_to_compare:
		for item in frappe.get_all("SPN Monthly Discount Item", fields=["*"], filters ={"parent": discount}):
			if (float(total_to_compare) >= item.slab_from) and (float(total_to_compare) <= item.slab_to):
				return item.discount_pct

@frappe.whitelist()
def get_list(dt):
	doctypes = list(set(frappe.db.sql_list("""select parent
			from `tabDocField` df where fieldname='naming_series' and
			exists(select * from `tabDocPerm` dp, `tabRole` role where dp.role = role.name and dp.parent = df.parent and not role.disabled)""")
		+ frappe.db.sql_list("""select dt from `tabCustom Field`
			where fieldname='naming_series'""")))

	prefixes = ""
	for d in doctypes:
		if d == dt:
			options = ""
			try:
				options = get_options(d)
			except frappe.DoesNotExistError:
				frappe.msgprint('Unable to find DocType {0}'.format(d))
				continue

			if options:
				prefixes = prefixes + "\n" + options

	prefixes.replace("\n\n", "\n")
	prefixes = "\n".join(sorted(prefixes.split()))

	return {
		"prefixes": prefixes
	}

def get_options(arg=None):
	return frappe.get_meta(arg).get_field("naming_series").options

@frappe.whitelist()
def get_stock_entry_list(dt):
	import re
	se_materialreceipt_list = []
	se_materialissue_list = []

	prefixes_dict = get_list(dt)
	prefixes_list = prefixes_dict["prefixes"].split("\n")
	print prefixes_list

	for series in prefixes_list:
		se_series = re.search("([A-Z])([A-Z])(S)(-)",series)
		print "SE Series",se_series

		if se_series == None:
			se_materialreceipt_list.append(series)
			print se_materialreceipt_list
		else:
			se_materialissue_list.append(se_series.string)
			print se_materialissue_list

	return{
		"materialreceipt": "\n".join(sorted(se_materialreceipt_list)),
		"materialissue": "\n".join(sorted(se_materialissue_list))
	}

@frappe.whitelist()
def get_cust_namingseries_pool(dt):
	prefixes_dict = get_list(dt)
	prefixes_list = prefixes_dict["prefixes"].split("\n")
	return prefixes_list

@frappe.whitelist()
def check_if_distributor(dt,customer_territory,customer_group):
	import re
	prefixeslist = []

	check = re.search("(Distributor)",customer_territory) or re.search("(Distributor)",customer_group)
	prefixeslist = get_cust_namingseries_pool(dt)

	if check == None:
		for cust_series in prefixeslist:
			if re.search("(^A)",cust_series):
				return cust_series
	else:
		for cust_series in prefixeslist:
			if re.search("(^S)",cust_series):
				return cust_series

@frappe.whitelist()
def get_user_field_restrictions(doctype):
	restriction_map_list = frappe.get_all("SPN Field Restriction Map Item", filters={"parent":frappe.session.user,"dt":doctype}, fields=["field_restriction_map"])
	if len(restriction_map_list) > 0:
		return restriction_map_list[0].field_restriction_map
	else:
		return []

@frappe.whitelist()
def get_discount_and_freebies(discount_scheme, total_qty, total_amount, items, company):
	dsc = frappe.get_doc("SPN Discount Scheme", discount_scheme)

	if items:
		items = json.loads(items)

	if dsc.quantity_or_amount == "Quantity":
		# for x in xrange(1,10):
		# 	print "quantity", items
		discount_pct = 0.0
		freebies = []

		discount_items = frappe.get_all("SPN Discount Scheme Item",
			filters=[
				["discount_scheme", "=", discount_scheme],
				["to_qty", ">=", total_qty],["from_qty", "<=", total_qty]
			], fields=["*"])

		if len(discount_items) > 0:
			discount_pct = discount_items[0].discount_pct
			freebies = frappe.get_all("SPN Discount Scheme Freebie",
				filters=[
					["against_scheme", "=", discount_scheme],
					["against_scheme_item", "=", discount_items[0].name]
				], fields=["*"])

		return {
			"discount_pct": discount_pct,
			"freebies": freebies,
			"expense_account": frappe.db.get_value("Company", filters={"name": company}, fieldname="default_expense_account"),
			"income_account": frappe.db.get_value("Company", filters={"name": company}, fieldname="default_income_account")
		}

	elif dsc.quantity_or_amount == "Amount":
		for x in xrange(1,10):
			print "amount", company
		discount_pct = 0.0
		freebies = []

		discount_items = frappe.get_all("SPN Discount Scheme Item",
			filters=[
				["discount_scheme", "=", discount_scheme],
				["to_amount",">=",total_amount],["from_amount","<=",total_amount]
			], fields=["*"])

		if len(discount_items) > 0:
			discount_pct = 0.0
			freebies = []

			freebies = frappe.get_all("SPN Discount Scheme Freebie",
				filters=[
					["against_scheme", "=", discount_scheme],
					["against_scheme_item", "=", discount_items[0].name]
				], fields=["*"])

		return {
			"discount_pct": discount_items[0].discount_pct,
			"freebies": freebies,
			"expense_account": frappe.db.get_value("Company", filters={"name": company}, fieldname="default_expense_account"),
			"income_account": frappe.db.get_value("Company", filters={"name": company}, fieldname="default_income_account")
		}

	elif dsc.quantity_or_amount == "Item Quantity":
		# for x in xrange(1,10):
		# 	print "Item Quantity", items
		discount_scheme_items = frappe.get_all("SPN Discount Scheme Item", filters=[["discount_scheme", "=", discount_scheme]], fields=["*"])

		item_wise_discounts = []
		for item in items:
			for discount_scheme_item in [i for i in discount_scheme_items if i["item"] == item.get("item_code") and (i["from_qty"] <= item.get("qty") <= i["to_qty"])]:

				#print "DISCOUNT SCHEME ITEM FOR ", item.get("item_code"), " : ", discount_scheme_item.item

				freebies = []
				for freebie in frappe.get_all("SPN Discount Scheme Freebie", filters={"against_scheme": discount_scheme, "against_scheme_item": discount_scheme_item.name}, fields=["*"]):
					freebies.append(freebie)

				item_wise_discounts.append({
					"item": item.get("item_code"),
					"discount_pct": discount_scheme_item.discount_pct,
					"freebies": freebies,
					"expense_account": frappe.db.get_value("Company", filters={"name": company}, fieldname="default_expense_account"),
					"income_account": frappe.db.get_value("Company", filters={"name": company}, fieldname="default_income_account")
				})

		#return {"discounts": item_wise_discounts, "campaign": dsc.campaign}
		return item_wise_discounts

	else:
		# for x in xrange(1,10):
		# 	print "else", company
		return {
			"discount_pct": 0.0,
			"freebies": []
		}
	# elif dsc.quantity_or_amount == "Item Group Quantity":
	# 	discount_scheme_items = frappe.get_all("SPN Discount Scheme Item", filters=[["discount_scheme", "=", discount_scheme]], fields=["*"])
	# 	item_wise_discounts = []

	# 	item_groups = [i.item_group for i in items if i.item_group not in item_groups]

	# 	for item_group in item_groups:




		# for grupp in item_gruppen:
		# 	for discount_scheme_item in [i for i in discount_scheme_items if i["item"] == item.get("item_code") and (i["from_qty"] <= item.get("qty") <= i["to_qty"])]:
		# 		freebies = []
		# 		for freebie in frappe.get_all("SPN Discount Item Freebies", filters={"discount_scheme": discount_scheme, "against_item": discount_scheme_item.name}, fields=["*"]):
		# 			freebies.append(freebie)

		# 	item_wise_discounts.append({
		# 		"item": item.item_code,
		# 		"discount_pct": discount_scheme_item.discount_pct,
		# 		"freebies": freebies
		# 	})

		#for item in items:
			# for discount_scheme_item in [i for i in discount_scheme_items if i["item"] == item.get("item_code") and (i["from_qty"] <= item.get("qty") <= i["to_qty"])]:
			# 	freebies = []
			# 	for freebie in frappe.get_all("SPN Discount Item Freebies", filters={"discount_scheme": discount_scheme, "against_item": discount_scheme_item.name}, fields=["*"]):
			# 		freebies.append(freebie)

			# item_wise_discounts.append({
			# 	"item": item.item_code,
			# 	"discount_pct": discount_scheme_item.discount_pct,
			# 	"freebies": freebies
			# })


