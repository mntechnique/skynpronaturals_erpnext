# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "skynpronaturals_erpnext"
app_title = "SkynPro Naturals ERPNext"
app_publisher = "MN Technique"
app_description = "ERPNext customization for SkynPro Naturals"
app_icon = "octicon octicon-file-directory"
app_color = "#60b044"
app_email = "support@mntechnique.com"
app_license = "GPL v3"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/skynpronaturals_erpnext/css/skynpronaturals_erpnext.css"
# app_include_js = "/assets/skynpronaturals_erpnext/js/skynpronaturals_erpnext.js"

# include js, css files in header of web template
# web_include_css = "/assets/skynpronaturals_erpnext/css/skynpronaturals_erpnext.css"
# web_include_js = "/assets/skynpronaturals_erpnext/js/skynpronaturals_erpnext.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "skynpronaturals_erpnext.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "skynpronaturals_erpnext.install.before_install"
# after_install = "skynpronaturals_erpnext.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "skynpronaturals_erpnext.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
    "Sales Invoice": {
        "validate": "skynpronaturals_erpnext.api.validate_sales_invoice",
    },
     "Purchase Receipt": {
        "on_submit": "skynpronaturals_erpnext.api.pr_on_submit",
        "on_cancel": "skynpronaturals_erpnext.api.pr_on_cancel",
        "validate": "skynpronaturals_erpnext.api.validate_purchase_receipt",
    },
    "Stock Entry": {
        "on_submit": "skynpronaturals_erpnext.api.stock_entry_on_submit",
        "validate": "skynpronaturals_erpnext.api.validate_stock_entry",
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"skynpronaturals_erpnext.tasks.all"
# 	],
# 	"daily": [
# 		"skynpronaturals_erpnext.tasks.daily"
# 	],
# 	"hourly": [
# 		"skynpronaturals_erpnext.tasks.hourly"
# 	],
# 	"weekly": [
# 		"skynpronaturals_erpnext.tasks.weekly"
# 	]
# 	"monthly": [
# 		"skynpronaturals_erpnext.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "skynpronaturals_erpnext.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "skynpronaturals_erpnext.event.get_events"
# }

fixtures = [{"dt": "Custom Field", "filters":[["name", "in", ['Sales Invoice-spn_warehouse', 'Customer-spn_tin_no',
															'Customer-spn_cst_no', 'Terms and Conditions-spn_territory',
															'Sales Invoice-spn_carrier', 'Sales Invoice-spn_mode_of_transport',
															'Sales Invoice-spn_lr_no', 'Sales Invoice-spn_lr_date',
															'Sales Invoice-spn_no_of_cases', 'Sales Invoice-spn_consignment_weight',
															'Sales Invoice-spn_road_permit_no', 'Sales Invoice-cb_payload_info',
                                                            'Warehouse-spn_letterhead',
                                                            'Sales Invoice-sb_transport_and_payload_information',
                                                            'Purchase Receipt-pr_carrier','Purchase Receipt-pr_mode_of_transport',
                                                            'Purchase Receipt-pr_lr_no','Purchase Receipt-pr_lr_date',
                                                            'Purchase Receipt-pr_no_of_cases','Purchase Receipt-pr_gross_weight',
                                                            'Purchase Receipt-pr_road_permit_no',
                                                            'Purchase Receipt-spn_warehouse',
                                                            'Stock Entry-spn_stock_entry_type','Stock Entry-spn_to_warehouse',
                                                            'Stock Entry Detail-spn_t_warehouse',
                                                            'Stock Entry-st_carrier','Stock Entry-st_mode_of_transport',
                                                            'Stock Entry-st_lr_no','Stock Entry-st_lr_date',
                                                            'Stock Entry-st_no_of_cases','Stock Entry-st_gross_weight',
                                                            'Stock Entry-st_road_permit_no', 'Stock Entry Detail-standard_rate',
                                                            'Stock Entry-transport_and_payload_information',
                                                            'Stock Entry-cb_transport_payload_info_1',
                                                            'Stock Entry-spn_linked_transit_entry',
                                                            'Stock Entry Detail-spn_qty_lost',
                                                            "Purchase Receipt Item-spn_rejected_qty",
                                                            "Purchase Receipt Item-spn_transit_loss_qty",
                                                            "Purchase Receipt-spn_stock_entry",
                                                            "Stock Entry Detail-spn_rejected_qty",
                                                            "Stock Entry Detail-spn_rejected_warehouse",
                                                            "Customer-spn_customer_id","Sales Invoice-spn_monthly_discount", 
                                                            "Sales Order-spn_tp_so_name"]]]},
             {"dt": "Custom Script", "filters":[["name", "in", ['Sales Invoice-client','Purchase Receipt-Client','Stock Entry-Client']]]},
             {"dt": "Property Setter", "filters": [["name", "in",["update_stock", "Sales Invoice Item-rate-read_only"]]]},
             {"dt": "Print Format", "filters": [["name", "in", ["SPN Sales Invoice","Memo Invoice","Goods Receipt Note","Stock Transfer Note"]]]}]

