// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN Tally Data Import Tool', {
	refresh: function(frm) {

	},
	btn_import: function(frm) {
		frappe.call({
			method: "skynpronaturals_erpnext.si_import.process_sheet_and_create_si",
			args: { 
				path_to_sheet: frm.doc.attach_sheet,
				path_to_returns_map: frm.doc.returns_map_sheet
			},
			freeze: true,
			freeze_message: "Importing...",
			callback: function(r) {
				if(r) {
					console.log(r.message);
					cur_frm.set_value("import_log", r.message);
				}
			}
		})
	}
});
