frappe.ui.form.on("Purchase Receipt Item", "item_code", function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	d["warehouse"] = cur_frm.doc.spn_warehouse;
});

frappe.ui.form.on("Purchase Receipt", "spn_warehouse", function(frm) {
    if(frm.doc.spn_warehouse) {
        items = frm.doc.items;
        for (var i=0; i <= items.length - 1; i++) {
            items[i].warehouse = cur_frm.doc.spn_warehouse;
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
    }
});

frappe.ui.form.on("Purchase Receipt", {
	refresh: function(frm) {
		frappe.call({
			method:"skynpronaturals_erpnext.api.get_user_field_restrictions",
			args:{doctype:cur_frm.doc.doctype},
			callback: function(r){
				if (r.message) {
					apply_restrictions(cur_frm,r.message)
				}
			}
		})	
    }
})


function apply_restrictions(frm, le_map){   
    le_map = JSON.parse(le_map);   
    map_keys = Object.keys(le_map);
console.log("MAP", le_map);
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