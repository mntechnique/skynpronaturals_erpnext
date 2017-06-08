frappe.ui.form.on("Purchase Invoice", {
	onload: function(frm) {
		frappe.call({
			method:"skynpronaturals_erpnext.api.get_user_field_restrictions",
			args:{doctype:cur_frm.doc.doctype},
			callback: function(r){
				if (r.message && r.message.length > 0) {
					apply_restrictions(cur_frm,r.message)
				}
			}
		})	
    }
});