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

def process_voucher_no(voucher_no):
	naming_series = voucher_no[:-4] + "-.#####"
	processed_voucher_no = voucher_no[:-4] + "-" + voucher_no[-4:].zfill(5) 
	warehouse = ""
	letter_head = ""
	#print "naming series", voucher_no[:-4].lower()
		
	if voucher_no[:-4].lower() in ["bc","bv","bu"]:
		warehouse = "(MAHARASHTRA, Bhiwandi) Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN"
		letter_head = "(Maharashtra) Bellezimo Professionale Products Private Limited"
	elif voucher_no[:-4].lower() in ["gv","gc", "gu"]:
		warehouse = "(ASSAM, Guwahati) Bellezimo Professionale Products Pvt. Ltd. C/o. Siddhi Vinayak Agencies - SPN"
		letter_head = "(Assam) Bellezimo Professionale Products Private Limited"
	elif voucher_no[:-4].lower() in ["wbc","wbv","wbu"]:
		warehouse = "(WEST BENGAL, Kolkata) Bellezimo Professionale Products Pvt. Ltd. C/o. Alloy Associates - SPN"
		letter_head = "(West Bengal) Bellezimo Professionale Products Private Limited"
	else:
		warehouse = ""
		letter_head = ""

	return processed_voucher_no, naming_series, warehouse, letter_head

def percentage_by_voucher_no(voucher_no):
	if "bc" in voucher_no.lower():
		return 2.0
	elif "bv" in voucher_no.lower():
		return 13.5
	elif "gv" in voucher_no.lower():
		return 15.0
	elif "gc" in voucher_no.lower():
		return 2.0
	elif "wbv" in voucher_no.lower():
		return 15.0
	elif "wbc" in voucher_no.lower():
		return 2.0
	else:
		return None

def stc_template_by_naming_series_tax_percentage(voucher_no, tax_pct):
	if "bc" in voucher_no.lower():
		return "Maharashtra CST {0}%".format(tax_pct).replace(".0","")
	elif ("wbv" in voucher_no.lower()) or ("wbu" in voucher_no.lower()):
		return "West Bengal VAT {0}%".format(tax_pct).replace(".0","")
	elif "wbc" in voucher_no.lower():
		return "West Bengal CST {0}%".format(tax_pct).replace(".0","")
	elif ("bv" in voucher_no.lower()) or ("bu" in voucher_no.lower()):
		return "Maharashtra VAT {0}%".format(tax_pct).replace(".0","")
	elif ("gv" in voucher_no.lower()) or ("gu" in voucher_no.lower()):
		return "Assam VAT {0}%".format(tax_pct).replace(".0","")
	elif "gc" in voucher_no.lower():
		return "Assam CST {0}%".format(tax_pct).replace(".0","")
	else:
		return None

def account_head_by_naming_series(voucher_no):
	if "bc" in voucher_no.lower():
		return "Maharashtra CST - SPN"
	elif ("wbv" in voucher_no.lower()) or ("wbu" in voucher_no.lower()):
		return "West Bengal VAT - SPN"
	elif "wbc" in voucher_no.lower():
		return "West Bengal CST - SPN"
	elif ("bv" in voucher_no.lower()) or ("bu" in voucher_no.lower()):
		return "Maharashtra VAT - SPN"
	elif ("gv" in voucher_no.lower()) or ("gu" in voucher_no.lower()):
		return "Assam VAT - SPN"
	elif "gc" in voucher_no.lower():
		return "Assam CST - SPN"
	else:
		return None	

def price_list_by_customer_or_net_total(customer, net_total):

	cg = frappe.db.get_value("Customer", {"name": customer}, "customer_group")

	print "Customer Group", cg, " : Cust: '", customer, "'"

	if net_total <= 5.0: ##Less than two means memo invoice.
		return "MEMO/ZERO INVOICING"

	if ("maharashtra" in cg.lower()) or ("maharastra" in cg.lower()):
		return "Maharashtra"
	elif "west bengal" in cg.lower():
		return "West Bengal (VAT)"
	elif "assam" in cg.lower():
		return "Assam"
	elif "gujarat" in cg.lower():
		if "registered" in cg.lower():
			return "Gujarat Registered Distributor"
		elif "unregistered" in cg.lower():
			return "Gujarat Unregistered Distributor"
	else:
		return cg

def get_corrected_territory(territory):
	if "maha" in territory.lower():
		return "Maharashtra"
	elif "delhi" in territory.lower():
		return "Delhi"
	else:
		return territory

@frappe.whitelist()
def process_sheet_and_create_si(path_to_sheet, path_to_returns_map, debit_to="Debtors - SPN", income_ac="Sales - SPN", cost_center="Main - SPN"):
	from frappe.model.rename_doc import rename_doc

	msgs, out = [], []
	
	final_json = csv_to_json(path=path_to_sheet)
	rows = final_json["data"]
	
	#Get returns map dict
	returns_map_dict = csv_to_json(path_to_returns_map, 0, 1)

	unique_vouchers = list(set([v.get("Voucher No") for v in rows]))

	processed_recs = 0

	msgs.append("Vouchers to process: {0}".format(len(unique_vouchers)))

	print "Vouchers to process: {0}".format(len(unique_vouchers))

	for uv in unique_vouchers:
		rowmsg = []
		voucher_no, naming_series, warehouse, letter_head = process_voucher_no(uv)

		rowmsg.append("Processing voucher: {0}".format(uv))

		net_total = sum([float(i.get("Quantity")) * float(i.get("Rate")) for i in rows if i.get("Voucher No") == uv])
		grand_total = sum([
					(float(i.get("Quantity")) * float(i.get("Rate"))) + 
					((float(i.get("Quantity")) * float(i.get("Rate"))) * (percentage_by_voucher_no(i.get("Voucher No")) if i.get("Percentage") == "null" else float(i.get("Percentage")) / 100)) for i in rows if i.get("Voucher No") == uv])

		#Skip if already exists
		if frappe.db.get_value("Sales Invoice", {"name": voucher_no}, "name"):
			rowmsg.append("Voucher {0} already exists".format(voucher_no))
			print voucher_no, " already exists."
			continue

		#Append
		if net_total < 0:
		 	rowmsg.append("Return Invoice. (Net: {1}, Grand: {2})".format(uv, net_total, grand_total))

		voucher_items = [i for i in rows if i.get("Voucher No") == uv]
		percentage = (float(voucher_items[0]["Percentage"] if voucher_items[0]["Percentage"] != "null" else 0.0))
	
	 	rowmsg.append(make_si(uv, voucher_no, voucher_items, naming_series, warehouse, letter_head, net_total, grand_total, percentage, returns_map_dict, debit_to, income_ac, cost_center))

	 	processed_recs += 1
	 	msgs.append("\n".join(rowmsg))

	 	print "\n".join(rowmsg), " Rec# ", processed_recs

	 	if processed_recs == 100:
	 		break

 	msgs.append("Processed vouchers: {0}".format(processed_recs))
	print "Processed vouchers: {0}".format(processed_recs)

	return "\n".join(msgs)

def make_si(tally_voucher_no, voucher_no, voucher_items, naming_series, warehouse, letter_head, net_total, grand_total, percentage, returns_map_dict, debit_to, income_ac, cost_center):
	rowmsg = []

	posting_date = frappe.utils.datetime.datetime.strptime(voucher_items[0]["Date"], "%d-%m-%Y")

	si = frappe.new_doc("Sales Invoice")
	si.naming_series = naming_series
	si.posting_date = posting_date #frappe.utils.datetime.datetime.strptime(voucher_items[0]["Date"], "%d-%m-%Y")#.date() #frappe.utils.getdate(voucher_items[0]["Date"])
	si.company = "Bellezimo Professionale Products Pvt. Ltd."
	si.customer = voucher_items[0]["Party Name"]
	si.currency = "INR"
	si.conversion_rate = 1.0
	si.selling_price_list = price_list_by_customer_or_net_total(voucher_items[0]["Party Name"], net_total)
	si.price_list_currency = "INR"
	si.plc_conversion_rate = 1.0
	si.base_net_total = net_total
	si.base_grand_total = grand_total
	si.grand_total = grand_total
	si.debit_to = debit_to
	si.c_form_applicable = "Yes" if (voucher_items[0].get("Form Name") == "C") else "No"
	si.is_return = 1 if (grand_total < 0) else 0
	si.due_date = si.posting_date #frappe.utils.datetime.datetime.strptime(voucher_items[0]["Date"], "%d-%m-%Y").date() #frappe.utils.getdate(voucher_items[0]["Date"])
	si.territory = get_corrected_territory(voucher_items[0]["State_1"])
	si.taxes_and_charges = stc_template_by_naming_series_tax_percentage(voucher_no, percentage)
	si.spn_warehouse = warehouse
	si.letter_head = letter_head
	
	if net_total < 0:
		si.is_return = "Yes"
		return_against = [r['Original Invoice'] for r in returns_map_dict["data"] if r["Cancelled Invoice"] == tally_voucher_no]

		if len(return_against) > 0:
			processed_voucher_no = process_voucher_no(return_against[0])[0]
			rowmsg.append("Return against: {0}".format(processed_voucher_no))
			si.return_against = processed_voucher_no

	rowmsg.append("Original Date: {0}, SI Date {1}".format(voucher_items[0]["Date"], si.posting_date))

	for item in voucher_items:

		si.append("items", {
			"item_code": item["Stock Item Alias"],
			"item_name": item["Item Name"],
			"description": item["Item Name"],
			"qty": float(item["Quantity"]),
			"rate": float(item["Rate"]),
			"amount": float(item["Quantity"]) * float(item["Rate"]),
			"base_rate": float(item["Rate"]),
			"base_amount": float(item["Quantity"]) * float(item["Rate"]),
			"income_account": income_ac,
			"cost_center": cost_center,
			"price_list_rate": frappe.db.get_value("Item Price", {"price_list": si.selling_price_list, "item_name": item["Stock Item Alias"] }, "price_list_rate"),
			"warehouse": warehouse,
		})

	si.append("taxes", {
		"charge_type": "On Net Total",
		"account_head": account_head_by_naming_series(voucher_no),
		"description": frappe.db.get_value("Sales Taxes and Charges", {"account_head": account_head_by_naming_series(voucher_no), "parent": stc_template_by_naming_series_tax_percentage(voucher_no, percentage)}, "description"),
		"cost_center": cost_center,
		"rate": percentage,
		"tax_amount": net_total * (percentage/100),
		"total": grand_total,
		"tax_amount_after_discount_amount": grand_total,
		"base_tax_amount": net_total * percentage,
		"base_total": grand_total,
		"base_tax_amount_after_discount_amount": net_total * (percentage/100)	
	})

	try:
		si.save()
		frappe.db.commit()
		#'"Invoice Saved. ({0})".format(si.name))
		rowmsg.append("Invoice Saved. ({0})".format(si.name))
		rename_doc("Sales Invoice", si.name, voucher_no, force=True)
		rowmsg.append("Renamed to {0}".format(voucher_no))
	except Exception as e:
		rowmsg.append("not saved: {1}".format(voucher_no, e))

	return "\n".join(rowmsg)
