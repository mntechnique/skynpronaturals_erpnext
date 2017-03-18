// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN User Naming Series Map', {
	onload: function(frm) {

    },
	refresh: function(frm) {
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_list",
			args:{"dt":"Sales Invoice"},
			callback:function(r){
				cur_frm.fields_dict.sales_naming_series_map.grid.get_docfield("naming_series").options = r.message.prefixes;
			}
		});
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_list",
			args:{"dt":"Purchase Receipt"},
			callback:function(r){
				cur_frm.fields_dict.purchase_naming_series_map.grid.get_docfield("naming_series").options = r.message.prefixes;
			}
		});
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_stock_entry_list",
			args:{"dt":"Stock Entry"},
			callback:function(r){
				cur_frm.fields_dict.stockentry_material_receipt_naming_series_map.grid.get_docfield("naming_series").options = r.message.materialreceipt;
			}
		});
		frappe.call({
			method: "skynpronaturals_erpnext.api.get_stock_entry_list",
			args:{"dt":"Stock Entry"},
			callback:function(r){
				cur_frm.fields_dict.stockentry_material_issue_naming_series_map.grid.get_docfield("naming_series").options = r.message.materialissue;
			}
		});
    }
});


// frappe.ui.form.on("SPN User Stock Entry Naming Series Map Item", "map_doctype", function(frm, cdt, cdn){  	
//   	var child = locals[cdt][cdn]; 
// 	frappe.call({
// 		method: "skynpronaturals_erpnext.api.get_stock_entry_list",
// 		args:{"dt":"Stock Entry"},
// 		callback:function(r){
// 			console.log("CHILD", child);
// 			var map = child.map_doctype;
// 			//console.log("CHILD naming_series", cur_frm.fields_dict.stockentry_naming_series_map.grid.get_grid_row(child.name));
// 			if(map == "Stock Entry-Material Receipt"){
// 				cur_frm.fields_dict.stockentry_naming_series_map.grid.get_grid_row(child.name).docfields[1].options =  r.message.materialreceipt;
// 				cur_frm.refresh_fields();
// 				map = null;
// 			}	
// 			else if(map == "Stock Entry-Material Issue")
// 			{
// 				cur_frm.fields_dict.stockentry_naming_series_map.grid.get_grid_row(child.name).docfields[1].options =  r.message.materialissue;
// 				cur_frm.refresh_fields();
// 				console.log("Grid Row Issue", cur_frm.fields_dict.stockentry_naming_series_map.grid.get_grid_row(child.name));
// 				map = null;
// 			}
// 		}
// 	});

// });