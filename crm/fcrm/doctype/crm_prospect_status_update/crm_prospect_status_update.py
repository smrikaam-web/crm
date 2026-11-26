# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMProspectStatusUpdate(Document):
	def validate(self):
		if not self.description or len(self.description.strip()) < 15:
			frappe.throw(_("Description must be at least 15 characters long."))

		valid_main = ("Contacted", "Not Contacted", "Not Valid")
		if self.main_status and self.main_status not in valid_main:
			frappe.throw(_("Invalid Main Status. Must be one of: {0}").format(", ".join(valid_main)))

		if self.main_status == "Not Contacted":
			self.activity_status = None
			self.next_action = None
			self.follow_up_date = None
			self.call_back_date = None
			valid_subs = ("Voice mail", "No answer")
			if not self.sub_status:
				frappe.throw(_("Sub Status is required when Main Status is Not Contacted."))
			if self.sub_status not in valid_subs:
				frappe.throw(_("Invalid Sub Status for Not Contacted. Must be one of: {0}").format(", ".join(valid_subs)))
		elif self.main_status == "Not Valid":
			self.activity_status = None
			self.next_action = None
			self.follow_up_date = None
			self.call_back_date = None
			valid_subs = ("Wrong number", "Others")
			if not self.sub_status:
				frappe.throw(_("Sub Status is required when Main Status is Not Valid."))
			if self.sub_status not in valid_subs:
				frappe.throw(_("Invalid Sub Status for Not Valid. Must be one of: {0}").format(", ".join(valid_subs)))
		elif self.main_status == "Contacted":
			self.sub_status = None
