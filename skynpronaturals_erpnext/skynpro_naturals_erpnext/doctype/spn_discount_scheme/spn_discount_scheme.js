// Copyright (c) 2016, MN Technique and contributors
// For license information, please see license.txt
frappe.provide("erpnext.utils");

frappe.discount_scheme = {};

frappe.ui.form.on('SPN Discount Scheme', {
	onload: function(frm) {
		make_discount_item_dialog(frm);
		render_discount_items();
	}
});

function make_discount_item_dialog(frm) {
	frappe.discount_scheme["discount_item_dialog"] = new frappe.ui.Dialog({
		title: __("Quick Discount Item Entry"),
		fields: [
			{fieldtype: "Currency", fieldname: "from_amount", label: __("From Amount")},
			{fieldtype: "Currency", fieldname: "to_amount", label: __("To Amount")},
			{fieldtype: "Float", fieldname: "from_qty", label: __("From Quantity")},
			{fieldtype: "Float", fieldname: "to_qty", label: __("To Quantity")},
			{fieldtype: "Percent", fieldname: "discount_pct", label: __("Discount Percent")},
			{fieldtype: "Currency", fieldname: "coupon_amount", label: __("Coupon Amount")}
		]
	});
	var dialog = frappe.discount_scheme["discount_item_dialog"];
	dialog.set_primary_action(__("Save"), function() {
		var btn = this;
		var values = dialog.get_values();
		frappe.call({
			doc: cur_frm.doc,
			method: "add_discount_item",
			args: {
				"values": values
			},
			callback: function(r) {
				console.log("Values", r.message);
				dialog.clear(); dialog.hide();
				render_discount_items();
			}
		})
	});
}

function make_freebie_dialog(frm, discount_item) {
	if (!frappe.discount_scheme["freebie_dialog"]) {
		var discount_item_local = discount_item;
		frappe.discount_scheme["freebie_dialog"] = new frappe.ui.Dialog({
			title: __("Quick Freebie Entry"),
			fields: [
				{fieldtype: "Link", fieldname: "freebie_item", label: __("Freebie Item"), options: "Item"},
				{fieldtype: "Float", fieldname: "freebie_qty", label: __("Freebie Quantity")}
			]
		});
		var dialog = frappe.discount_scheme["freebie_dialog"];
		dialog.set_primary_action(__("Save"), function() {
			var btn = this;
			var values = dialog.get_values();
			frappe.call({
				doc: cur_frm.doc,
				method: "add_freebie",
				args: {
					"values": values,
					"discount_item": discount_item_local
				},
				callback: function(r) {
					dialog.clear(); dialog.hide();
					render_discount_items();
				}
			})
		});
	}
}

function render_discount_items() {
	frappe.call({
		method: "get_discount_scheme_items",
		doc: cur_frm.doc,
		callback: function(r) {
			var wrapper = $(cur_frm.fields_dict['scheme_details'].wrapper);
			
			wrapper.html(frappe.render_template("discount_scheme_details", r.message))
			wrapper.find(".add-discount-item").on("click", function() {
				frappe.discount_scheme["discount_item_dialog"].show();
			})
			wrapper.find(".add-freebie").on("click", function() {
				make_freebie_dialog(cur_frm, $(this).attr('data-discount-item'));
				frappe.discount_scheme["freebie_dialog"].show();
			});
		}
	})
}