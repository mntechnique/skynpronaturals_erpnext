// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN User Naming Series Map', {
	refresh: function(frm) {
        cur_frm.set_query("doctype", "naming_series_map", function() {
            return {
            	query: "",
                filters: [
                    ["DocType", "name", "in", ["Sales Invoice","Purchase Receipt"]]
                ]
            }
        });
    }
});
