import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.classes.unit_test_case import UnitTestCase

from crm.integrations.twilio.api import format_caller_id_label, get_caller_ids, voice
from crm.integrations.twilio.twilio_handler import Twilio


class TestTwilioCallerIDs(UnitTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_format_caller_id_label(self):
		# US number formatting
		self.assertEqual(format_caller_id_label("+12025550143"), "US United States • +12025550143")
		self.assertEqual(
			format_caller_id_label("+12025550143", "Sales"),
			"US United States (Sales) • +12025550143",
		)
		# UK number formatting
		self.assertEqual(format_caller_id_label("+447412097737"), "GB United Kingdom • +447412097737")
		# India number formatting
		self.assertEqual(format_caller_id_label("+919876543210"), "IN India • +919876543210")
		# Empty number
		self.assertEqual(format_caller_id_label(""), "")
		self.assertEqual(format_caller_id_label(None), "")

	def test_get_caller_ids_guest_rejected(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_caller_ids()
		frappe.set_user("Administrator")

	@patch("crm.integrations.twilio.api.frappe.get_doc")
	def test_get_caller_ids_disabled(self, mock_get_doc):
		mock_settings = MagicMock()
		mock_settings.enabled = 0
		mock_get_doc.return_value = mock_settings

		result = get_caller_ids()
		self.assertFalse(result["ok"])
		self.assertEqual(result["error"], "twilio_disabled")
		self.assertEqual(result["numbers"], [])

	@patch("crm.integrations.twilio.api.frappe.get_doc")
	def test_get_caller_ids_credentials_missing(self, mock_get_doc):
		mock_settings = MagicMock()
		mock_settings.enabled = 1
		mock_settings.account_sid = None
		mock_settings.get_password.return_value = None
		mock_settings.api_key = None
		mock_get_doc.return_value = mock_settings

		result = get_caller_ids()
		self.assertFalse(result["ok"])
		self.assertEqual(result["error"], "twilio_credentials_missing")
		self.assertEqual(result["numbers"], [])

	@patch("crm.integrations.twilio.api.Twilio.connect")
	@patch("crm.integrations.twilio.api.frappe.get_doc")
	def test_get_caller_ids_returns_authorized_numbers(self, mock_get_doc, mock_connect):
		mock_settings = MagicMock()
		mock_settings.enabled = 1
		mock_settings.account_sid = "AC00000000000000000000000000000000"
		mock_settings.get_password.return_value = "token123"
		mock_get_doc.return_value = mock_settings

		mock_twilio = MagicMock()
		mock_num1 = SimpleNamespace(
			phone_number="+12025550143",
			friendly_name="(202) 555-0143",
			capabilities={"voice": True, "SMS": True},
		)
		mock_twilio.get_voice_phone_numbers.return_value = [mock_num1]
		mock_connect.return_value = mock_twilio

		result = get_caller_ids()
		self.assertTrue(result["ok"])
		self.assertEqual(len(result["numbers"]), 1)
		self.assertEqual(result["numbers"][0]["number"], "+12025550143")
		self.assertIn("US United States", result["numbers"][0]["label"])

	def test_get_voice_phone_numbers_filters_non_voice(self):
		mock_client = MagicMock()
		num_voice = SimpleNamespace(
			phone_number="+12025550143",
			capabilities={"voice": True, "SMS": True},
		)
		num_sms_only = SimpleNamespace(
			phone_number="+18005550199",
			capabilities={"voice": False, "SMS": True},
		)
		mock_client.incoming_phone_numbers.list.return_value = [num_voice, num_sms_only]

		handler = Twilio.__new__(Twilio)
		handler.twilio_client = mock_client

		voice_numbers = handler.get_voice_phone_numbers()
		self.assertEqual(len(voice_numbers), 1)
		self.assertEqual(voice_numbers[0].phone_number, "+12025550143")

	@patch("crm.integrations.twilio.api.create_call_log")
	@patch("crm.integrations.twilio.api.validate_twilio_request")
	def test_voice_webhook_uses_authorized_caller_id(
		self, mock_validate_request, mock_create_call_log
	):
		mock_twilio = MagicMock()
		mock_twilio.get_phone_numbers.return_value = ["+12025550143"]
		mock_twilio.generate_twilio_dial_response.return_value = MagicMock(to_xml=lambda: "<Response/>")
		mock_validate_request.return_value = mock_twilio

		orig_get_value = frappe.db.get_value

		def side_effect(doctype, *args, **kwargs):
			if doctype == "CRM Telephony Agent":
				return "+19999999999"
			return orig_get_value(doctype, *args, **kwargs)

		with patch("crm.integrations.twilio.api.frappe.db.get_value", side_effect=side_effect):
			# Outbound call with authorized callerId
			response = voice(
				Caller="client:agent_user",
				To="+15551234567",
				callerId="+12025550143",
			)
			mock_twilio.generate_twilio_dial_response.assert_called_with("+12025550143", "+15551234567")

	@patch("crm.integrations.twilio.api.create_call_log")
	@patch("crm.integrations.twilio.api.validate_twilio_request")
	def test_voice_webhook_ignores_unauthorized_caller_id(
		self, mock_validate_request, mock_create_call_log
	):
		mock_twilio = MagicMock()
		mock_twilio.get_phone_numbers.return_value = ["+12025550143"]
		mock_twilio.generate_twilio_dial_response.return_value = MagicMock(to_xml=lambda: "<Response/>")
		mock_validate_request.return_value = mock_twilio

		orig_get_value = frappe.db.get_value

		def side_effect(doctype, *args, **kwargs):
			if doctype == "CRM Telephony Agent":
				return "+12025550143"
			return orig_get_value(doctype, *args, **kwargs)

		with patch("crm.integrations.twilio.api.frappe.db.get_value", side_effect=side_effect):
			# Outbound call with unauthorized fake UK callerId
			response = voice(
				Caller="client:agent_user",
				To="+15551234567",
				callerId="+447412097737",
			)
			# Should fall back to agent number, NOT the unauthorized UK number
			mock_twilio.generate_twilio_dial_response.assert_called_with("+12025550143", "+15551234567")
