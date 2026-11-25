import functools
import re

import frappe
import phonenumbers
import requests
from frappe import _
from frappe.core.doctype.comment.comment import Comment
from frappe.core.doctype.communication.communication import Communication
from frappe.utils import floor, now
from phonenumbers import NumberParseException
from phonenumbers import PhoneNumberFormat as PNF


def parse_phone_number(phone_number: str, default_country: str = "IN"):
	try:
		# Parse the number
		number = phonenumbers.parse(phone_number, default_country)

		# Get various information about the number
		result = {
			"is_valid": phonenumbers.is_valid_number(number),
			"country_code": number.country_code,
			"national_number": str(number.national_number),
			"formats": {
				"international": phonenumbers.format_number(number, PNF.INTERNATIONAL),
				"national": phonenumbers.format_number(number, PNF.NATIONAL),
				"E164": phonenumbers.format_number(number, PNF.E164),
				"RFC3966": phonenumbers.format_number(number, PNF.RFC3966),
			},
			"type": phonenumbers.number_type(number),
			"country": phonenumbers.region_code_for_number(number),
			"is_possible": phonenumbers.is_possible_number(number),
		}

		return {"success": True, **result}
	except NumberParseException as e:
		return {"success": False, "error": str(e)}


def are_same_phone_number(number1: str, number2: str, default_region: str = "IN", validate: bool = True):
	"""
	Check if two phone numbers are the same, regardless of their format.

	Args:
	    number1 (str): First phone number
	    number2 (str): Second phone number
	    default_region (str): Default region code for parsing ambiguous numbers

	Returns:
	    bool: True if numbers are same, False otherwise
	"""
	try:
		# Parse both numbers
		parsed1 = phonenumbers.parse(number1, default_region)
		parsed2 = phonenumbers.parse(number2, default_region)

		# Check if both numbers are valid
		if validate and not (phonenumbers.is_valid_number(parsed1) and phonenumbers.is_valid_number(parsed2)):
			return False

		# Convert both to E164 format and compare
		formatted1 = phonenumbers.format_number(parsed1, phonenumbers.PhoneNumberFormat.E164)
		formatted2 = phonenumbers.format_number(parsed2, phonenumbers.PhoneNumberFormat.E164)

		return formatted1 == formatted2

	except phonenumbers.NumberParseException:
		return False


def seconds_to_duration(seconds: float | int) -> str:
	if not seconds:
		return "0s"

	hours = floor(seconds // 3600)
	minutes = floor((seconds % 3600) // 60)
	seconds = floor((seconds % 3600) % 60)

	# 1h 0m 0s -> 1h
	# 0h 1m 0s -> 1m
	# 0h 0m 1s -> 1s
	# 1h 1m 0s -> 1h 1m
	# 1h 0m 1s -> 1h 1s
	# 0h 1m 1s -> 1m 1s
	# 1h 1m 1s -> 1h 1m 1s

	if hours and minutes and seconds:
		return f"{hours}h {minutes}m {seconds}s"
	elif hours and minutes:
		return f"{hours}h {minutes}m"
	elif hours and seconds:
		return f"{hours}h {seconds}s"
	elif minutes and seconds:
		return f"{minutes}m {seconds}s"
	elif hours:
		return f"{hours}h"
	elif minutes:
		return f"{minutes}m"
	elif seconds:
		return f"{seconds}s"
	else:
		return "0s"


def is_admin(user: str | None = None) -> bool:
	"""
	Check whether `user` is an admin

	:param user: User to check against, defaults to current user
	:return: Whether `user` is an admin
	"""
	user = user or frappe.session.user
	return user == "Administrator"


def is_sales_user(user: str | None = None) -> bool:
	"""
	Check whether `user` is an agent

	:param user: User to check against, defaults to current user
	:return: Whether `user` is an agent
	"""
	user = user or frappe.session.user
	return is_admin() or "Sales Manager" in frappe.get_roles(user) or "Sales User" in frappe.get_roles(user)


def sales_user_only(fn: callable) -> callable:
	"""Decorator to validate if user is an agent."""

	@functools.wraps(fn)
	def wrapper(*args, **kwargs):
		if not is_sales_user():
			frappe.throw(
				msg=_("You are not permitted to access this resource."),
				title=_("Not Allowed"),
				exc=frappe.PermissionError,
			)

		return fn(*args, **kwargs)

	return wrapper


def is_frappe_version(version: str, above: bool = False, below: bool = False):
	from frappe.pulse.utils import get_frappe_version

	current_version = get_frappe_version()
	major_version = int(current_version.split(".")[0])
	target_version = int(version.split(".")[0])

	if above:
		return major_version >= target_version
	if below:
		return major_version < target_version
	return major_version == target_version


def _should_update_modified(doc: Communication | Comment) -> bool:
	if not frappe.db.get_single_value("FCRM Settings", "update_timestamp_on_new_communication"):
		return False

	if not (doc.reference_doctype and doc.reference_name):
		return False

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"]:
		return False

	if doc.doctype not in ["Comment", "Communication"]:
		return False

	return True


def _get_communication_status(doc: Communication) -> str | None:
	if doc.doctype != "Communication":
		return None

	if not (doc.reference_doctype and doc.reference_name):
		return None

	if doc.sent_or_received not in ("Sent", "Received"):
		return None

	auto_reopen = frappe.db.get_single_value("FCRM Settings", "auto_reopen_on_new_communication")
	auto_replied = frappe.db.get_single_value("FCRM Settings", "auto_mark_replied_on_response")

	if doc.sent_or_received == "Received" and auto_reopen:
		return "Open"
	elif doc.sent_or_received == "Sent" and auto_replied:
		return "Replied"

	return None


def create_lead_from_incoming_email(doc: Communication, method: str | None = None):
	if doc.doctype != "Communication":
		return

	if doc.sent_or_received != "Received" and doc.communication_type != "Communication":
		return

	if doc.reference_doctype and doc.reference_name:
		return

	if not doc.email_account:
		return

	if is_bounce_email(doc):
		return

	create_lead_enabled = frappe.db.get_value(
		"Email Account", doc.email_account, "create_lead_from_incoming_email"
	)
	if not create_lead_enabled:
		return

	if frappe.db.exists("CRM Lead", {"email": doc.sender}):
		return

	if _is_automated_email_sender(doc.sender):
		return

	lead = frappe.new_doc("CRM Lead")
	lead.email = doc.sender

	if doc.sender_full_name:
		lead.first_name = doc.sender_full_name.split(" ")[0]
		lead.last_name = (
			doc.sender_full_name.split(" ")[-1] if len(doc.sender_full_name.split(" ")) > 1 else ""
		)
	else:
		lead.first_name = doc.sender.split("@")[0]

	if frappe.db.exists("CRM Lead Source", "Email"):
		lead.source = "Email"

	lead.insert(ignore_permissions=True)

	doc.reference_doctype = "CRM Lead"
	doc.reference_name = lead.name
	doc.save(ignore_permissions=True)


_AUTOMATED_SENDER_LOCAL_PARTS = frozenset(
	{
		"no-reply",
		"noreply",
		"no_reply",
		"donotreply",
		"do-not-reply",
		"do_not_reply",
		"mailer-daemon",
		"mailer_daemon",
		"postmaster",
		"bounce",
		"bounces",
		"daemon",
		"mail-daemon",
		"mail_daemon",
		"autoresponder",
	}
)

_BOUNCE_SENDER_PATTERNS = _AUTOMATED_SENDER_LOCAL_PARTS

_BOUNCE_SUBJECT_KEYWORDS = [
	"delivery status notification",
	"message delivery failure",
	"undelivered mail",
	"mail delivery failed",
	"failure notice",
	"returned mail",
	"undeliverable",
	"delivery notification: delivery has failed",
	"mail delivery subsystem",
	"delivery failure",
	"delayed delivery",
	"warning: could not send message",
]

_BOUNCE_CONTENT_INDICATORS = [
	"multipart/report",
	"message/delivery-status",
	"delivery to the following recipients failed",
	"your message wasn't delivered to",
	"your message could not be delivered",
	"this is an automatically generated delivery status notification",
	"action: failed",
	"remote-mta:",
	"reporting-mta:",
	"diagnostic-code:",
	"status: 5.",
	"status: 4.",
	"550 5.1.1",
	"554 5.7.1",
	"address couldn't be found",
	"recipient address rejected",
	"user unknown",
	"mailbox unavailable",
	"host or domain name not found",
]


def is_bounce_or_automated_email(sender: str | None) -> bool:
	"""Check if an email address belongs to automated notifications or bounce systems."""
	if not sender:
		return True
	sender_clean = sender.strip().strip("<>").strip()
	if not sender_clean or sender_clean == "<>":
		return True
	if "@" not in sender_clean:
		return sender_clean.lower() in _BOUNCE_SENDER_PATTERNS

	match = re.search(r"<?([^<>\s]+@[^<>\s]+)>?", sender)
	address = match.group(1) if match else sender_clean
	local = address.split("@", 1)[0].strip().lower()
	local = re.sub(r"\+.*$", "", local)
	if local in _BOUNCE_SENDER_PATTERNS:
		return True
	return local.endswith(("-noreply", "_noreply", "-no-reply", "_no-reply", "-bounce", "_bounce", "-bounces"))


def is_bounce_contact_name(name: str | None) -> bool:
	"""Check if a contact name or title is a bounce / system daemon identifier."""
	if not name:
		return False
	n = name.strip().lower()
	bounce_names = {
		"mailer daemon",
		"mailer-daemon",
		"mailer_daemon",
		"postmaster",
		"noreply",
		"no-reply",
		"no_reply",
		"bounce",
		"daemon",
	}
	if n in bounce_names or n.startswith(("mailer daemon", "mailer-daemon", "postmaster", "noreply", "no-reply")):
		return True
	return False


def is_bounce_email(doc: Communication) -> bool:
	"""Detect automated delivery failure and bounce messages using reliable email headers,
	metadata, subjects, and DSN indicators.
	"""
	if doc.doctype != "Communication" or getattr(doc, "sent_or_received", "") != "Received":
		return False

	sender = getattr(doc, "sender", None) or ""
	# 1. Fast check: sender local-part is mailer-daemon, postmaster, bounce, etc.
	if sender:
		sender_clean = sender.strip().strip("<>").lower()
		if not sender_clean or sender_clean == "<>" or any(p in sender_clean for p in ["mailer-daemon", "mailer_daemon", "postmaster"]):
			return True

	# 2. Subject check
	subject = (getattr(doc, "subject", None) or "").strip().lower()
	for kw in _BOUNCE_SUBJECT_KEYWORDS:
		if kw in subject:
			return True

	# 3. Content / Text Content DSN indicators
	content = (getattr(doc, "content", None) or "").lower()
	text_content = (getattr(doc, "text_content", None) or "").lower()
	full_text = f"{content}\n{text_content}"

	match_count = 0
	for ind in _BOUNCE_CONTENT_INDICATORS:
		if ind in full_text:
			match_count += 1
			if match_count >= 1 and (is_bounce_or_automated_email(sender) or "delivery" in subject or "undeliver" in subject or "fail" in subject):
				return True
			if match_count >= 2:
				return True

	return False


def extract_bounced_recipient(doc: Communication) -> str | None:
	"""Extract the failed recipient email address from bounce notification content."""
	text = f"{doc.text_content or ''}\n{doc.content or ''}"
	patterns = [
		r"Delivery to the following recipients failed(?: permanently)?:\s*[*•-]?\s*<?([^\s<>@]+@[^\s<>@]+)>?",
		r"Your message wasn't delivered to\s+<?([^\s<>@]+@[^\s<>@]+)>?",
		r"Your message could not be delivered to\s+<?([^\s<>@]+@[^\s<>@]+)>?",
		r"Final-Recipient:\s*(?:rfc822;)?\s*<?([^\s<>@]+@[^\s<>@]+)>?",
		r"Original-Recipient:\s*(?:rfc822;)?\s*<?([^\s<>@]+@[^\s<>@]+)>?",
		r"Failed recipient:\s*<?([^\s<>@]+@[^\s<>@]+)>?",
		r"To:\s*<?([^\s<>@]+@[^\s<>@]+)>?",
		r"<([^\s<>@]+@[^\s<>@]+)>:?\s*(?:user unknown|mailbox unavailable|550|554|host not found)",
	]
	for p in patterns:
		m = re.search(p, text, re.IGNORECASE)
		if m:
			candidate = m.group(1).strip().strip("<>\"'.,;")
			if "@" in candidate and not is_bounce_or_automated_email(candidate):
				return candidate
	return None


def process_bounce_notification(doc: Communication) -> bool:
	"""Handle an incoming bounce notification:
	1. Mark incoming bounce communication as Bounced.
	2. Find the original outbound email that failed.
	3. Mark the outbound email as Bounced.
	4. Link bounce message to the original prospect without creating a Contact.
	"""
	try:
		doc.delivery_status = "Bounced"
		doc.db_set("delivery_status", "Bounced", update_modified=False)

		matched_comm = None
		# 1. Match via in_reply_to or references
		if getattr(doc, "in_reply_to", None) and frappe.db.exists("Communication", doc.in_reply_to):
			matched_comm = frappe.get_doc("Communication", doc.in_reply_to)

		# 2. Match via Message-ID quoted in bounce body
		if not matched_comm:
			text = f"{doc.text_content or ''}\n{doc.content or ''}"
			msg_ids = re.findall(r"Message-ID:\s*<([^>]+)>", text, re.IGNORECASE)
			for mid in msg_ids:
				parent = frappe.db.get_value(
					"Communication",
					{"message_id": ["in", [mid, f"<{mid}>"]]},
					["name", "reference_doctype", "reference_name", "delivery_status"],
					as_dict=True,
				)
				if parent:
					matched_comm = parent
					break

		# 3. Match via extracted bounced recipient
		failed_recipient = extract_bounced_recipient(doc)
		if not matched_comm and failed_recipient:
			outbound = frappe.db.get_all(
				"Communication",
				filters={
					"sent_or_received": "Sent",
					"recipients": ["like", f"%{failed_recipient}%"],
				},
				order_by="creation desc",
				limit=1,
				fields=["name", "reference_doctype", "reference_name", "delivery_status"],
			)
			if outbound:
				matched_comm = outbound[0]

		if matched_comm:
			# Update original outbound email delivery_status to "Bounced"
			frappe.db.set_value("Communication", matched_comm.name, "delivery_status", "Bounced", update_modified=False)
			doc.in_reply_to = matched_comm.name
			doc.db_set("in_reply_to", matched_comm.name, update_modified=False)

			ref_doctype = getattr(matched_comm, "reference_doctype", None)
			ref_name = getattr(matched_comm, "reference_name", None)
			if ref_doctype and ref_name and ref_doctype != "Communication" and not is_bounce_contact_name(ref_name):
				doc.reference_doctype = ref_doctype
				doc.reference_name = ref_name
				doc.db_set("reference_doctype", ref_doctype, update_modified=False)
				doc.db_set("reference_name", ref_name, update_modified=False)
		else:
			# No match: ensure it is NOT linked to any Contact
			if doc.reference_doctype == "Contact" and is_bounce_contact_name(doc.reference_name):
				doc.reference_doctype = None
				doc.reference_name = None
				doc.db_set("reference_doctype", None, update_modified=False)
				doc.db_set("reference_name", None, update_modified=False)

		frappe.publish_realtime("crm_tasks_updated")
		return True
	except Exception:
		return False


_is_automated_email_sender = is_bounce_or_automated_email


def on_comment_insert(doc: Comment, method: str | None = None):
	if not (doc.reference_doctype and doc.reference_name):
		return

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"] or doc.comment_type != "Comment":
		return

	if not _should_update_modified(doc):
		return

	if doc.reference_doctype and doc.reference_name:
		frappe.enqueue(update_modified_background, doctype=doc.reference_doctype, docname=doc.reference_name)


def update_modified_background(doctype: str, docname: str):
	frappe.db.set_value(doctype, docname, "modified", now(), update_modified=False)


def handle_incoming_email_reply(doc: Communication):
	"""Handle incoming email reply: match thread via In-Reply-To/References/Message-ID,
	associate with Contact/Lead/Task, mark original communication as Replied,
	and notify the assigned CRM user."""
	if doc.doctype != "Communication" or getattr(doc, "sent_or_received", "") != "Received":
		return

	if is_bounce_email(doc):
		process_bounce_notification(doc)
		return

	matched_comm = None
	# Case 1: doc.in_reply_to is already linked to parent Communication
	if getattr(doc, "in_reply_to", None) and frappe.db.exists("Communication", doc.in_reply_to):
		parent_candidates = frappe.db.get_all(
			"Communication",
			filters={"name": doc.in_reply_to},
			fields=["name", "reference_doctype", "reference_name", "sender", "recipients", "delivery_status"],
			limit=1,
		)
		if parent_candidates:
			matched_comm = parent_candidates[0]

	# Case 2: Match via Message-ID in references or In-Reply-To header
	if not matched_comm:
		in_reply_to_ids = []
		for header_val in [getattr(doc, "in_reply_to", None), getattr(doc, "references", None)]:
			if header_val:
				found = re.findall(r"<([^>]+)>", str(header_val))
				if found:
					in_reply_to_ids.extend(found)
				else:
					in_reply_to_ids.extend([h.strip() for h in str(header_val).split() if h.strip()])

		for msg_id in in_reply_to_ids:
			clean_id = msg_id.strip("<>")
			# 2a. Match on Communication.message_id
			parent_candidates = frappe.db.get_all(
				"Communication",
				filters={"message_id": ["in", [msg_id, f"<{msg_id}>", clean_id]]},
				fields=["name", "reference_doctype", "reference_name", "sender", "recipients", "delivery_status"],
				order_by="creation desc",
				limit=1,
			)
			if parent_candidates:
				matched_comm = parent_candidates[0]
				break

			# 2b. Match on Email Queue.message_id (outgoing emails store message_id in Email Queue)
			queue_parent = frappe.db.get_all(
				"Email Queue",
				filters={"message_id": ["in", [msg_id, f"<{msg_id}>", clean_id]], "communication": ["is", "set"]},
				fields=["communication"],
				order_by="creation desc",
				limit=1,
			)
			if queue_parent and queue_parent[0].communication:
				parent_candidates = frappe.db.get_all(
					"Communication",
					filters={"name": queue_parent[0].communication},
					fields=["name", "reference_doctype", "reference_name", "sender", "recipients", "delivery_status"],
					limit=1,
				)
				if parent_candidates:
					matched_comm = parent_candidates[0]
					break

			# 2c. Check if clean_id prefix matches a Communication name directly
			possible_name = clean_id.split("@", 1)[0]
			if frappe.db.exists("Communication", possible_name):
				parent_candidates = frappe.db.get_all(
					"Communication",
					filters={"name": possible_name},
					fields=["name", "reference_doctype", "reference_name", "sender", "recipients", "delivery_status"],
					limit=1,
				)
				if parent_candidates:
					matched_comm = parent_candidates[0]
					break

		if matched_comm and not getattr(doc, "in_reply_to", None):
			try:
				doc.in_reply_to = matched_comm.name
				doc.db_set("in_reply_to", matched_comm.name, update_modified=False)
			except Exception:
				pass

	if matched_comm:
		# Update original outgoing email's delivery_status to "Replied"
		frappe.db.set_value("Communication", matched_comm.name, "delivery_status", "Replied", update_modified=False)

		# Associate incoming email with the actual reference doc (overwrite if unset or if "Communication")
		ref_doctype = matched_comm.reference_doctype
		ref_name = matched_comm.reference_name

		if ref_doctype and ref_name and ref_doctype != "Communication":
			doc.reference_doctype = ref_doctype
			doc.reference_name = ref_name
			doc.db_set("reference_doctype", ref_doctype, update_modified=False)
			doc.db_set("reference_name", ref_name, update_modified=False)

		# Also check if contact can be resolved
		contact_name = None
		if doc.reference_doctype == "Contact" and not is_bounce_contact_name(doc.reference_name):
			contact_name = doc.reference_name
		elif doc.sender and not is_bounce_or_automated_email(doc.sender):
			contact_name = frappe.db.get_value("Contact", {"email_id": doc.sender.strip()}, "name")
			if not contact_name:
				c_match = frappe.db.sql("""
					SELECT c.name FROM `tabContact` c
					LEFT JOIN `tabContact Email` ce ON ce.parent = c.name
					WHERE c.email_id = %s OR ce.email_id = %s
					LIMIT 1
				""", (doc.sender.strip(), doc.sender.strip()))
				if c_match:
					contact_name = c_match[0][0]

		if contact_name and is_bounce_contact_name(contact_name):
			contact_name = None

		# If we have contact and reference is not set or not Contact, set it to Contact
		if contact_name and (not (doc.reference_doctype and doc.reference_name) or doc.reference_doctype == "Communication"):
			doc.reference_doctype = "Contact"
			doc.reference_name = contact_name
			doc.db_set("reference_doctype", "Contact", update_modified=False)
			doc.db_set("reference_name", contact_name, update_modified=False)

		# Notify assigned CRM user
		assigned_user = None
		if contact_name:
			assigned_user = frappe.db.get_value("CRM Daily Allocation", {"contact": contact_name}, "assigned_to")
			if not assigned_user:
				contact_assign = frappe.db.get_value("Contact", contact_name, "_assign")
				if contact_assign:
					try:
						assignees = json.loads(contact_assign) if isinstance(contact_assign, str) else contact_assign
						if assignees:
							assigned_user = assignees[0]
					except Exception:
						pass
		if not assigned_user and matched_comm.sender:
			assigned_user = frappe.db.get_value("User", {"email": matched_comm.sender}, "name")

		if assigned_user:
			notify_user_of_reply(assigned_user, doc, matched_comm)
		return

	# If no header match, fallback to match sender email with Contact
	if (not (doc.reference_doctype and doc.reference_name) or doc.reference_doctype == "Communication") and doc.sender and not is_bounce_or_automated_email(doc.sender):
		sender_email = doc.sender.strip()
		contact_match = frappe.db.sql("""
			SELECT c.name FROM `tabContact` c
			LEFT JOIN `tabContact Email` ce ON ce.parent = c.name
			WHERE c.email_id = %s OR ce.email_id = %s
			LIMIT 1
		""", (sender_email, sender_email))
		if contact_match:
			contact_name = contact_match[0][0]
			if is_bounce_contact_name(contact_name):
				return
			doc.reference_doctype = "Contact"
			doc.reference_name = contact_name
			doc.db_set("reference_doctype", "Contact", update_modified=False)
			doc.db_set("reference_name", contact_name, update_modified=False)

			# Also mark the most recent outgoing email to this contact as Replied
			recent_sent = frappe.db.get_all(
				"Communication",
				filters={"reference_doctype": "Contact", "reference_name": contact_name, "sent_or_received": "Sent"},
				order_by="creation desc",
				limit=1,
				fields=["name"],
			)
			if recent_sent:
				frappe.db.set_value("Communication", recent_sent[0].name, "delivery_status", "Replied", update_modified=False)

			assigned_user = frappe.db.get_value("CRM Daily Allocation", {"contact": contact_name}, "assigned_to")
			if not assigned_user:
				contact_assign = frappe.db.get_value("Contact", contact_name, "_assign")
				if contact_assign:
					try:
						assignees = json.loads(contact_assign) if isinstance(contact_assign, str) else contact_assign
						if assignees:
							assigned_user = assignees[0]
					except Exception:
						pass
			if assigned_user:
				notify_user_of_reply(assigned_user, doc, None)
			return


def notify_user_of_reply(user: str, comm_doc: Communication, parent_comm: dict | None = None):
	"""Publish realtime notification and create CRM Notification entry for assigned user."""
	try:
		frappe.publish_realtime(
			"crm_incoming_reply",
			{
				"communication": comm_doc.name,
				"subject": comm_doc.subject,
				"sender": comm_doc.sender,
				"sender_full_name": getattr(comm_doc, "sender_full_name", None) or comm_doc.sender,
				"reference_doctype": comm_doc.reference_doctype,
				"reference_name": comm_doc.reference_name,
			},
			user=user,
		)
		frappe.publish_realtime("crm_tasks_updated", user=user)
		frappe.publish_realtime("crm_notification", user=user)

		if frappe.db.exists("DocType", "CRM Notification"):
			sender_name = getattr(comm_doc, "sender_full_name", None) or comm_doc.sender or "Prospect"
			notif_text = f"Prospect {sender_name} replied: {comm_doc.subject or '(No Subject)'}"

			# Avoid duplicate notification for same communication and user
			if not frappe.db.exists("CRM Notification", {
				"to_user": user,
				"reference_doctype": comm_doc.reference_doctype,
				"reference_name": comm_doc.reference_name,
				"notification_text": notif_text,
			}):
				notif = frappe.new_doc("CRM Notification")
				notif.to_user = user
				notif.from_user = "Administrator"
				notif.type = "Mention"
				notif.notification_text = notif_text
				notif.reference_doctype = comm_doc.reference_doctype
				notif.reference_name = comm_doc.reference_name
				notif.flags.ignore_permissions = True
				notif.insert()
	except Exception:
		pass


def on_communication_insert(doc: Communication, method: str | None = None):
	if is_bounce_email(doc):
		process_bounce_notification(doc)
		return
	handle_incoming_email_reply(doc)
	create_lead_from_incoming_email(doc)


def on_communication_update(doc: Communication, method: str | None = None):
	if not (doc.reference_doctype and doc.reference_name):
		return

	if doc.reference_doctype == "Contact":
		frappe.db.set_value("Contact", doc.reference_name, "modified", now(), update_modified=False)
		frappe.publish_realtime("crm_tasks_updated")
		return

	if doc.reference_doctype not in ["CRM Lead", "CRM Deal"]:
		return

	should_update_modified = _should_update_modified(doc)
	status = _get_communication_status(doc)

	values = {}

	if should_update_modified:
		values["modified"] = now()

	if status:
		last_communication = frappe.get_last_doc(
			"Communication",
			{"reference_doctype": doc.reference_doctype, "reference_name": doc.reference_name},
		)
		if last_communication and last_communication.name == doc.name:
			values["communication_status"] = status

	if not values:
		return

	frappe.db.set_value(
		doc.reference_doctype,
		doc.reference_name,
		values,
		update_modified=False,
	)
