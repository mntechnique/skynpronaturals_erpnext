import frappe, json

@frappe.whitelist()
def validate_sales_invoice(self, method):

    spn_warehouse = frappe.db.get_value("Sales Invoice","spn_warehouse")
    cust_ter = frappe.db.get_value("Sales Invoice","territory")
    cust_group = frappe.db.get_value("Sales Invoice","customer_group")
    self.naming_series = get_naming_series(spn_warehouse,cust_ter,cust_group)

@frappe.whitelist()
def get_naming_series(spn_warehouse, cust_ter, cust_group):
    if spn_warehouse == "Bellezimo Professionale Products Pvt. Ltd. C/o. Kotecha Clearing & Forwarding Pvt. Ltd.  - SPN":
        if cust_group=="Assam Registered Distributor" and cust_ter == "Assam":
            return "GV-.#####"
        elif cust_group=="Assam Unregistered Distributor":
            return "GU-.#####"
        else:
            return "GC-.#####"
    elif spn_warehouse == "Maharastra":
        if cust_group=="Maharashtra Registered Distributor" and cust_ter == "Mharashtra":
            return "BV-.#####"
        elif cust_group=="Maharashtra Unregistered Distributor":
            return "BU-.#####"
        else:
            return "BC-.#####"



