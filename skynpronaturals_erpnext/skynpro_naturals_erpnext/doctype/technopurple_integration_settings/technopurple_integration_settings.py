# -*- coding: utf-8 -*-
# Copyright (c) 2015, MN Technique and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TechnoPurpleIntegrationSettings(Document):
	def on_update(self):
		pass# frappe.add_version(self)