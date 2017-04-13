from frappe import _

def get_data():
	return [
		{
			"label": _("Settings"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "SPN Settings",
					"label": "SPN Settings",
					"description": _("Global Settings for SPN")
				},
				{
					"type": "doctype",
					"name": "SPN Field Restriction Map",
					"label": "Field Restriction Map",
					"description": _("Field Restriction Map"),
				},
				{
					"type": "doctype",
					"name": "SPN User Naming Series Map",
					"label": "User Naming Series Map",
					"description": _("List of Machine Families"),
				},
			]
		},
		{
			"label": _("Masters"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "SPN Discount Scheme",
					"label": "Discount Schemes",
					"description": _("List of Discount Schemes"),
				},
				{
					"type": "doctype",
					"name": "SPN Discount Scheme Item",
					"label": "Discount Scheme Items",
					"description": _("List of Discount Scheme Items"),
				},
				{
					"type": "doctype",
					"name": "SPN Discount Scheme Freebie",
					"label": "Freebies",
					"description": _("List of Freebies against discount scheme items."),
				},
				{
					"type": "doctype",
					"name": "Campaign",
					"label": "Campaign",
					"description": _("List of Campaigns"),
				},
				{
					"type": "doctype",
					"name": "Pricing Rule",
					"label": "Pricing Rule",
					"description": _("List of Pricing Rules"),
				}
			]
		}
	]