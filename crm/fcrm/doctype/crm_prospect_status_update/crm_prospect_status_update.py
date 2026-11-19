# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMProspectStatusUpdate(Document):
	def validate(self):
		if not self.description or len(self.description.strip()) < 15:
			frappe.throw(_("Description must be at least 15 characters long."))
