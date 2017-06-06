//SPNSE

frappe.ui.form.on("Stock Entry", "onload", function(frm) {
	frm.set_df_property("spn_to_warehouse", "hidden", 1);

	//Haack!
	//$('.form-in-grid').find('[data-fieldname="item_code"]').on("click", function(){ console.log("POPO") })
});


frappe.ui.form.on("Stock Entry Detail", "qty", function(doc,cdt,cdn) {
	var row = locals[cdt][cdn];
	frappe.db.get_value("Item Price", {"item_code":row.item_code,"price_list":"Standard Buying"}, "price_list_rate", function(r) {
		if (r && r["price_list_rate"]) {
			frappe.model.set_value(row.doctype, row.name, "spn_buying_rate", r["price_list_rate"]);
			frappe.model.set_value(row.doctype, row.name, "spn_buying_amt", r["price_list_rate"] * row["qty"]);
	   	}
   	});
});

frappe.ui.form.on("Stock Entry", "refresh", function(frm) {
	//var condition = (((frm.doc.docstatus == 0)  || frm.doc.__islocal) || frm.doc.spn_linked);
	var condition = (!frm.doc.spn_linked_transit_entry) 
		&& (frm.doc.spn_stock_entry_type == "Skynpro") 
		&& (frm.doc.purpose =="Material Transfer") 
		&& ((frm.doc.docstatus == 0) || (frm.doc.__islocal));

	if (condition) {
		frm.add_custom_button(__("Set Details from Transit Entry"), function() {
		   var p = frappe.prompt([
				{
					'fieldname': 'stock_entry', 
					'fieldtype': 'Link', 
					'options': 'Stock Entry',
					'label': 'Stock Entry',
					'get_query': function() {
						return {
							filters: {"spn_linked_transit_entry":"", "docstatus":"1"}
						}
					}
				}
			],
			function(value){
				console.log(value);
				set_details_from_transit_entry(frm, value["stock_entry"]);
			},
			'Select Transit Entry',
			'Select'
			)
		});
	}
	set_transit_warehouse_filter(frm);
    
    frappe.call({
        method:"skynpronaturals_erpnext.api.get_user_field_restrictions",
        args:{ doctype : cur_frm.doc.doctype },
        callback: function(r){
        	console.log("Restrictions", r);
        	if (r.message) {
            	apply_restrictions(cur_frm,r.message)
        	}
        }
    });
    
});


frappe.ui.form.on("Stock Entry", "spn_to_warehouse", function(frm) {
	if(frm.doc.spn_to_warehouse) {
		items = frm.doc.items;
		for (var i=0; i <= items.length - 1; i++) {
			items[i].spn_t_warehouse = cur_frm.doc.spn_to_warehouse;
		}
	}
});

frappe.ui.form.on("Stock Entry Detail", "items_add", function(doc, cdt, cdn) {
	console.log("SPN T WAREHOUSE");
	if(cur_frm.doc.spn_to_warehouse) {
		console.log("Setting SPN TO WAREHOUSE");
		frappe.model.set_value(cdt, cdn, "spn_t_warehouse", cur_frm.doc.spn_to_warehouse);
		cur_frm.refresh_field("items");
	}
});

frappe.ui.form.on("Stock Entry", "from_warehouse", function(frm) {
	if(frm.doc.from_warehouse) {
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_spn_letter_head",
			args: {spn_warehouse: cur_frm.doc.from_warehouse }, 
			callback: function(r) {
				if (!r.exc) {
					cur_frm.set_value("letter_head", r.message);
				} else {
					frappe.msgprint("Check letterhead field in selected Warehouse.")
				}
			}
		});
	}
});

frappe.ui.form.on("Stock Entry", "purpose", function(frm) {
	set_destination_warehouse(frm);
	if (cur_frm.doc.purpose == "Material Transfer") {
		cur_frm.set_value("spn_stock_entry_type", "Skynpro");
	} else {
		cur_frm.set_value("spn_stock_entry_type", "Default");
	}
	cur_frm.refresh();
});

frappe.ui.form.on("Stock Entry", "spn_stock_entry_type", function(frm) {
	set_destination_warehouse(frm);
});

frappe.ui.form.on("Stock Entry Detail", "spn_qty_lost", function(frm, cdt, cdn) {
	recalculate_item_qty(frm,cdt,cdn);
});
frappe.ui.form.on("Stock Entry Detail", "spn_rejected_qty", function(frm, cdt, cdn) {
	recalculate_item_qty(frm,cdt,cdn);
});

//Helpers
function set_destination_warehouse(frm){
	if (frm.doc.purpose == "Material Transfer") {
		if (frm.doc.spn_stock_entry_type == "Skynpro") {
			frm.set_df_property("spn_to_warehouse", "hidden", 0);
			frappe.model.get_value("SPN Settings", "SPN Settings", "spn_transit_warehouse", function(r){                         
				cur_frm.set_value("to_warehouse", r.spn_transit_warehouse);
			});
		} else {
			frm.set_df_property("spn_to_warehouse", "hidden", 1);
			cur_frm.set_value("to_warehouse", "");
		}
	} else {
		frm.set_df_property("spn_to_warehouse", "hidden", 1);
		cur_frm.set_value("to_warehouse", "");
	}
}

//Details from transit entry
function set_details_from_transit_entry(frm, transit_entry_name) {
	items = [];
	frappe.call({
		method: "skynpronaturals_erpnext.api.get_details_from_transit_entry",
		args: { 
			"transit_entry_name" : transit_entry_name 
		},
		callback: function(r) {
			console.log("Details fetched", r);
			//Set Type
			//cur_frm.set_value("purpose", "Material Transfer");
			cur_frm.set_value("spn_stock_entry_type", "Default");

			//Set Items
			cur_frm.set_value("items", []); //Clear existing items first (blank row/items from prev fetch).
			for (i=0;i<=r.message.items.length-1; i++) {
				row = frappe.model.add_child(cur_frm.doc, "Stock Entry Detail", "items");
				row.item_code = r.message.items[i].item_code;
				row.item_name = r.message.items[i].item_name;
				row.qty = r.message.items[i].qty;
				row.transfer_qty = r.message.items[i].transfer_qty;
				row.uom = r.message.items[i].uom;
				row.basic_rate = r.message.items[i].basic_rate;
				row.basic_amount = r.message.items[i].basic_amount;
				row.additional_cost = r.message.items[i].additional_cost;
				row.valuation_rate = r.message.items[i].valuation_rate;
				row.amount = r.message.items[i].amount;
				row.conversion_factor = r.message.items[i].conversion_factor;
				row.expense_account = r.message.items[i].expense_account;
				row.cost_center = r.message.items[i].cost_center;
				row.spn_buying_rate = r.message.items[i].spn_buying_rate;
				refresh_field("items");
			}

			//Set Default warehouses here. Cause cascade in items.
			frappe.model.get_value("SPN Settings", "SPN Settings", "spn_transit_warehouse", function(rval){                      
				cur_frm.set_value("from_warehouse", rval.spn_transit_warehouse);
			});
			
			cur_frm.set_value("to_warehouse", r.message.destination_warehouse);
			
			//Link selected SE to current SE.
			cur_frm.set_value("spn_linked_transit_entry", transit_entry_name);

			refresh_field("items");
		}
	});
}

function create_transit_loss_stock_entry_on_submit(frm) {
	var items_with_transit_loss = frm.doc.items.filter(function(i) { i.spn_loss_qty > 0.0 });
	if (items_with_transit_loss.length > 0) {
		//Create transit entry with stock loss
		frappe.call({
			method: "refreshednow_erpnext.api.create_transit_loss_stock_entry",
			args: { "created_against" : frm.doc.name },
			callback: function(r) {
				if (!r.exc) {
					show_alert("Transit loss entry created (" + r.message + ")");
				}
			}
		})
	}
}

function recalculate_item_qty(frm,cdt,cdn) {
	var d = locals[cdt][cdn];
	frappe.db.get_value("Stock Entry Detail", 
		filters={"parent": cur_frm.doc.spn_linked_transit_entry, "item_code": d["item_code"]}, 
		fieldname="qty",
		function(r) {
			d["qty"] = r.qty - ( (d["spn_rejected_qty"] || 0.0) + (d["spn_qty_lost"] || 0.0));
			refresh_field("items"); 
	});
}


function set_transit_warehouse_filter(frm) {
	//Transit warehouse
	frappe.model.get_value("SPN Settings", "SPN Settings", "spn_transit_warehouse", function(r){
		var r = r; 
		frm.set_query("to_warehouse", function() {
			if(cur_frm.doc.purpose="Material Transfer" && cur_frm.doc.spn_stock_entry_type == "Skynpro") {
				return {
					query: "skynpronaturals_erpnext.api.se_get_allowed_warehouses",
					filters: {"name": r.spn_transit_warehouse}
				}
			} else {
				return {
					query: "skynpronaturals_erpnext.api.se_get_allowed_warehouses"
				}
			}
		});
	});
}

function apply_restrictions(frm, le_map){    
    le_map = JSON.parse(le_map);   
    map_keys = Object.keys(le_map);
    console.log("LE Map", le_map);

    if (map_keys) {
        for (var i=0; i<map_keys.length; i++) {
            if(cur_frm.fields_dict[map_keys[i]].df.fieldtype == "Table"){
                $.each(le_map[map_keys[i]], function(key, value) {
                	console.log("lemap mapkeys i:", le_map[map_keys[i]]);
                    var field_name = Object.keys(value)[0];
      				console.log("Field: ", field_name, " Value: ", value);
                    cur_frm.set_query(field_name, map_keys[i], function() {
						console.log("Table field", value[field_name]);
                        return {
                            filters: {
                              "name" : value[field_name]
                            }
                        }
                    });
                });
            } else if (cur_frm.fields_dict[map_keys[i]].df.fieldtype == "Select") {
                cur_frm.fields_dict[map_keys[i]].df.options = le_map[map_keys[i]].join("\n");
                refresh_field(map_keys[i]);
            } else {
                var filter_value = le_map[map_keys[i]];
                cur_frm.set_query(map_keys[i], function() {
                	console.log("Normal field", filter_value);
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
