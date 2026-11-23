# Copyright (c) 2026, Smrikaam and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WebsiteBooking(Document):
	def after_insert(self):
		self.update_source_counts()

	def on_trash(self):
		self.update_source_counts()

	def update_source_counts(self):
		if not self.source:
			return
		total = frappe.db.count("Website Booking", {"source": self.source})
		new_count = frappe.db.count("Website Booking", {"source": self.source, "booking_status": "New"})
		frappe.db.set_value(
			"Website Booking Source",
			self.source,
			{
				"total_bookings": total,
				"new_bookings": new_count,
			},
			update_modified=False,
		)
