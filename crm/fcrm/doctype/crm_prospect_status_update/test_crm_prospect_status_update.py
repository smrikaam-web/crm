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
		self.assertIsNone(history[0].get("sub_status"))

	def test_not_contacted_with_sub_status(self):
		"""Not Contacted requires Sub Status ('Voice mail' or 'No answer') and persists correctly."""
		# Missing sub_status should fail
		with self.assertRaises(frappe.ValidationError):
			create_prospect_status_update(
				contact=self.contact,
				main_status="Not Contacted",
				description="Attempted call but no response received from prospect.",
			)

		# Invalid sub_status should fail
		with self.assertRaises(frappe.ValidationError):
			create_prospect_status_update(
				contact=self.contact,
				main_status="Not Contacted",
				sub_status="Wrong number",  # wrong category
				description="Attempted call but no response received from prospect.",
			)

		# Valid: Voice mail
		res_vm = create_prospect_status_update(
			contact=self.contact,
			main_status="Not Contacted",
			sub_status="Voice mail",
			description="Attempted call to prospect and left a detailed voicemail message.",
		)
		self.assertEqual(res_vm["main_status"], "Not Contacted")
		self.assertEqual(res_vm["sub_status"], "Voice mail")
		self.assertIsNone(res_vm["activity_status"])

		# Valid: No answer
		res_na = create_prospect_status_update(
			contact=self.contact,
			main_status="Not Contacted",
			sub_status="No answer",
			description="Rang for 45 seconds but received no answer from the prospect.",
		)
		self.assertEqual(res_na["main_status"], "Not Contacted")
		self.assertEqual(res_na["sub_status"], "No answer")

		history = get_prospect_status_history(self.contact)
		self.assertEqual(history[0]["name"], res_na["name"])
		self.assertEqual(history[0]["sub_status"], "No answer")
		self.assertEqual(history[1]["name"], res_vm["name"])
		self.assertEqual(history[1]["sub_status"], "Voice mail")

	def test_not_valid_with_sub_status(self):
		"""Not Valid requires Sub Status ('Wrong number' or 'Others') and persists correctly."""
		# Missing sub_status should fail
		with self.assertRaises(frappe.ValidationError):
			create_prospect_status_update(
				contact=self.contact,
				main_status="Not Valid",
				description="Dialed the number provided on file and it was invalid.",
			)

		# Invalid sub_status should fail
		with self.assertRaises(frappe.ValidationError):
			create_prospect_status_update(
				contact=self.contact,
				main_status="Not Valid",
				sub_status="Voice mail",  # wrong category
				description="Dialed the number provided on file and it was invalid.",
			)

		# Valid: Wrong number
		res_wn = create_prospect_status_update(
			contact=self.contact,
			main_status="Not Valid",
			sub_status="Wrong number",
			description="Person answering indicated this was the wrong number entirely.",
		)
		self.assertEqual(res_wn["main_status"], "Not Valid")
		self.assertEqual(res_wn["sub_status"], "Wrong number")

		# Valid: Others
		res_ot = create_prospect_status_update(
			contact=self.contact,
			main_status="Not Valid",
			sub_status="Others",
			description="Number is disconnected or out of service permanently.",
		)
		self.assertEqual(res_ot["main_status"], "Not Valid")
		self.assertEqual(res_ot["sub_status"], "Others")

		history = get_prospect_status_history(self.contact)
		self.assertEqual(history[0]["name"], res_ot["name"])
		self.assertEqual(history[0]["sub_status"], "Others")
		self.assertEqual(history[1]["name"], res_wn["name"])
		self.assertEqual(history[1]["sub_status"], "Wrong number")

	def test_activities_includes_sub_status(self):
		"""Contact activities timeline contains sub_status in item and title."""
		res = create_prospect_status_update(
			contact=self.contact,
			main_status="Not Contacted",
			sub_status="Voice mail",
			description="Left a voicemail requesting callback regarding initial proposal.",
		)
		activities = get_contact_activities(self.contact)
		found = next((item for item in activities["status_updates"] if item["name"] == res["name"]), None)
		self.assertIsNotNone(found)
		self.assertEqual(found["sub_status"], "Voice mail")
		self.assertIn("Voice mail", found["activity_title"])

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
