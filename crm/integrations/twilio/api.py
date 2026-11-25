import json

import frappe
from frappe import _
from twilio.twiml.voice_response import VoiceResponse
from werkzeug.wrappers import Response

from crm.integrations.api import get_contact_by_phone_number

from .twilio_handler import IncomingCall, Twilio, TwilioCallDetails


def validate_twilio_request(args, require_application_sid: bool = False):
	twilio = Twilio.connect()
	if not twilio:
		frappe.throw(_("Twilio configuration is missing"), frappe.PermissionError)

	account_sid = frappe.utils.cstr(args.get("AccountSid"))
	if not account_sid or account_sid != frappe.utils.cstr(twilio.account_sid):
		frappe.throw(_("Invalid Twilio account"), frappe.PermissionError)

	if require_application_sid:
		application_sid = frappe.utils.cstr(args.get("ApplicationSid"))
		if not application_sid or application_sid != frappe.utils.cstr(twilio.application_sid):
			frappe.throw(_("Invalid Twilio application"), frappe.PermissionError)

	return twilio


@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("CRM Twilio Settings", "enabled")


@frappe.whitelist()
def check_twilio_configuration():
	"""Validates the complete Twilio setup and returns detailed configuration status."""
	settings = frappe.get_doc("CRM Twilio Settings")
	agent_number = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number") or ""

	missing_fields = []
	if not settings.enabled:
		missing_fields.append(_("Twilio Integration is Disabled"))
	if not settings.account_sid:
		missing_fields.append("Account SID")
	if not settings.api_key:
		missing_fields.append("API Key")
	has_api_secret = bool(settings.get_password("api_secret", raise_exception=False))
	if not has_api_secret:
		missing_fields.append("API Secret")
	if not settings.twiml_sid:
		missing_fields.append("TwiML Application SID")
	if not agent_number:
		missing_fields.append(_("Caller Twilio Phone Number (CRM Telephony Agent)"))

	return {
		"enabled": bool(settings.enabled),
		"account_sid": bool(settings.account_sid),
		"api_key": bool(settings.api_key),
		"api_secret": has_api_secret,
		"twiml_sid": bool(settings.twiml_sid),
		"agent_number": agent_number,
		"is_configured": len(missing_fields) == 0,
		"missing_fields": missing_fields,
		"record_calls": bool(settings.record_calls),
		"enable_live_transcription": bool(getattr(settings, "enable_live_transcription", False)),
	}


@frappe.whitelist()
def generate_access_token():
	"""Returns access token that is required to authenticate Twilio Client SDK."""
	settings = frappe.get_doc("CRM Twilio Settings")
	if not (settings and settings.enabled):
		return {
			"ok": False,
			"error": "twilio_not_configured",
			"detail": _("Twilio configuration is missing. Please contact your administrator."),
		}

	missing = []
	if not settings.account_sid:
		missing.append("Account SID")
	if not settings.api_key:
		missing.append("API Key")
	if not settings.get_password("api_secret", raise_exception=False):
		missing.append("API Secret")
	if not settings.twiml_sid:
		missing.append("TwiML Application SID")

	if missing:
		return {
			"ok": False,
			"error": "twilio_credentials_missing",
			"detail": _("Twilio configuration is incomplete. Missing settings: {0}. Please contact your administrator.").format(", ".join(missing)),
		}

	from_number = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number")
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": _("Your account is not configured with a Twilio phone number. Please contact your administrator."),
		}

	try:
		twilio = Twilio(settings=settings)
		token = twilio.generate_voice_access_token(identity=frappe.session.user)
		if not token:
			return {
				"ok": False,
				"error": "token_generation_failed",
				"detail": _("Failed to generate Twilio access token. Please verify Twilio settings."),
			}

		return {
			"ok": True,
			"token": frappe.safe_decode(token),
		}
	except Exception as exc:
		frappe.log_error(title="Failed to generate Twilio voice access token")
		return {
			"ok": False,
			"error": "token_generation_failed",
			"detail": _("Failed to generate Twilio access token: {0}").format(str(exc)),
		}


COUNTRY_PREFIX_MAP = {
	"+1": ("US", "United States"),
	"+44": ("GB", "United Kingdom"),
	"+91": ("IN", "India"),
	"+61": ("AU", "Australia"),
	"+49": ("DE", "Germany"),
	"+33": ("FR", "France"),
	"+971": ("AE", "UAE"),
	"+65": ("SG", "Singapore"),
	"+43": ("AT", "Austria"),
	"+41": ("CH", "Switzerland"),
}


def format_caller_id_label(phone_number: str, friendly_name: str | None = None) -> str:
	"""Formats an authorized caller ID phone number for display."""
	if not phone_number:
		return ""

	phone = str(phone_number).strip()

	prefix_info = None
	for code, info in COUNTRY_PREFIX_MAP.items():
		if phone.startswith(code):
			prefix_info = info
			break

	if prefix_info:
		iso, country = prefix_info
		if friendly_name and friendly_name != phone and not friendly_name.startswith("+"):
			return f"{iso} {country} ({friendly_name}) • {phone}"
		return f"{iso} {country} • {phone}"

	if friendly_name and friendly_name != phone:
		return f"{friendly_name} • {phone}"

	return phone


@frappe.whitelist()
def get_caller_ids():
	"""Retrieve verified and authorized Twilio phone numbers for outbound voice calling.
	Only numbers owned by the configured Twilio account with outbound voice capability are returned.
	"""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	settings = frappe.get_doc("CRM Twilio Settings")
	if not (settings and settings.enabled):
		return {
			"ok": False,
			"error": "twilio_disabled",
			"message": _("Twilio integration is not enabled."),
			"numbers": [],
		}

	has_auth_token = bool(settings.get_password("auth_token", raise_exception=False))
	if not settings.account_sid or not (has_auth_token or settings.api_key):
		return {
			"ok": False,
			"error": "twilio_credentials_missing",
			"message": _("Twilio credentials are missing or incomplete. Please contact your administrator."),
			"numbers": [],
		}

	try:
		twilio = Twilio.connect()
		if not twilio:
			return {
				"ok": False,
				"error": "twilio_not_connected",
				"message": _("Twilio service is currently unavailable."),
				"numbers": [],
			}

		voice_numbers = twilio.get_voice_phone_numbers()
		caller_ids = []
		for num in voice_numbers:
			phone = getattr(num, "phone_number", None)
			if not phone:
				continue
			friendly_name = getattr(num, "friendly_name", None) or phone
			label = format_caller_id_label(phone, friendly_name)
			caller_ids.append({
				"number": phone,
				"friendly_name": friendly_name,
				"label": label,
			})

		return {
			"ok": True,
			"numbers": caller_ids,
		}
	except Exception as exc:
		frappe.log_error(title="Failed to retrieve Twilio caller numbers", message=str(exc))
		return {
			"ok": False,
			"error": "fetch_failed",
			"message": _("Failed to retrieve Twilio caller numbers: {0}").format(str(exc)),
			"numbers": [],
		}


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server."""

	def _get_caller_number(caller):
		identity = caller.replace("client:", "").strip()
		user = Twilio.emailid_from_identity(identity)
		return frappe.db.get_value("CRM Telephony Agent", user, "twilio_number")

	args = frappe._dict(kwargs)
	twilio = validate_twilio_request(args, require_application_sid=True)

	# Generate TwiML instructions to make a call
	from_number = _get_caller_number(args.Caller)

	# If a specific callerId was sent by the client, verify that it is an authorized incoming number
	requested_caller_id = args.get("callerId") or args.get("From")
	if requested_caller_id and not requested_caller_id.startswith("client:"):
		try:
			authorized_numbers = twilio.get_phone_numbers()
			cleaned_requested = requested_caller_id.replace(" ", "")
			matching = next((n for n in authorized_numbers if n.replace(" ", "") == cleaned_requested), None)
			if matching:
				from_number = matching
		except Exception as exc:
			frappe.log_error(title="Failed to verify Twilio caller ID in voice webhook", message=str(exc))

	if not from_number:
		resp = VoiceResponse()
		resp.say(_("Your account is not configured with a phone number. Please contact your administrator."))
		return Response(resp.to_xml(), mimetype="text/xml")

	call_details = TwilioCallDetails(args, call_from=from_number)
	try:
		create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	resp = twilio.generate_twilio_dial_response(from_number, args.To)
	return Response(resp.to_xml(), mimetype="text/xml")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	call_details = TwilioCallDetails(args)
	try:
		create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype="text/xml")


def _call_failed_response():
	resp = VoiceResponse()
	resp.say(_("We're unable to connect your call right now. Please try again later."))
	return resp


def find_call_log(call_sid: str):
	"""Find CRM Call Log by CallSid (checks name, id, or resolves child leg via Twilio)."""
	if not call_sid:
		return None

	# 1. Direct match by name
	if frappe.db.exists("CRM Call Log", call_sid):
		return frappe.get_doc("CRM Call Log", call_sid)

	# 2. Match by id field
	name_by_id = frappe.db.get_value("CRM Call Log", {"id": call_sid}, "name")
	if name_by_id:
		return frappe.get_doc("CRM Call Log", name_by_id)

	# 3. If call_sid is a child leg, lookup parent SID from Twilio API
	try:
		twilio = Twilio.connect()
		if twilio:
			call_info = twilio.get_call_info(call_sid)
			parent_sid = getattr(call_info, "parent_call_sid", None)
			if parent_sid:
				if frappe.db.exists("CRM Call Log", parent_sid):
					return frappe.get_doc("CRM Call Log", parent_sid)
				name_by_parent = frappe.db.get_value("CRM Call Log", {"id": parent_sid}, "name")
				if name_by_parent:
					return frappe.get_doc("CRM Call Log", name_by_parent)
	except Exception:
		pass

	return None


def create_call_log(call_details: TwilioCallDetails):
	details = call_details.to_dict()
	call_sid = details.get("id")

	# Idempotent: return existing call log if already created
	existing_log = find_call_log(call_sid)
	if existing_log:
		return existing_log

	call_log = frappe.get_doc({
		**details,
		"doctype": "CRM Call Log",
		"telephony_medium": "Twilio",
	})

	# link call log with prospect / contact / lead / deal
	contact_number = details.get("from") if details.get("type") == "Incoming" else details.get("to")
	link(contact_number, call_log)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()

	frappe.publish_realtime(
		"crm:call_updated",
		{
			"call_log": call_log.name,
			"status": call_log.status,
			"type": call_log.type,
			"duration": call_log.duration,
		},
		after_commit=True,
	)
	return call_log


def link(contact_number, call_log):
	if not contact_number:
		return

	contact = get_contact_by_phone_number(contact_number)
	if contact and contact.get("name"):
		contact_name = contact.get("name")
		# Always link Contact
		call_log.link_with_reference_doc("Contact", contact_name)

		# Ensure primary reference points to Contact
		if not call_log.reference_doctype or call_log.reference_doctype == "Contact":
			call_log.reference_doctype = "Contact"
			call_log.reference_docname = contact_name

		# Also link associated Deal and Lead if present
		if contact.get("deal"):
			call_log.link_with_reference_doc("CRM Deal", contact.get("deal"))
		if contact.get("lead"):
			call_log.link_with_reference_doc("CRM Lead", contact.get("lead"))
	elif contact and contact.get("lead"):
		lead_name = contact.get("lead")
		call_log.link_with_reference_doc("CRM Lead", lead_name)
		if not call_log.reference_doctype:
			call_log.reference_doctype = "CRM Lead"
			call_log.reference_docname = lead_name


def _parse_datetime_field(val):
	if not val:
		return None
	if hasattr(val, "strftime"):
		return get_datetime_from_timestamp(val)
	try:
		return str(frappe.utils.get_datetime(val))
	except Exception:
		return None


def update_call_log(call_sid, status=None, duration=None, start_time=None, end_time=None):
	"""Update call log status and details."""
	call_log = find_call_log(call_sid)
	if not call_log:
		return None

	try:
		twilio = Twilio.connect()
		if twilio:
			try:
				call_details = twilio.get_call_info(call_sid)
				if not status and hasattr(call_details, "status") and call_details.status:
					status = call_details.status
				if duration is None and hasattr(call_details, "duration") and call_details.duration is not None:
					duration = call_details.duration
				if not start_time and hasattr(call_details, "start_time") and call_details.start_time:
					start_time = call_details.start_time
				if not end_time and hasattr(call_details, "end_time") and call_details.end_time:
					end_time = call_details.end_time
			except Exception:
				pass

		if status:
			call_log.status = TwilioCallDetails.get_call_status(status)

		if duration is not None:
			try:
				call_log.duration = int(duration)
			except (ValueError, TypeError):
				pass

		if start_time:
			parsed_start = _parse_datetime_field(start_time)
			if parsed_start:
				call_log.start_time = parsed_start

		if end_time:
			parsed_end = _parse_datetime_field(end_time)
			if parsed_end:
				call_log.end_time = parsed_end

		call_log.save(ignore_permissions=True)
		frappe.db.commit()

		frappe.publish_realtime(
			"crm:call_updated",
			{
				"call_log": call_log.name,
				"status": call_log.status,
				"duration": call_log.duration,
				"recording_url": call_log.recording_url,
			},
			after_commit=True,
		)
		return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()
		return call_log


def get_twilio_settings():
	return frappe.get_single("CRM Twilio Settings")


@frappe.whitelist(allow_guest=True)
def update_recording_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	recording_url = args.get("RecordingUrl")
	call_sid = args.get("CallSid")
	if not recording_url or not call_sid:
		frappe.throw(_("Missing recording parameters"), frappe.ValidationError)

	call_log = find_call_log(call_sid)
	if not call_log:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	try:
		# If Twilio recording URL lacks audio format extension, append .mp3
		if recording_url.startswith("https://api.twilio.com") and not recording_url.endswith((".mp3", ".wav")):
			recording_url = f"{recording_url}.mp3"

		call_log.recording_url = recording_url

		# Update duration from RecordingDuration if available and duration is not set
		if args.get("RecordingDuration") and (not call_log.duration or call_log.duration == 0):
			try:
				call_log.duration = int(args.get("RecordingDuration"))
			except (ValueError, TypeError):
				pass

		if call_log.status in ("Initiated", "Ringing", "In Progress"):
			call_log.status = "Completed"

		call_log.save(ignore_permissions=True)
		frappe.db.commit()

		frappe.publish_realtime(
			"crm:call_updated",
			{
				"call_log": call_log.name,
				"status": call_log.status,
				"recording_url": call_log.recording_url,
				"duration": call_log.duration,
			},
			after_commit=True,
		)
		return {"status": "success", "call_log": call_log.name}
	except Exception as exc:
		frappe.log_error(title=_("Failed to capture Twilio recording"))
		raise exc


@frappe.whitelist(allow_guest=True)
def update_call_status_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	target_sid = args.get("ParentCallSid") or args.get("CallSid")
	call_log = update_call_log(
		target_sid,
		status=args.get("CallStatus"),
		duration=args.get("CallDuration"),
	)
	if not call_log:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	call_info = {
		"ParentCallSid": args.get("ParentCallSid"),
		"CallSid": args.get("CallSid"),
		"CallStatus": args.get("CallStatus"),
		"CallDuration": args.get("CallDuration"),
		"From": args.get("From"),
		"To": args.get("To"),
	}

	# Send user-defined message to active call if supported (ignore if call already ended)
	if args.get("ParentCallSid"):
		try:
			client = Twilio.get_twilio_client()
			client.calls(args.ParentCallSid).user_defined_messages.create(content=json.dumps(call_info))
		except Exception:
			pass

	return {"status": "success", "call_log": call_log.name}


def get_datetime_from_timestamp(timestamp):
	from datetime import datetime
	from zoneinfo import ZoneInfo

	if not timestamp:
		return None

	datetime_utc_tz_str = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")
	datetime_utc_tz = datetime.strptime(datetime_utc_tz_str, "%Y-%m-%d %H:%M:%S%z")
	system_timezone = frappe.utils.get_system_timezone()
	converted_datetime = datetime_utc_tz.astimezone(ZoneInfo(system_timezone))
	return frappe.utils.format_datetime(converted_datetime, "yyyy-MM-dd HH:mm:ss")


@frappe.whitelist(allow_guest=True)
def transcription_callback(**kwargs):
	"""Webhook endpoint for Twilio real-time transcription callbacks.
	Receives streaming transcription events (both tracks) and broadcasts them to the agent
	via Frappe realtime socket while persisting final utterances in the CRM Call Log.
	"""
	args = frappe._dict(kwargs)
	if not args and frappe.request and getattr(frappe.request, "data", None):
		try:
			args = frappe._dict(json.loads(frappe.request.data))
		except Exception:
			pass

	validate_twilio_request(args)

	call_sid = args.get("CallSid")
	if not call_sid:
		return {"status": "ignored", "reason": "Missing CallSid"}

	call_log = frappe.db.get_value("CRM Call Log", call_sid, ["name", "type", "caller", "receiver"], as_dict=True)
	if not call_log and args.get("ParentCallSid"):
		call_log = frappe.db.get_value("CRM Call Log", args.get("ParentCallSid"), ["name", "type", "caller", "receiver"], as_dict=True)
	if not call_log:
		call_log = frappe.db.get_value("CRM Call Log", {"id": call_sid}, ["name", "type", "caller", "receiver"], as_dict=True)

	transcription_event = args.get("TranscriptionEvent") or args.get("event") or ""

	agent_user = None
	if call_log:
		agent_user = call_log.caller if call_log.type == "Outgoing" else call_log.receiver

	if transcription_event == "transcription-started":
		msg = {
			"call_sid": call_sid,
			"event": "started",
		}
		if agent_user:
			frappe.publish_realtime("twilio_transcription", msg, user=agent_user, after_commit=False)
		else:
			frappe.publish_realtime("twilio_transcription", msg, after_commit=False)
		return {"status": "ok"}

	elif transcription_event == "transcription-stopped":
		msg = {
			"call_sid": call_sid,
			"event": "stopped",
		}
		if agent_user:
			frappe.publish_realtime("twilio_transcription", msg, user=agent_user, after_commit=False)
		else:
			frappe.publish_realtime("twilio_transcription", msg, after_commit=False)
		return {"status": "ok"}

	# Handle transcription-content
	raw_data = args.get("TranscriptionData")
	data = {}
	if isinstance(raw_data, str):
		try:
			data = json.loads(raw_data)
		except Exception:
			data = {"transcript": raw_data}
	elif isinstance(raw_data, dict):
		data = raw_data

	transcript_text = (data.get("transcript") or "").strip()
	if not transcript_text:
		return {"status": "ok"}

	# Determine speaker: Customer or Agent
	track = args.get("Track") or ""
	speaker = None

	if track == "inbound_track":
		speaker = args.get("InboundTrackLabel") or args.get("TrackLabel")
	elif track == "outbound_track":
		speaker = args.get("OutboundTrackLabel") or args.get("TrackLabel")
	else:
		speaker = args.get("TrackLabel")

	if not speaker or speaker.lower() not in ("customer", "agent"):
		if call_log:
			if call_log.type == "Outgoing":
				speaker = "agent" if track == "inbound_track" else "customer"
			else:
				speaker = "customer" if track == "inbound_track" else "agent"
		else:
			speaker = "agent" if track == "inbound_track" else "customer"

	speaker = "customer" if speaker.lower() in ("customer", "caller", "client", "lead") else "agent"

	is_final = str(args.get("Final", "false")).lower() in ("true", "1") or bool(data.get("isFinal"))

	msg = {
		"call_sid": call_sid,
		"event": "content",
		"speaker": speaker,
		"text": transcript_text,
		"is_final": is_final,
		"sequence_id": args.get("SequenceId"),
		"timestamp": args.get("Timestamp"),
	}

	if agent_user:
		frappe.publish_realtime("twilio_transcription", msg, user=agent_user, after_commit=False)
	else:
		frappe.publish_realtime("twilio_transcription", msg, after_commit=False)

	# Atomically record final utterance to CRM Call Log
	if is_final and call_log:
		formatted_utterance = f"[{speaker.capitalize()}]\n{transcript_text}\n\n"
		frappe.db.sql(
			"""
			UPDATE `tabCRM Call Log`
			SET transcript = CONCAT(IFNULL(transcript, ''), %s)
			WHERE name = %s
			""",
			(formatted_utterance, call_log.name),
		)
		frappe.db.commit()

	return {"status": "ok"}


@frappe.whitelist()
def save_call_transcript(call_sid: str, transcript: str):
	"""Save complete formatted transcript to CRM Call Log upon call completion."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	if transcript and transcript.strip():
		call_log.transcript = transcript.strip()
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
	return {"status": "ok", "transcript": call_log.transcript}


@frappe.whitelist()
def get_call_transcript(call_sid: str):
	"""Retrieve call transcript for a given call sid."""
	if not frappe.has_permission("CRM Call Log", "read", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return frappe.db.get_value("CRM Call Log", call_sid, "transcript")
