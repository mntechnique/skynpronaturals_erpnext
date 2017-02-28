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

from skynpronaturals_erpnext.si_import import csv_to_json

# @frappe.whitelist()
# def prepsheet_stock_entry(path_to_sheet):
# 	import csv

# 	rows = process_stock_entries()
# 	column_headings_row = ["name", "naming_series", "purpose", "company", "posting_date", "posting_time", "~", "item_code", "description", "qty", "uom", "conversion_factor", "stock_uom", "transfer_qty", "s_warehouse", "t_warehouse", "~"]

# 	with open('/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_stockentry_out.csv', 'w') as csvfile:
# 		fieldnames = column_headings_row
# 		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

# 		writer.writeheader()
# 		for row in rows:
# 			writer.writerow(row)

@frappe.whitelist()
def process_stock_entries(path_to_sheet):

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

	final_json = csv_to_json(path_to_sheet) #'/home/gaurav/gaurav-work/skynpro/Tally2ERPNext/skynpro_tally_stockentry.csv'
	rows = final_json["data"]

	unique_stnnos = list(set([v.get("Voucher No") for v in rows]))

	out = []

	processed_recs = 0

	print "Unique recs", len(unique_stnnos)

	# for stn_no in unique_stnnos:
	# 	print "STNNo", stn_no
	# 	stn_items = [x for x in rows if x["Voucher No"] == stn_no]
	# 	print "---"
	# 	print stn_items
	# 	print "---"


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
			"posting_date": frappe.utils.getdate(stn_items[0]["Date"]),
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
