import frappe
from frappe.core.doctype.communication.communication import get_contacts

from crm.tests import CRMTestCase
from crm.utils import is_bounce_email, is_bounce_or_automated_email, process_bounce_notification


class TestEmailSyncProtection(CRMTestCase):
	def setUp(self):
		super().setUp()
		# Ensure test email account exists with create_contact=0
		if not frappe.db.exists("Email Account", "_Test Sync Email Account"):
			ea = frappe.new_doc("Email Account")
			ea.email_account_name = "_Test Sync Email Account"
			ea.email_id = "crm_sync_test@smrikaam.com"
			ea.create_contact = 0
			ea.enable_incoming = 1
			ea.insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Email Account", "_Test Sync Email Account", "create_contact", 0)

	def test_scenario_01_manual_and_import_contact_creation(self):
		"""Scenario 1 & 10: Admin imports / manually creates contact -> Succeeds normally."""
		test_email = "imported_prospect_01@smrikaam-client.com"
		if frappe.db.exists("Contact", {"email_id": test_email}):
			frappe.delete_doc("Contact", frappe.db.get_value("Contact", {"email_id": test_email}, "name"), force=True)

		contact = frappe.new_doc("Contact")
		contact.first_name = "Imported"
		contact.last_name = "Prospect"
		contact.email_id = test_email
		contact.custom_country = "Austria"
		contact.insert(ignore_permissions=True)

		self.assertTrue(frappe.db.exists("Contact", contact.name))
		self.assertEqual(contact.custom_country, "Austria")

	def test_scenario_02_assign_prospect_and_task_integrity(self):
		"""Scenario 2: Assigned prospect records and daily allocation remain intact."""
		test_email = "assigned_prospect_02@smrikaam-client.com"
		if not frappe.db.exists("Contact", {"email_id": test_email}):
			contact = frappe.new_doc("Contact")
			contact.first_name = "Assigned"
			contact.last_name = "Prospect"
			contact.email_id = test_email
			contact.insert(ignore_permissions=True)
		else:
			contact = frappe.get_doc("Contact", {"email_id": test_email})

		# Check or create allocation
		if not frappe.db.exists("CRM Daily Allocation", {"contact": contact.name}):
			alloc = frappe.new_doc("CRM Daily Allocation")
			alloc.contact = contact.name
			alloc.assigned_to = "Administrator"
			alloc.assigned_by = "Administrator"
			alloc.status = "To Do"
			alloc.insert(ignore_permissions=True)

		alloc_name = frappe.db.get_value("CRM Daily Allocation", {"contact": contact.name}, "name")
		self.assertTrue(alloc_name)
		self.assertEqual(frappe.db.get_value("CRM Daily Allocation", alloc_name, "assigned_to"), "Administrator")

	def test_scenario_03_outbound_email_to_existing_prospect_links_no_duplicate(self):
		"""Scenario 3: Outbound email records activity against existing Contact without duplicate."""
		test_email = "outbound_target_03@smrikaam-client.com"
		if not frappe.db.exists("Contact", {"email_id": test_email}):
			contact = frappe.new_doc("Contact")
			contact.first_name = "Target"
			contact.last_name = "Client"
			contact.email_id = test_email
			contact.insert(ignore_permissions=True)
		else:
			contact = frappe.get_doc("Contact", {"email_id": test_email})

		initial_contact_count = frappe.db.count("Contact", {"email_id": test_email})

		# Create outbound communication
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Email"
		comm.sent_or_received = "Sent"
		comm.sender = "sam.walker@smrikaam.com"
		comm.recipients = test_email
		comm.subject = "Proposal Discussion"
		comm.content = "Here is our proposal."
		comm.reference_doctype = "Contact"
		comm.reference_name = contact.name
		comm.insert(ignore_permissions=True)

		self.assertTrue(frappe.db.exists("Communication", comm.name))
		final_contact_count = frappe.db.count("Contact", {"email_id": test_email})
		self.assertEqual(initial_contact_count, final_contact_count)
		self.assertEqual(comm.reference_doctype, "Contact")
		self.assertEqual(comm.reference_name, contact.name)

	def test_scenario_04_inbound_unknown_sender_creates_no_contact(self):
		"""Scenario 4: Inbound email from unknown sender stores communication, NO contact created."""
		unknown_sender = "unknown_stranger_99@external-domain.org"
		# Ensure contact does not exist
		self.assertFalse(frappe.db.exists("Contact", {"email_id": unknown_sender}))

		# Receive email via Communication with email_account set
		comm = frappe.new_doc("Communication")
		comm.communication_type = "Communication"
		comm.communication_medium = "Email"
		comm.sent_or_received = "Received"
		comm.sender = unknown_sender
		comm.recipients = "sam.walker@smrikaam.com"
		comm.subject = "Cold Inquiry from Unknown"
		comm.content = "Hello, are you available?"
		comm.email_account = "_Test Sync Email Account"
		comm.insert(ignore_permissions=True)

		# Verify communication exists but NO Contact was created
		self.assertTrue(frappe.db.exists("Communication", comm.name))
		self.assertFalse(frappe.db.exists("Contact", {"email_id": unknown_sender}))
		self.assertNotEqual(comm.reference_doctype, "Contact")

	def test_scenario_05_inbound_mailer_daemon_creates_no_contact_and_marks_bounce(self):
		"""Scenario 5 & 7: Inbound Mailer-Daemon bounce creates NO contact and marks outbound email Bounced."""
		prospect_email = "bounced_prospect_05@invalid-smrikaam-domain.com"
		daemon_sender = "mailer-daemon@mx1.secureserver.net"

		# Create outbound email that will fail
		outbound_msg_id = f"<outbound-{frappe.generate_hash()[:10]}@smrikaam.com>"
		outbound = frappe.new_doc("Communication")
		outbound.communication_type = "Communication"
		outbound.communication_medium = "Email"
		outbound.sent_or_received = "Sent"
		outbound.sender = "sam.walker@smrikaam.com"
		outbound.recipients = prospect_email
		outbound.subject = "Urgent Proposal"
		outbound.message_id = outbound_msg_id
		outbound.delivery_status = "Sent"
		outbound.insert(ignore_permissions=True)

		contacts_before = frappe.db.count("Contact")

		# Create incoming bounce notification
		bounce = frappe.new_doc("Communication")
		bounce.communication_type = "Communication"
		bounce.communication_medium = "Email"
		bounce.sent_or_received = "Received"
		bounce.sender = daemon_sender
		bounce.recipients = "sam.walker@smrikaam.com"
		bounce.subject = "Mail delivery failed: returning message to sender"
		bounce.content = (
			f"This is the mail system at host mx1.\n"
			f"Delivery to the following recipients failed permanently:\n"
			f"* {prospect_email}\n"
			f"Action: failed\nStatus: 5.1.1\n"
		)
		bounce.text_content = bounce.content
		bounce.email_account = "_Test Sync Email Account"
		bounce.insert(ignore_permissions=True)

		# Verify no contact created
		contacts_after = frappe.db.count("Contact")
		self.assertEqual(contacts_before, contacts_after)
		self.assertFalse(frappe.db.exists("Contact", {"email_id": daemon_sender}))
		self.assertNotEqual(bounce.reference_doctype, "Contact")

		# Verify outbound communication delivery_status updated to "Bounced"
		outbound_status = frappe.db.get_value("Communication", outbound.name, "delivery_status")
		self.assertEqual(outbound_status, "Bounced")

	def test_scenario_06_inbound_postmaster_creates_no_contact(self):
		"""Scenario 6: Inbound postmaster notification creates NO contact."""
		postmaster_sender = "postmaster@relay.googlemail.com"
		contacts_before = frappe.db.count("Contact")

		bounce = frappe.new_doc("Communication")
		bounce.communication_type = "Communication"
		bounce.communication_medium = "Email"
		bounce.sent_or_received = "Received"
		bounce.sender = postmaster_sender
		bounce.recipients = "sam.walker@smrikaam.com"
		bounce.subject = "Delivery Status Notification (Failure)"
		bounce.content = "Technical details of permanent failure: 550 User not found."
		bounce.text_content = bounce.content
		bounce.email_account = "_Test Sync Email Account"
		bounce.insert(ignore_permissions=True)

		contacts_after = frappe.db.count("Contact")
		self.assertEqual(contacts_before, contacts_after)
		self.assertFalse(frappe.db.exists("Contact", {"email_id": postmaster_sender}))

	def test_scenario_08_existing_contact_incoming_email_associates_correctly(self):
		"""Scenario 8: Legitimate incoming email from existing contact associates without duplicate."""
		test_email = "legit_prospect_08@client-partner.com"
		if not frappe.db.exists("Contact", {"email_id": test_email}):
			contact = frappe.new_doc("Contact")
			contact.first_name = "Legit"
			contact.last_name = "Client"
			contact.email_id = test_email
			contact.insert(ignore_permissions=True)
		else:
			contact = frappe.get_doc("Contact", {"email_id": test_email})

		# Send outbound first
		outbound = frappe.new_doc("Communication")
		outbound.communication_type = "Communication"
		outbound.sent_or_received = "Sent"
		outbound.sender = "sam.walker@smrikaam.com"
		outbound.recipients = test_email
		outbound.subject = "Follow up"
		outbound.reference_doctype = "Contact"
		outbound.reference_name = contact.name
		outbound.message_id = f"<thread-08-{frappe.generate_hash()[:8]}@smrikaam.com>"
		outbound.insert(ignore_permissions=True)

		contacts_before = frappe.db.count("Contact")

		# Inbound reply from legit contact
		inbound = frappe.new_doc("Communication")
		inbound.communication_type = "Communication"
		inbound.sent_or_received = "Received"
		inbound.sender = test_email
		inbound.recipients = "sam.walker@smrikaam.com"
		inbound.subject = "Re: Follow up"
		inbound.content = "Thanks for following up! Let's talk tomorrow."
		inbound.in_reply_to = outbound.name
		inbound.email_account = "_Test Sync Email Account"
		inbound.insert(ignore_permissions=True)

		contacts_after = frappe.db.count("Contact")
		self.assertEqual(contacts_before, contacts_after)
		# Associated with the contact
		self.assertEqual(inbound.reference_doctype, "Contact")
		self.assertEqual(inbound.reference_name, contact.name)
		# Outbound marked Replied
		self.assertEqual(frappe.db.get_value("Communication", outbound.name, "delivery_status"), "Replied")

	def test_scenario_09_frappe_get_contacts_monkey_patch_safeguard(self):
		"""Scenario 9: Core frappe get_contacts with auto_create_contact=True never creates Contact."""
		daemon = "mailer-daemon@subdomain.bounce-host.net"
		contacts = get_contacts([daemon], auto_create_contact=True)
		self.assertEqual(contacts, [])
		self.assertFalse(frappe.db.exists("Contact", {"email_id": daemon}))
