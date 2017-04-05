// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN Discount Scheme Item', {
	refresh: function(frm) {
		var qty_readonly = (cur_frm.doc.from_amount != 0 || cur_frm.doc.to_amount != 0);
		var amt_readonly = (cur_frm.doc.from_qty != 0 || cur_frm.doc.to_qty != 0);

		cur_frm.set_df_property("from_qty", "read_only", qty_readonly);
		cur_frm.set_df_property("to_qty", "read_only", qty_readonly);

		cur_frm.set_df_property("from_amount", "read_only", amt_readonly);
		cur_frm.set_df_property("to_amount", "read_only", amt_readonly);
	},
});
