// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN User Naming Series Map', {
	onload: function(frm) {
        set_query_doctype(frm);
    },
	refresh: function(frm) {
		// frm.set_df_property("naming_series", "options", "a\nb\nc", null, "naming_series_map")	
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_list",
			args:{"dt":"Sales Invoice"},
			callback:function(r){
				cur_frm.fields_dict.naming_series_map.grid.get_docfield("naming_series").options = r.message.prefixes;
				refresh_fields();
			}
		});		
		set_query_doctype(frm);
    }
});

function set_query_doctype(frm){
    frm.set_query("map_doctype", "naming_series_map", function() {
        return {
        	query: "",
            filters: [
                ["DocType", "name", "in", ["Sales Invoice","Purchase Receipt"]]
            ]
        }
    });
}

// list = ["D.RM-PREC-.#####","D.RM-PREC-RET-.#####","SINV-D.RM-.#####"];
// cur_frm.set_df_property("naming_series", "options", list.join("\n"), null, "naming_series_map");
// frappe.utils.filter_dict(cur_frm.fields_dict["fields"].grid.docfields, {"fieldname": "naming_series"})[0].options = "D.RM-PREC-.#####\nD.RM-PREC-RET-.#####\nSINV-D.RM-.#####";