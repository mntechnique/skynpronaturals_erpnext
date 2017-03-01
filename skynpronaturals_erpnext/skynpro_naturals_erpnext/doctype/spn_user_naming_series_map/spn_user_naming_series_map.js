// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN User Naming Series Map', {
	onload: function(frm) {
        // set_query_doctype(frm);
    },
	refresh: function(frm) {
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_list",
			args:{"dt":"Sales Invoice"},
			callback:function(r){
				cur_frm.fields_dict.sales_naming_series_map.grid.get_docfield("naming_series").options = r.message.prefixes;
				refresh_field();
				// set_query_doctype(cur_frm,"Sales Invoice");
			}
		});
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_list",
			args:{"dt":"Purchase Invoice"},
			callback:function(r){
				cur_frm.fields_dict.purchase_naming_series_map.grid.get_docfield("naming_series").options = r.message.prefixes;
				refresh_field();
				// set_query_doctype(cur_frm,"Purchase Invoice");
			}
		});		
    }
});

// function set_query_doctype(frm,map_docname){
//     frm.set_query("map_doctype", "naming_series_map", function() {
//         return {
//         	query: "",
//             filters: [
//                 ["DocType", "name", "in", [map_docname]]
//             ]
//         }
//     });
// }

// list = ["D.RM-PREC-.#####","D.RM-PREC-RET-.#####","SINV-D.RM-.#####"];
// cur_frm.set_df_property("naming_series", "options", list.join("\n"), null, "naming_series_map");
// frappe.utils.filter_dict(cur_frm.fields_dict["fields"].grid.docfields, {"fieldname": "naming_series"})[0].options = "D.RM-PREC-.#####\nD.RM-PREC-RET-.#####\nSINV-D.RM-.#####";