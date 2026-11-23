# Copyright (c) 2026, Smrikaam and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Seed default website booking sources and indexes for Booking Hub."""
	# Add performance indexes
	for col in ["source", "booking_status", "appointment_date", "email"]:
		try:
			frappe.db.add_index("Website Booking", [col])
		except Exception:
			pass

	# Seed default sources
	default_sources = [
		{
			"source_id": "src_smrikaam",
			"source_name": "Smrikaam",
			"domain": "smrikaam.com",
			"website_type": "Corporate",
			"description": "Smrikaam Corporate Website",
			"connection_status": "Connected",
			"is_active": 1,
		},
		{
			"source_id": "src_bitxhift",
			"source_name": "BitXhift",
			"domain": "bitxhift.com",
			"website_type": "Product",
			"description": "BitXhift Product Website",
			"connection_status": "Connected",
			"is_active": 1,
		},
	]

	for src in default_sources:
		if not frappe.db.exists("Website Booking Source", src["source_id"]):
			doc = frappe.new_doc("Website Booking Source")
			doc.update(src)
			doc.generate_credentials()
			doc.insert(ignore_permissions=True)
		else:
			existing = frappe.get_doc("Website Booking Source", src["source_id"])
			if not existing.api_secret_hash:
				existing.generate_credentials()
				existing.save(ignore_permissions=True)

	frappe.db.commit()
