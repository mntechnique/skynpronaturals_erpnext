import frappe, json

@frappe.whitelist()
def validate_sales_invoice(self, method):

    spn_warehouse = frappe.db.get_value("Sales Invoice","spn_warehouse")
    cust_ter = frappe.db.get_value("Sales Invoice","territory")
    cust_group = frappe.db.get_value("Sales Invoice","customer_group")

    if not self.naming_series:
        self.naming_series = get_naming_series(spn_warehouse,cust_ter,cust_group)

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
    # tle = frappe.new_doc("Stock Entry")

    # orig_entry = frappe.get_doc("Stock Entry", transit_entry_name)

    # tle.purpose = "Material Transfer"
    # tle.posting_date = orig_entry.posting_date
    # tle.posting_time = orig_entry.posting_time

    
    
       

