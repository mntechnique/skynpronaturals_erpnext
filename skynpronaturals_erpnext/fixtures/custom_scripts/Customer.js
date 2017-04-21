// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer', {
	customer_group: function(frm) {
		distributor_check(frm);
	},
	territory: function(frm) {
		distributor_check(frm);				
	}
});

function distributor_check(frm) {
	if(frm.doc.territory&&frm.doc.customer_group){
		frappe.call({
			method: "skynpronaturals_erpnext.api.check_if_distributor",
			args:{"dt":"Customer","customer_territory":frm.doc.territory,"customer_group":frm.doc.customer_group},
			callback:function(r){
				frm.doc.naming_series = r.message;
			}
		});
	}	
    cur_frm.refresh_fields();
}
