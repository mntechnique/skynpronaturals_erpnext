// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt

frappe.ui.form.on('SPN Discount Scheme Item', {
	refresh: function(frm) {

	},
	//quick_entry: function(frm) {
	//	console.log("QUICKENTRY", "BLAHBLAH");
		// var naming_series_options = frm.fields_dict.naming_series.df.options;
		// var naming_series_default = frm.fields_dict.naming_series.df.default || naming_series_options.split("\n")[0];

		// var dialog = new frappe.ui.Dialog({
		// 	title: __("Quick Journal Entry"),
		// 	fields: [
		// 		{fieldtype: "Currency", fieldname: "debit", label: __("Amount"), reqd: 1},
		// 		{fieldtype: "Link", fieldname: "debit_account", label: __("Debit Account"), reqd: 1,
		// 			options: "Account",
		// 			get_query: function() {
		// 				return erpnext.journal_entry.account_query(frm);
		// 			}
		// 		},
		// 		{fieldtype: "Link", fieldname: "credit_account", label: __("Credit Account"), reqd: 1,
		// 			options: "Account",
		// 			get_query: function() {
		// 				return erpnext.journal_entry.account_query(frm);
		// 			}
		// 		},
		// 		{fieldtype: "Date", fieldname: "posting_date", label: __("Date"), reqd: 1,
		// 			default: frm.doc.posting_date},
		// 		{fieldtype: "Small Text", fieldname: "user_remark", label: __("User Remark"), reqd: 1},
		// 		{fieldtype: "Select", fieldname: "naming_series", label: __("Series"), reqd: 1,
		// 			options: naming_series_options, default: naming_series_default},
		// 	]
		// });

		// dialog.set_primary_action(__("Save"), function() {
		// 	var btn = this;
		// 	var values = dialog.get_values();

		// 	frm.set_value("posting_date", values.posting_date);
		// 	frm.set_value("user_remark", values.user_remark);
		// 	frm.set_value("naming_series", values.naming_series);

		// 	// clear table is used because there might've been an error while adding child
		// 	// and cleanup didn't happen
		// 	frm.clear_table("accounts");

		// 	// using grid.add_new_row() to add a row in UI as well as locals
		// 	// this is required because triggers try to refresh the grid

		// 	var debit_row = frm.fields_dict.accounts.grid.add_new_row();
		// 	frappe.model.set_value(debit_row.doctype, debit_row.name, "account", values.debit_account);
		// 	frappe.model.set_value(debit_row.doctype, debit_row.name, "debit_in_account_currency", values.debit);

		// 	var credit_row = frm.fields_dict.accounts.grid.add_new_row();
		// 	frappe.model.set_value(credit_row.doctype, credit_row.name, "account", values.credit_account);
		// 	frappe.model.set_value(credit_row.doctype, credit_row.name, "credit_in_account_currency", values.debit);

		// 	frm.save();

		// 	dialog.hide();
		// });

		// dialog.show();
//	}
});
