//SPN
frappe.ui.form.on("Sales Invoice", {
    "btn_apply_discount_scheme": function(frm) {
        if (!cur_frm.doc.spn_monthly_discount) {
            frappe.msgprint("Please select a discount scheme.");
        } else if (cur_frm.doc.items.length == 0){
            frappe.msgprint("Please add items before applying discount scheme.");
        } else {
            var total_qty = 0.0
            $.each(cur_frm.doc.items, function(k,v) {
                total_qty += v["qty"];
            });

            frappe.call({
                method: "skynpronaturals_erpnext.api.get_discount_and_freebies",
                args: {
                    discount_scheme: cur_frm.doc.spn_monthly_discount,
                    total_qty: total_qty,
                    total_amount: cur_frm.doc.total,
                    items: cur_frm.doc.items.filter(function(item) { return item.amount > 0 }),
                    company: cur_frm.doc.company
                },
                callback: function(r) {
                    var abbr = frappe.get_abbr(cur_frm.doc.company, cur_frm.doc.company.length);
                    console.log("test object", r);
                    //For item-wise freebies
                    if (Array.isArray(r.message)) {
                        console.log("For multiple items...");

                        $.each(r.message, function(idx, dsc_item) {
                            si_item = cur_frm.doc.items.filter(function(f) { return f["item_code"] == dsc_item["item"]; })
                            frappe.model.set_value("Sales Invoice Item", si_item[0].name, "discount_percentage", dsc_item.discount_pct);
                            $.each(dsc_item["freebies"], function(i, freebie) {
                                remove_freebie(freebie);
                                add_freebie(abbr, freebie, r.message[i].income_account, r.message[i].expense_account, dsc_item["item"]);
                            });
                        });
                    } else {
                        console.log("Applying pct");
                        console.log(r);
                        if (r.message && r.message.discount_pct) {
                            cur_frm.set_value("additional_discount_percentage", r.message.discount_pct);
                        }

                        if(r.message && r.message.freebies) {
                            $.each(r.message.freebies, function(i, freebie) {
                                add_freebie(abbr, freebie, r.message.income_account, r.message.expense_account);
                            });
                        }
                    }               
                    cur_frm.refresh_fields();
                }
            });
        }
    },
    "spn_monthly_discount": function(frm) {
        frappe.db.get_value("SPN Discount Scheme", cur_frm.doc.spn_monthly_discount, "item_group", function(r) {
            if (r && r.item_group) {
                console.log("Filtering for:", r.item_group);
                //Get list of item groups with single-quotes.
                var retval = r.item_group.trim().split(",");
                var item_groups = []
                $.each(retval, function(idx, val) {  item_groups.push(val.trim());  });

                cur_frm.set_query("item_code", "items", function(doc, cdt, cdn) {
                    console.log("itemgroups", item_groups);
                    return { filters: [["item_group", "in", item_groups]] }
                });
            } else {
                cur_frm.set_query("item_code", "items", function(doc, cdt, cdn) {
                    console.log("Clearing")
                    return { filters: [] }
                });
            }
        });
    },
    "spn_warehouse": function(frm) {
        if(frm.doc.spn_warehouse && frm.doc.territory && frm.doc.customer_group) {
            items = frm.doc.items;
            for (var i=0; i <= items.length - 1; i++) {
                items[i].warehouse = cur_frm.doc.spn_warehouse;
            }
        }
        

        //Fetch and set letterhead
        frappe.call({
            method: "skynpronaturals_erpnext.api.get_spn_letter_head",
            args: {spn_warehouse: frm.doc.spn_warehouse }, 
            callback: function(r) {
                if (!r.exc) {
                    cur_frm.set_value("letter_head", r.message);
                } else {
                    frappe.msgprint("Check letterhead field in selected Warehouse.")
                }
            }
        });
        
        if (cur_frm.doc.spn_warehouse && cur_frm.doc.territory && cur_frm.doc.customer_group) {
            frappe.call({
                method: "skynpronaturals_erpnext.api.get_naming_series",
                args: { 
                 "spn_warehouse": frm.doc.spn_warehouse,
                 "cust_ter": frm.doc.territory,
                 "cust_group": frm.doc.customer_group
                },
                callback: function(r){
                    if (r) {
                        cur_frm.set_value("naming_series", r.message);
                    }
                }
            });
        }
        
        //Fetch terms by territory and set.
        frappe.call({
            method: "skynpronaturals_erpnext.api.get_terms_by_warehouse_state",
            args: { 
             "spn_warehouse": frm.doc.spn_warehouse
            },
            callback: function(r){
                if (r) {
                    cur_frm.set_value("tc_name", r.message);
                }
            }
        });
    }
});

frappe.ui.form.on("Sales Invoice Item", "item_code", function(frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    d["warehouse"] = cur_frm.doc.spn_warehouse;
});

frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
    //get_spn_discount();
    frappe.call({
        method:"skynpronaturals_erpnext.api.get_user_field_restrictions",
        args:{doctype:cur_frm.doc.doctype},
        callback: function(r){
            if(r.message) {
                //apply_restrictions(cur_frm,r.message)
                console.log("Field restrictions")
            }
        }
    })  
    }
})

function apply_restrictions(frm, le_map){
    le_map = JSON.parse(le_map);   
    map_keys = Object.keys(le_map);

    if (map_keys) {
        for (var i=0; i<map_keys.length; i++) {
            if(cur_frm.fields_dict[map_keys[i]].df.fieldtype == "Table"){
                $.each(le_map[map_keys[i]], function(key, value) {
                    var field_name = Object.keys(value)[0];
                    cur_frm.set_query(field_name, map_keys[i], function() {
                        return {
                            filters: {
                              "name" : value[field_name]
                            }
                        }
                    });
                });
            } else{
                var filter_value = le_map[map_keys[i]];
                cur_frm.set_query(map_keys[i], function() {
                    return {
                        filters: {
                          "name" : filter_value
                        }
                    }
                });                 
            }
        }
    }        
}

function add_freebie(abbr, freebie, income_account, expense_account, against_item_code) {
    var d = frappe.model.add_child(cur_frm.doc, "Sales Invoice Item", "items");
    d.item_code = freebie.freebie_item;
    d.item_name = freebie.freebie_item_name;
    d.description = freebie.freebie_item_name;
    d.warehouse = cur_frm.doc.spn_warehouse;
    d.uom = "Nos";
    d.qty = freebie.freebie_qty;
    d.rate = 0.0;
    d.income_account = income_account;
    d.expense_account = expense_account;
    d.amount = 0.0;
}

frappe.ui.form.on("Sales Invoice Item", {
    items_add: function(doc, cdt, cdn) {
        console.log("tested");
    },
    items_on_form_rendered: function(doc, grid_row) {
        console.log("tested form");
    },


});

function remove_freebie(freebie){
    for(var i = 0; i<cur_frm.doc.items.length;i++){
        console.log("remove", cur_frm.doc.items[i].item_code, freebie.freebie_item);

        if(cur_frm.doc.items[i].item_code == freebie.freebie_item && cur_frm.doc.items[i].amount == 0) {

            /*cur_frm.doc.items[i].splice(freebie_item,)*/
            //cur_frm.doc.items.splice(i, 1);
            /*cur_frm.doc.items.pop();*/
            //delete cur_frm.doc.items[i];
        }
    }
   /* $.each(cur_frm.doc.items, function(index, item){
        if (item.amount == 0){
            //console.log("Removing ", item.item_code, "Freebie", freebie.freebie_item)
            cur_frm.doc.items.splice(index, 1);
            return false;
        }
    });*/
}
