# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import random
import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.contact import (
	create_prospect_status_update,
	get_prospect_status_history,
	get_contact_activities,
	convert_contact_to_lead,
	update_contact_social_links,
)


class TestCRMProspectStatusUpdate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Create test contact with unique email and valid numeric phone
		uid = frappe.generate_hash()[:8]
		self.email = f"test_prospect_{uid}@example.com"
		self.mobile = f"+1202555{random.randint(1000, 9999)}"
		doc = frappe.new_doc("Contact")
		doc.first_name = "TestProspect"
		doc.last_name = "StatusUpdate"
		doc.add_email(self.email, is_primary=True)
		doc.add_phone(self.mobile, is_primary_mobile_no=True)
		doc.company_name = "Acme Corp"
		doc.insert(ignore_permissions=True)
		self.contact = doc.name

	def tearDown(self):
		if hasattr(self, "contact") and frappe.db.exists("Contact", self.contact):
			frappe.delete_doc("Contact", self.contact, force=True, ignore_permissions=True)
		frappe.db.rollback()

	def test_description_minimum_character_validation(self):
		"""Throws error if description is less than 15 characters."""
		with self.assertRaises(frappe.ValidationError):
			create_prospect_status_update(
				contact=self.contact,
				main_status="Contacted",
				description="Short",
			)

	def test_create_and_fetch_status_update(self):
		"""Can create a prospect status update and fetch it in history."""
		res = create_prospect_status_update(
			contact=self.contact,
			main_status="Contacted",
			activity_status="Portfolio Sent",
			follow_up_date="2026-12-01",
			next_action="Send portfolio",
			description="Sent the revised company presentation and case studies.",
		)
		self.assertTrue(res.get("name"))
		self.assertEqual(res.get("main_status"), "Contacted")
		self.assertEqual(res.get("activity_status"), "Portfolio Sent")

		history = get_prospect_status_history(self.contact)
		self.assertTrue(len(history) >= 1)
		self.assertEqual(history[0]["name"], res["name"])
		self.assertEqual(history[0]["description"], "Sent the revised company presentation and case studies.")

	def test_activities_includes_status_updates(self):
		"""Contact activities timeline contains status updates."""
		res = create_prospect_status_update(
			contact=self.contact,
			main_status="Contacted",
			activity_status="Requirement Gathered",
			follow_up_date="2026-12-05",
			next_action="Book discovery call",
			description="Gathered initial requirements for cloud CRM migration project.",
		)
		activities = get_contact_activities(self.contact)
		self.assertIn("status_updates", activities)
		self.assertTrue(any(item["name"] == res["name"] for item in activities["status_updates"]))
		self.assertTrue(any(item["name"] == res["name"] for item in activities["all_activities"]))

	def test_convert_contact_to_lead(self):
		"""Can convert contact to Lead and prevent duplicate conversion."""
		res = convert_contact_to_lead(self.contact)
		self.assertTrue(res.get("success"))
		self.assertFalse(res.get("already_converted"))
		lead_name = res.get("lead_name")
		self.assertTrue(frappe.db.exists("CRM Lead", lead_name))

		lead_doc = frappe.get_doc("CRM Lead", lead_name)
		self.assertEqual(lead_doc.email, self.email)
		self.assertEqual(lead_doc.mobile_no, self.mobile)

		# Second call should recognize already converted
		res2 = convert_contact_to_lead(self.contact)
		self.assertTrue(res2.get("success"))
		self.assertTrue(res2.get("already_converted"))
		self.assertEqual(res2.get("lead_name"), lead_name)

		# Cleanup created lead
		if frappe.db.exists("CRM Lead", lead_name):
			frappe.delete_doc("CRM Lead", lead_name, force=True, ignore_permissions=True)

	def test_update_contact_social_links(self):
		"""Can update LinkedIn, Upwork, and Website on contact."""
		res = update_contact_social_links(
			self.contact,
			linkedin="https://linkedin.com/in/prospect",
			upwork="https://upwork.com/fl/prospect",
			website="https://prospect.example.com",
		)
		self.assertEqual(res.get("custom_linkedin"), "https://linkedin.com/in/prospect")
		self.assertEqual(res.get("custom_upwork"), "https://upwork.com/fl/prospect")
		self.assertEqual(res.get("custom_website"), "https://prospect.example.com")
