from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe import _


def validate(doc, method):
	update_deals_email_mobile_no(doc)
	sync_allocation_fields_on_contact_update(doc)


def sync_allocation_fields_on_contact_update(doc):
	name = getattr(doc, "name", None)
	if not name:
		return
	org_name = getattr(doc, "company_name", None) or ""
	from crm.api.daily_allocation import resolve_country_for_contact, get_timezone_for_country, format_timezone_label
	cntry = resolve_country_for_contact(name, org_name)
	tz = get_timezone_for_country(cntry) if cntry else "Not Available"
	tz_label = format_timezone_label(tz, cntry) if tz != "Not Available" else "Not Available"

	# Populate custom_country and custom_timezone on the Contact doc if available
	if cntry and not getattr(doc, "custom_country", None):
		doc.custom_country = cntry
	if tz_label and tz_label != "Not Available" and not getattr(doc, "custom_timezone", None):
		doc.custom_timezone = tz_label

	if frappe.db.exists("CRM Daily Allocation", {"contact": name}):
		full_name = doc.full_name or f"{doc.first_name or ''} {doc.last_name or ''}".strip() or name
		c_email = doc.email_id or (doc.email_ids[0].email_id if getattr(doc, "email_ids", None) else "") or ""
		c_phone = doc.mobile_no or (doc.phone_nos[0].phone if getattr(doc, "phone_nos", None) else "") or ""

		frappe.db.set_value(
			"CRM Daily Allocation",
			{"contact": name},
			{
				"contact_name": full_name,
				"organization": org_name,
				"email": c_email,
				"mobile_no": c_phone,
				"country": cntry or "",
				"timezone": tz if tz != "Not Available" else "",
			},
			update_modified=False,
		)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				"CRM Deal",
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


@frappe.whitelist()
def get_linked_deals(contact: str) -> list[dict[str, Any]]:
	"""The deals that list the contact and that the user can read, the last changed first."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return frappe.get_list(
		"CRM Deal",
		filters=[["CRM Contacts", "contact", "=", contact]],
		fields=[
			"name",
			"organization",
			"organization.organization_logo as organization_logo",
			"currency",
			"deal_value",
			"status",
			"email",
			"mobile_no",
			"deal_owner",
			"deal_owner.full_name as deal_owner_name",
			"modified",
		],
		order_by="modified desc",
		distinct=True,
	)


@frappe.whitelist()
def create_new(contact: str, field: str, value: str) -> bool:
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact_doc.email_ids) == 0 else 0}
		contact_doc.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact_doc.phone_nos) == 0 else 0}
		contact_doc.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact_doc.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str) -> bool:
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact_doc.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact_doc.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact_doc.save()
	return True


@frappe.whitelist()
def search_emails(txt: str | None = None) -> list[Any]:
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results


# -------------------------------------------------------------
# CONTACT ACTIVITY ENDPOINTS
# -------------------------------------------------------------

def _format_seconds(seconds: int | float | None) -> str:
	if not seconds:
		return "00:00"
	s = int(seconds)
	mins = s // 60
	secs = s % 60
	return f"{mins:02d}:{secs:02d}"


@frappe.whitelist()
def get_contact_activities(contact: str) -> dict[str, Any]:
	"""Return categorized activities (All, Emails, Calls, Notes, Meetings) for a Contact."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact {0} not found").format(contact), frappe.DoesNotExistError)

	contact_doc = frappe.get_doc("Contact", contact)
	emails = [e.email_id.strip() for e in contact_doc.email_ids if e.email_id]
	phones = [p.phone.strip() for p in contact_doc.phone_nos if p.phone]
	if contact_doc.mobile_no and contact_doc.mobile_no.strip() not in phones:
		phones.append(contact_doc.mobile_no.strip())
	if contact_doc.phone and contact_doc.phone.strip() not in phones:
		phones.append(contact_doc.phone.strip())

	# Find linked CRM Leads (by matching email or direct link)
	leads = []
	if emails:
		leads = frappe.get_all("CRM Lead", filters={"email": ["in", emails]}, pluck="name")

	# Attached call notes to exclude from standalone notes tab
	call_names_pre = set()
	for c in frappe.db.get_all("CRM Call Log", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="name"):
		call_names_pre.add(c)
	for c in frappe.db.get_all("Dynamic Link", filters={"link_doctype": "Contact", "link_name": contact, "parenttype": "CRM Call Log"}, pluck="parent"):
		call_names_pre.add(c)
	for l in leads:
		for c in frappe.db.get_all("CRM Call Log", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="name"):
			call_names_pre.add(c)
	for p in phones:
		cleaned_digits = "".join(ch for ch in p if ch.isdigit())
		if len(cleaned_digits) >= 7:
			suffix = cleaned_digits[-10:] if len(cleaned_digits) >= 10 else cleaned_digits
			for c in frappe.db.get_all("CRM Call Log", filters={"to": ["like", f"%{suffix}%"]}, pluck="name"):
				call_names_pre.add(c)
			for c in frappe.db.get_all("CRM Call Log", filters={"from": ["like", f"%{suffix}%"]}, pluck="name"):
				call_names_pre.add(c)
		else:
			for c in frappe.db.get_all("CRM Call Log", filters={"to": p}, pluck="name"):
				call_names_pre.add(c)
			for c in frappe.db.get_all("CRM Call Log", filters={"from": p}, pluck="name"):
				call_names_pre.add(c)

	call_attached_notes = set()
	raw_calls = []
	if call_names_pre:
		raw_calls = frappe.get_all(
			"CRM Call Log",
			filters={"name": ["in", list(call_names_pre)]},
			fields=[
				"name", "caller", "receiver", "from", "to", "duration",
				"start_time", "end_time", "status", "type", "recording_url",
				"creation", "note", "owner"
			],
			order_by="creation desc",
		)
		for c in raw_calls:
			if c.note:
				call_attached_notes.add(c.note)

	# ---------------------------------------------------------
	# 1. NOTES (FCRM Note)
	# ---------------------------------------------------------
	note_names = set()
	for n in frappe.db.get_all("FCRM Note", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="name"):
		note_names.add(n)
	for n in frappe.db.get_all("Dynamic Link", filters={"link_doctype": "Contact", "link_name": contact, "parenttype": "FCRM Note"}, pluck="parent"):
		note_names.add(n)
	for l in leads:
		for n in frappe.db.get_all("FCRM Note", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="name"):
			note_names.add(n)

	# Exclude notes that are attached to call logs so they only appear inside the Call card
	note_names = note_names - call_attached_notes

	raw_notes = []
	if note_names:
		raw_notes = frappe.get_all(
			"FCRM Note",
			filters={"name": ["in", list(note_names)]},
			fields=["name", "title", "content", "pinned", "pinned_by", "pinned_on", "owner", "creation", "modified"],
			order_by="creation desc",
		)

	# ---------------------------------------------------------
	# 2. MEETINGS (Event)
	# ---------------------------------------------------------
	event_names = set()
	for e in frappe.db.get_all("Event", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="name"):
		event_names.add(e)
	for e in frappe.db.get_all("Event Participants", filters={"reference_doctype": "Contact", "reference_docname": contact}, pluck="parent"):
		event_names.add(e)
	for email in emails:
		for e in frappe.db.get_all("Event Participants", filters={"email": email}, pluck="parent"):
			event_names.add(e)
	for e in frappe.db.get_all("Dynamic Link", filters={"link_doctype": "Contact", "link_name": contact, "parenttype": "Event"}, pluck="parent"):
		event_names.add(e)
	for l in leads:
		for e in frappe.db.get_all("Event", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="name"):
			event_names.add(e)
		for e in frappe.db.get_all("Event Participants", filters={"reference_doctype": "CRM Lead", "reference_docname": l}, pluck="parent"):
			event_names.add(e)

	raw_events = []
	event_participants_map = {}
	if event_names:
		raw_events = frappe.get_all(
			"Event",
			filters={"name": ["in", list(event_names)]},
			fields=["name", "subject", "starts_on", "ends_on", "owner", "status", "description", "creation"],
			order_by="starts_on desc",
		)
		# Batch fetch event participants in 1 query
		parts = frappe.get_all(
			"Event Participants",
			filters={"parent": ["in", list(event_names)]},
			fields=["parent", "reference_doctype", "reference_docname", "email"],
		)
		for p in parts:
			lbl = p.email or p.reference_docname
			if lbl:
				event_participants_map.setdefault(p.parent, []).append(lbl)

	# ---------------------------------------------------------
	# 3. EMAILS (Communication)
	# ---------------------------------------------------------
	comm_names = set()
	for c in frappe.db.get_all(
		"Communication",
		filters={
			"reference_doctype": "Contact",
			"reference_name": contact,
			"communication_medium": ["in", ["Email", ""]],
			"communication_type": ["in", ["Communication", "Automated Message"]],
		},
		pluck="name",
	):
		comm_names.add(c)
	for c in frappe.db.get_all("Communication Link", filters={"link_doctype": "Contact", "link_name": contact}, pluck="parent"):
		comm_names.add(c)
	for l in leads:
		for c in frappe.db.get_all(
			"Communication",
			filters={
				"reference_doctype": "CRM Lead",
				"reference_name": l,
				"communication_medium": ["in", ["Email", ""]],
				"communication_type": ["in", ["Communication", "Automated Message"]],
			},
			pluck="name",
		):
			comm_names.add(c)
		for c in frappe.db.get_all("Communication Link", filters={"link_doctype": "CRM Lead", "link_name": l}, pluck="parent"):
			comm_names.add(c)
	for email in emails:
		for c in frappe.db.sql(
			"SELECT name FROM `tabCommunication` WHERE (sender = %s OR recipients LIKE %s) AND communication_type IN ('Communication', 'Automated Message') AND (communication_medium = 'Email' OR communication_medium IS NULL OR communication_medium = '')",
			(email, f"%{email}%"),
			as_dict=True,
		):
			comm_names.add(c.name)

	raw_comms = []
	attachments_by_comm = {}
	if comm_names:
		raw_comms = frappe.get_all(
			"Communication",
			filters={
				"name": ["in", list(comm_names)],
				"communication_medium": ["in", ["Email", ""]],
				"communication_type": ["in", ["Communication", "Automated Message"]],
			},
			fields=[
				"name", "sender", "sender_full_name", "recipients", "cc", "bcc",
				"subject", "content", "communication_date", "creation", "delivery_status",
				"sent_or_received", "in_reply_to", "message_id"
			],
			order_by="creation desc",
		)
		# Batch fetch attachments in 1 single query instead of N queries
		all_attached = frappe.get_all(
			"File",
			filters={"attached_to_doctype": "Communication", "attached_to_name": ["in", list(comm_names)]},
			fields=["name", "file_name", "file_url", "file_size", "attached_to_name"],
		)
		for att in all_attached:
			attachments_by_comm.setdefault(att.attached_to_name, []).append(att)

	# ---------------------------------------------------------
	# 4. STATUS UPDATES (CRM Prospect Status Update)
	# ---------------------------------------------------------
	raw_status_updates = []
	if frappe.db.table_exists("CRM Prospect Status Update"):
		raw_status_updates = frappe.db.sql(
			"""
			SELECT name, contact, task, main_status, connected_to, activity_status,
				   next_action, follow_up_date, call_back_date, description, creation, owner
			FROM `tabCRM Prospect Status Update`
			WHERE contact = %(contact)s
			ORDER BY creation DESC
			""",
			{"contact": contact},
			as_dict=True,
		)

	# ---------------------------------------------------------
	# BATCH USER LOOKUPS & CALL NOTES LOOKUPS (1 query each)
	# ---------------------------------------------------------
	all_users_to_fetch = set()
	for n in raw_notes:
		if n.owner: all_users_to_fetch.add(n.owner)
	for c in raw_calls:
		call_type = c.type or "Outgoing"
		uid = c.caller if call_type == "Outgoing" else c.receiver
		if uid: all_users_to_fetch.add(uid)
		if c.owner: all_users_to_fetch.add(c.owner)
	for e in raw_events:
		if e.owner: all_users_to_fetch.add(e.owner)
	for su in raw_status_updates:
		if su.get("owner"): all_users_to_fetch.add(su["owner"])

	user_full_names = {}
	if all_users_to_fetch:
		for u in frappe.get_all("User", filters={"name": ["in", list(all_users_to_fetch)]}, fields=["name", "full_name"]):
			user_full_names[u.name] = u.full_name or u.name

	call_notes_map = {}
	note_ids_for_calls = [c.note for c in raw_calls if c.note]
	if note_ids_for_calls:
		for fn in frappe.get_all("FCRM Note", filters={"name": ["in", note_ids_for_calls]}, fields=["name", "content"]):
			call_notes_map[fn.name] = fn.content or ""

	# ---------------------------------------------------------
	# BUILD OUTPUT LISTS
	# ---------------------------------------------------------
	notes_list = []
	for n in raw_notes:
		author = user_full_names.get(n.owner, n.owner or "User")
		notes_list.append({
			"activity_type": "note",
			"name": n.name,
			"title": n.title or _("Note"),
			"content": n.content or "",
			"owner": n.owner,
			"author_name": author,
			"creation": str(n.creation),
			"modified": str(n.modified),
			"date": str(n.creation),
			"pinned": bool(n.pinned),
			"pinned_by": n.pinned_by,
			"pinned_on": str(n.pinned_on) if n.pinned_on else None,
			"activity_title": _("{0} added a note").format(author),
		})

	calls_list = []
	twilio_recording_enabled = bool(frappe.db.get_single_value("CRM Twilio Settings", "record_calls"))
	for c in raw_calls:
		dur = c.duration or 0
		call_type = c.type or "Outgoing"
		user_id = c.caller if call_type == "Outgoing" else c.receiver
		user_name = user_full_names.get(user_id) or user_id or c.owner or "User"
		phone_no = c.to if call_type == "Outgoing" else getattr(c, "from")

		recording_path = ""
		if c.recording_url:
			if c.recording_url.startswith(("/files/", "/private/files/")):
				recording_path = c.recording_url
			else:
				recording_path = f"/api/method/crm.integrations.api.get_recording_url?call_log_name={c.name}"

		if recording_path:
			rec_status = "available"
		elif twilio_recording_enabled and (c.status in ("Completed", "In Progress", "Ringing")) and dur > 0:
			rec_status = "processing"
		else:
			rec_status = "none"

		calls_list.append({
			"activity_type": "call",
			"name": c.name,
			"type": call_type,
			"caller": c.caller,
			"receiver": c.receiver,
			"user": user_id,
			"user_name": user_name,
			"phone": phone_no or (phones[0] if phones else ""),
			"prospect_name": contact_doc.full_name,
			"duration": dur,
			"duration_formatted": _format_seconds(dur),
			"status": c.status or "Completed",
			"start_time": str(c.start_time or c.creation),
			"date": str(c.start_time or c.creation),
			"creation": str(c.creation),
			"note": call_notes_map.get(c.note, str(c.note) if c.note else ""),
			"recording_url": recording_path,
			"recording_status": rec_status,
			"has_recording": bool(recording_path),
			"activity_title": (
				_("{0} called this prospect").format(user_name)
				if call_type == "Outgoing"
				else _("{0} received a call").format(user_name)
			),
		})

	meetings_list = []
	for e in raw_events:
		organizer = user_full_names.get(e.owner, e.owner or "User")
		part_labels = event_participants_map.get(e.name, [contact_doc.full_name] if contact_doc.full_name else [])
		meetings_list.append({
			"activity_type": "meeting",
			"name": e.name,
			"title": e.subject or _("Meeting"),
			"starts_on": str(e.starts_on),
			"ends_on": str(e.ends_on),
			"date": str(e.starts_on or e.creation),
			"creation": str(e.creation),
			"owner": e.owner,
			"organizer_name": organizer,
			"status": e.status or "Open",
			"description": e.description or "",
			"participants": part_labels,
			"activity_title": _("Meeting scheduled"),
		})

	emails_list = []
	all_activity_emails = []
	for idx, c in enumerate(raw_comms):
		attached_files = attachments_by_comm.get(c.name, [])
		raw_html = c.content or ""
		clean_text = re.sub(r"<[^>]+>", " ", raw_html).strip()
		clean_text = " ".join(clean_text.split())
		snippet = clean_text[:140] + ("..." if len(clean_text) > 140 else "")

		sender_display = c.sender_full_name or c.sender or "User"
		is_incoming = (getattr(c, "sent_or_received", "") == "Received")
		activity_title = (
			_("Prospect replied to your email")
			if is_incoming
			else _("{0} sent an email to this prospect").format(sender_display)
		)

		base_email_item = {
			"activity_type": "email",
			"name": c.name,
			"sender": c.sender or "",
			"sender_full_name": sender_display,
			"recipients": c.recipients or "",
			"cc": c.cc or "",
			"bcc": c.bcc or "",
			"subject": c.subject or _("(No Subject)"),
			"snippet": snippet,
			"date": str(c.communication_date or c.creation),
			"creation": str(c.creation),
			"delivery_status": c.delivery_status or ("Received" if is_incoming else "Sending"),
			"sent_or_received": c.sent_or_received or ("Received" if is_incoming else "Sent"),
			"in_reply_to": getattr(c, "in_reply_to", None) or "",
			"attachments": attached_files,
			"activity_title": activity_title,
		}

		# In Emails tab: retain full content for emails
		full_email_item = dict(base_email_item)
		full_email_item["content"] = raw_html
		emails_list.append(full_email_item)

		# In All Activity tab: omit duplicate 50KB HTML body to save 500KB+ JSON payload
		summary_email_item = dict(base_email_item)
		summary_email_item["content"] = ""
		all_activity_emails.append(summary_email_item)

	status_updates_list = []
	for su in raw_status_updates:
		author_name = user_full_names.get(su["owner"], su["owner"] or "User")
		title_st = su.get("activity_status") or su.get("main_status")
		status_updates_list.append({
			"activity_type": "status_update",
			"name": su["name"],
			"contact": su["contact"],
			"task": su.get("task"),
			"main_status": su.get("main_status"),
			"connected_to": su.get("connected_to"),
			"activity_status": su.get("activity_status"),
			"next_action": su.get("next_action"),
			"follow_up_date": str(su.get("follow_up_date") or ""),
			"call_back_date": str(su.get("call_back_date") or ""),
			"description": su.get("description") or "",
			"date": str(su["creation"]),
			"creation": str(su["creation"]),
			"owner": su["owner"],
			"author_name": author_name,
			"activity_title": _("{0} updated status to {1}").format(author_name, title_st),
		})

	# ---------------------------------------------------------
	# COMBINE ALL CHRONOLOGICALLY (NEWEST FIRST)
	# ---------------------------------------------------------
	all_activities = sorted(
		notes_list + calls_list + meetings_list + all_activity_emails + status_updates_list,
		key=lambda x: str(x.get("date") or x.get("creation") or ""),
		reverse=True,
	)

	return {
		"all_activities": all_activities,
		"emails": emails_list,
		"calls": calls_list,
		"notes": notes_list,
		"meetings": meetings_list,
		"status_updates": status_updates_list,
		"counts": {
			"all_activity": len(all_activities),
			"emails": len(emails_list),
			"calls": len(calls_list),
			"notes": len(notes_list),
			"meetings": len(meetings_list),
			"status_updates": len(status_updates_list),
		},
	}


@frappe.whitelist()
def add_contact_note(contact: str, title: str | None = None, content: str | None = None, pinned: int | bool = 0) -> dict[str, Any]:
	"""Create a new Note linked to a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not content and not title:
		frappe.throw(_("Note title or content is required."))

	note_doc = frappe.new_doc("FCRM Note")
	note_doc.title = title or _("Note")
	note_doc.content = content or ""
	note_doc.reference_doctype = "Contact"
	note_doc.reference_docname = contact
	note_doc.pinned = 1 if pinned else 0
	note_doc.flags.ignore_permissions = True
	note_doc.insert()
	frappe.db.commit()

	return {"success": True, "name": note_doc.name}


@frappe.whitelist()
def log_contact_call(
	contact: str,
	call_type: str = "Outgoing",
	phone: str | None = None,
	duration: int | str = 0,
	status: str = "Completed",
	note: str | None = None,
	start_time: str | None = None,
) -> dict[str, Any]:
	"""Log a Call associated with a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_doc("Contact", contact)
	phone_val = phone or (contact_doc.phone_nos[0].phone if contact_doc.phone_nos else "") or "0000000000"

	try:
		dur_val = int(duration)
	except (ValueError, TypeError):
		dur_val = 0

	call_doc = frappe.new_doc("CRM Call Log")
	call_doc.type = call_type
	call_doc.status = status
	call_doc.duration = dur_val
	call_doc.reference_doctype = "Contact"
	call_doc.reference_docname = contact

	current_user = frappe.session.user
	user_phone = frappe.db.get_value("User", current_user, "phone") or "+10000000000"

	if call_type == "Outgoing":
		call_doc.caller = current_user
		call_doc.receiver = None
		call_doc.to = phone_val
		setattr(call_doc, "from", user_phone)
	else:
		call_doc.receiver = current_user
		call_doc.caller = None
		setattr(call_doc, "from", phone_val)
		call_doc.to = user_phone

	if start_time:
		call_doc.start_time = start_time

	call_doc.flags.ignore_permissions = True
	call_doc.insert()

	if note:
		note_doc = frappe.new_doc("FCRM Note")
		note_doc.title = _("Call with {0}").format(contact_doc.full_name)
		note_doc.content = note
		note_doc.reference_doctype = "CRM Call Log"
		note_doc.reference_docname = call_doc.name
		note_doc.flags.ignore_permissions = True
		note_doc.insert()
		frappe.db.set_value("CRM Call Log", call_doc.name, "note", note_doc.name)

	frappe.db.commit()

	if status == "Completed":
		try:
			from crm.api.daily_allocation import check_and_advance_task_to_in_progress
			check_and_advance_task_to_in_progress(contact=contact, phone=phone_val)
		except Exception as e:
			frappe.logger().error(f"Error advancing task status: {e}")

	return {"success": True, "name": call_doc.name}


@frappe.whitelist()
def schedule_contact_meeting(
	contact: str,
	title: str,
	starts_on: str,
	ends_on: str,
	description: str | None = None,
	status: str = "Open",
	location: str | None = None,
	participants: Any = None,
) -> dict[str, Any]:
	"""Schedule a Meeting (Event) associated with a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact_doc = frappe.get_doc("Contact", contact)
	contact_email = contact_doc.email_id or (contact_doc.email_ids[0].email_id if contact_doc.email_ids else "")

	event = frappe.new_doc("Event")
	event.subject = title
	event.event_category = "Meeting"
	event.event_type = "Public"
	event.starts_on = starts_on
	event.ends_on = ends_on
	event.status = status
	event.description = description or ""
	event.reference_doctype = "Contact"
	event.reference_docname = contact

	event.append("event_participants", {
		"reference_doctype": "Contact",
		"reference_docname": contact,
		"email": contact_email,
	})

	if participants:
		part_list = participants if isinstance(participants, list) else [p.strip() for p in str(participants).split(",") if p.strip()]
		for p in part_list:
			if p != contact_email:
				event.append("event_participants", {"email": p})

	event.flags.ignore_permissions = True
	event.insert()
	frappe.db.commit()

	return {"success": True, "name": event.name}


@frappe.whitelist()
def send_contact_email(
	contact: str,
	recipient: str,
	subject: str,
	content: str,
	cc: str | None = None,
	bcc: str | None = None,
) -> dict[str, Any]:
	"""Disallow direct email sending from Contact detail page."""
	frappe.throw(
		_("Email composition from Contact detail page is disabled. Please send emails from My Tasks workspace."),
		frappe.PermissionError,
	)


def ensure_contact_custom_fields():
	"""Ensure custom_is_dropped, country, timezone, social links and lead columns exist in tabContact."""
	try:
		if (
			not frappe.db.has_column("Contact", "custom_is_dropped")
			or not frappe.db.has_column("Contact", "custom_country")
			or not frappe.db.has_column("Contact", "custom_timezone")
			or not frappe.db.has_column("Contact", "custom_linkedin")
			or not frappe.db.has_column("Contact", "custom_upwork")
			or not frappe.db.has_column("Contact", "custom_website")
			or not frappe.db.has_column("Contact", "custom_converted_lead")
		):
			from crm.install import add_contact_custom_fields
			add_contact_custom_fields()
	except Exception:
		pass


@frappe.whitelist()
def backfill_contact_country_and_timezone():
	"""Populate custom_country and custom_timezone for contacts where available."""
	ensure_contact_custom_fields()
	from crm.api.daily_allocation import resolve_country_for_contact, get_timezone_for_country, format_timezone_label
	contacts = frappe.db.sql("""
		SELECT name, company_name, custom_country, custom_timezone
		FROM `tabContact`
		WHERE (custom_country IS NULL OR custom_country = '')
		   OR (custom_timezone IS NULL OR custom_timezone = '')
		LIMIT 200
	""", as_dict=True)

	updated = 0
	for c in contacts:
		cntry = resolve_country_for_contact(c.name, c.company_name)
		tz = get_timezone_for_country(cntry) if cntry else "Not Available"
		tz_label = format_timezone_label(tz, cntry) if tz != "Not Available" else "Not Available"

		vals = {}
		if cntry and not c.custom_country:
			vals["custom_country"] = cntry
		if tz_label and tz_label != "Not Available" and not c.custom_timezone:
			vals["custom_timezone"] = tz_label

		if vals:
			frappe.db.set_value("Contact", c.name, vals, update_modified=False)
			updated += 1
	if updated:
		frappe.db.commit()
	return {"updated": updated}


@frappe.whitelist()
def get_contact_tab_counts() -> dict[str, Any]:
	"""Dynamic counts for Unassigned, Assigned, Dropped contact tabs."""
	ensure_contact_custom_fields()
	user = frappe.session.user
	from crm.api.security import is_admin_only, get_contact_permission_conditions
	is_admin = is_admin_only(user)

	if is_admin:
		unassigned_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NULL OR _assign = '' OR _assign = '[]')
		""")[0][0]

		assigned_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NOT NULL AND _assign != '' AND _assign != '[]')
		""")[0][0]

		dropped_count = frappe.db.sql("""
			SELECT COUNT(*) FROM `tabContact`
			WHERE custom_is_dropped = 1
		""")[0][0]
	else:
		cond = get_contact_permission_conditions(user)
		base_where = f"AND ({cond})" if cond else ""

		unassigned_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NULL OR _assign = '' OR _assign = '[]')
			  {base_where}
		""")[0][0]

		assigned_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM `tabContact`
			WHERE (custom_is_dropped = 0 OR custom_is_dropped IS NULL)
			  AND (_assign IS NOT NULL AND _assign != '' AND _assign != '[]')
			  {base_where}
		""")[0][0]

		dropped_count = frappe.db.sql(f"""
			SELECT COUNT(*) FROM `tabContact`
			WHERE custom_is_dropped = 1
			  {base_where}
		""")[0][0]

	return {
		"unassigned": unassigned_count,
		"assigned": assigned_count,
		"dropped": dropped_count,
		"is_admin": is_admin,
	}


@frappe.whitelist()
def mark_contacts_dropped(names: Any, dropped: int = 1) -> dict[str, Any]:
	"""Mark selected contacts as Dropped (dropped=1) or Restore them to Unassigned (dropped=0)."""
	from crm.api.security import is_admin_or_manager
	if not is_admin_or_manager():
		frappe.throw(_("Permission denied. Only Administrator or Manager can mark contacts as dropped."), frappe.PermissionError)

	if isinstance(names, str):
		try:
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]

	if not names:
		frappe.throw(_("Please select at least one contact."))

	dropped_val = 1 if int(dropped) else 0

	for name in names:
		if frappe.db.exists("Contact", name):
			frappe.db.set_value("Contact", name, "custom_is_dropped", dropped_val)
			if dropped_val == 1:
				frappe.db.delete("CRM Daily Allocation", {"contact": name})
			elif dropped_val == 0:
				# Restoring to Unassigned: clear any assignments
				try:
					from frappe.desk.form import assign_to
					assign_to.clear("Contact", name, ignore_permissions=True)
				except Exception:
					pass

	frappe.db.commit()
	try:
		frappe.publish_realtime("crm_tasks_updated", {"dropped": dropped_val}, after_commit=True)
	except Exception:
		pass
	msg = (
		_("{0} contact(s) marked as Dropped.").format(len(names))
		if dropped_val
		else _("{0} contact(s) restored to Unassigned.").format(len(names))
	)
	return {"success": True, "count": len(names), "message": msg}


@frappe.whitelist()
def create_prospect_status_update(
	contact: str,
	main_status: str,
	description: str,
	connected_to: str | None = None,
	activity_status: str | None = None,
	next_action: str | None = None,
	follow_up_date: str | None = None,
	call_back_date: str | None = None,
	task_name: str | int | None = None,
) -> dict[str, Any]:
	"""Create a new CRM Prospect Status Update record."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact {0} not found").format(contact), frappe.DoesNotExistError)

	if not description or len(description.strip()) < 15:
		frappe.throw(_("Description must be at least 15 characters long."))

	valid_main = ("Contacted", "Not Contacted", "Not Valid")
	if main_status not in valid_main:
		frappe.throw(_("Invalid Main Status. Must be one of: {0}").format(", ".join(valid_main)))

	# Ensure doctype table exists
	if not frappe.db.table_exists("CRM Prospect Status Update"):
		frappe.reload_doc("fcrm", "doctype", "crm_prospect_status_update", force=True)

	doc = frappe.new_doc("CRM Prospect Status Update")
	doc.contact = contact
	doc.task = task_name or None
	doc.main_status = main_status
	doc.connected_to = connected_to or "Decision Maker (already confirmed)"
	doc.description = description.strip()

	if main_status == "Contacted":
		valid_activities = ("Portfolio Sent", "Requirement Gathered", "Call Back", "Not Interested", "Follow Up")
		if activity_status and activity_status not in valid_activities:
			frappe.throw(_("Invalid Activity Status. Must be one of: {0}").format(", ".join(valid_activities)))
		doc.activity_status = activity_status or None
		doc.next_action = next_action or None
		doc.follow_up_date = follow_up_date or None
		doc.call_back_date = call_back_date or None
	else:
		doc.activity_status = None
		doc.next_action = None
		doc.follow_up_date = None
		doc.call_back_date = None

	doc.insert(ignore_permissions=True)

	# Synchronize linked task status if task exists
	target_task = None
	if task_name and frappe.db.exists("CRM Daily Allocation", task_name):
		target_task = task_name
	else:
		t = frappe.db.get_value("CRM Daily Allocation", {"contact": contact}, "name")
		if t:
			target_task = t

	new_task_status = None
	if main_status == "Contacted":
		if activity_status == "Call Back":
			new_task_status = "Callback"
		elif activity_status == "Follow Up":
			new_task_status = "Follow up"
		elif activity_status == "Not Interested":
			new_task_status = "Not Interested"
		elif activity_status in ("Portfolio Sent", "Requirement Gathered"):
			new_task_status = "In Progress"
		else:
			new_task_status = "In Progress"
	elif main_status == "Not Interested":
		new_task_status = "Not Interested"

	if target_task and new_task_status:
		task_vals = {"status": new_task_status}
		if follow_up_date:
			task_vals["follow_up_date"] = follow_up_date
		elif call_back_date:
			task_vals["follow_up_date"] = call_back_date
		task_vals["notes"] = description.strip()[:250]
		try:
			frappe.db.set_value("CRM Daily Allocation", target_task, task_vals, update_modified=True)
		except Exception:
			pass

	frappe.db.commit()

	author_name = frappe.db.get_value("User", doc.owner, "full_name") or doc.owner or "User"
	return {
		"name": doc.name,
		"contact": doc.contact,
		"task": doc.task,
		"main_status": doc.main_status,
		"connected_to": doc.connected_to,
		"activity_status": doc.activity_status,
		"next_action": doc.next_action,
		"follow_up_date": str(doc.follow_up_date) if doc.follow_up_date else "",
		"call_back_date": str(doc.call_back_date) if doc.call_back_date else "",
		"description": doc.description,
		"creation": str(doc.creation),
		"owner": doc.owner,
		"author_name": author_name,
		"task_status": new_task_status,
	}


@frappe.whitelist()
def get_prospect_status_history(contact: str) -> list[dict[str, Any]]:
	"""Get all status update history records for a contact in chronological order (newest first)."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not frappe.db.table_exists("CRM Prospect Status Update"):
		return []

	records = frappe.db.sql(
		"""
		SELECT name, contact, task, main_status, connected_to, activity_status,
			   next_action, follow_up_date, call_back_date, description, creation, owner
		FROM `tabCRM Prospect Status Update`
		WHERE contact = %(contact)s
		ORDER BY creation DESC
		""",
		{"contact": contact},
		as_dict=True,
	)

	history = []
	for r in records:
		author_name = frappe.db.get_value("User", r.owner, "full_name") or r.owner or "User"
		history.append({
			"name": r.name,
			"contact": r.contact,
			"task": r.task,
			"main_status": r.main_status,
			"connected_to": r.connected_to,
			"activity_status": r.activity_status,
			"next_action": r.next_action,
			"follow_up_date": str(r.follow_up_date) if r.follow_up_date else "",
			"call_back_date": str(r.call_back_date) if r.call_back_date else "",
			"description": r.description,
			"creation": str(r.creation),
			"owner": r.owner,
			"author_name": author_name,
		})

	return history


@frappe.whitelist()
def convert_contact_to_lead(contact: str, task_name: str | None = None) -> dict[str, Any]:
	"""Convert a Contact / Prospect into a CRM Lead."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact {0} not found").format(contact), frappe.DoesNotExistError)

	ensure_contact_custom_fields()
	contact_doc = frappe.get_doc("Contact", contact)

	# 1. Check if already converted via custom_converted_lead
	if getattr(contact_doc, "custom_converted_lead", None) and frappe.db.exists("CRM Lead", contact_doc.custom_converted_lead):
		return {
			"success": True,
			"already_converted": True,
			"lead_name": contact_doc.custom_converted_lead,
			"message": _("This prospect has already been converted to Lead {0}.").format(contact_doc.custom_converted_lead),
		}

	# 2. Check if a Lead exists with the exact email
	lead_name = None
	if contact_doc.email_id:
		existing = frappe.db.get_value("CRM Lead", {"email": contact_doc.email_id}, "name")
		if existing:
			lead_name = existing

	if not lead_name:
		# Also check Dynamic Link
		dl = frappe.db.get_value(
			"Dynamic Link",
			{"parenttype": "Contact", "parent": contact, "link_doctype": "CRM Lead"},
			"link_name",
		)
		if dl and frappe.db.exists("CRM Lead", dl):
			lead_name = dl

	if lead_name:
		if hasattr(contact_doc, "custom_converted_lead") or frappe.db.has_column("Contact", "custom_converted_lead"):
			frappe.db.set_value("Contact", contact, "custom_converted_lead", lead_name, update_modified=False)
			frappe.db.commit()
		return {
			"success": True,
			"already_converted": True,
			"lead_name": lead_name,
			"message": _("This prospect is already associated with Lead {0}.").format(lead_name),
		}

	# 3. Create a new CRM Lead doc
	first_name = contact_doc.first_name or contact_doc.full_name or "Lead"
	last_name = contact_doc.last_name or ""
	lead_title = contact_doc.full_name or f"{first_name} {last_name}".strip()

	email = contact_doc.email_id or ""
	if not email and contact_doc.email_ids:
		for em in contact_doc.email_ids:
			if getattr(em, "is_primary", 0) and em.email_id:
				email = em.email_id
				break
		if not email and contact_doc.email_ids:
			email = contact_doc.email_ids[0].email_id

	phone = contact_doc.mobile_no or contact_doc.phone or ""
	if not phone and contact_doc.phone_nos:
		for ph in contact_doc.phone_nos:
			if getattr(ph, "is_primary_mobile_no", 0) and ph.phone:
				phone = ph.phone
				break
		if not phone and contact_doc.phone_nos:
			phone = contact_doc.phone_nos[0].phone

	org_name = contact_doc.company_name or ""
	job_title = contact_doc.designation or ""

	# If organization, designation, email, or phone is empty on contact, fall back to task data
	if task_name and frappe.db.exists("CRM Daily Allocation", task_name):
		task_vals = frappe.db.get_value("CRM Daily Allocation", task_name, ["organization", "designation", "email", "mobile_no"], as_dict=True)
		if task_vals:
			if not org_name and task_vals.get("organization"):
				org_name = task_vals["organization"]
			if not job_title and task_vals.get("designation"):
				job_title = task_vals["designation"]
			if not email and task_vals.get("email"):
				email = task_vals["email"]
			if not phone and task_vals.get("mobile_no"):
				phone = task_vals["mobile_no"]

	default_status = "New Lead"
	if not frappe.db.exists("CRM Lead Status", default_status):
		lead_statuses = frappe.get_all("CRM Lead Status", pluck="name", limit=1)
		default_status = lead_statuses[0] if lead_statuses else None

	lead_data = {
		"doctype": "CRM Lead",
		"first_name": first_name,
		"last_name": last_name,
		"lead_name": lead_title,
		"email": email,
		"mobile_no": phone,
		"phone": phone,
		"organization": org_name,
		"job_title": job_title,
		"website": getattr(contact_doc, "custom_website", "") or "",
		"linkedin": getattr(contact_doc, "custom_linkedin", "") or "",
		"lead_owner": frappe.session.user,
		"status": default_status,
	}

	lead = frappe.get_doc(lead_data)
	lead.insert(ignore_permissions=True)

	# 4. Link back to Contact
	if hasattr(contact_doc, "custom_converted_lead") or frappe.db.has_column("Contact", "custom_converted_lead"):
		frappe.db.set_value("Contact", contact, "custom_converted_lead", lead.name, update_modified=False)

	# Add Dynamic Link if not already present
	has_link = frappe.db.exists(
		"Dynamic Link",
		{"parenttype": "Contact", "parent": contact, "link_doctype": "CRM Lead", "link_name": lead.name},
	)
	if not has_link:
		try:
			dl_doc = frappe.new_doc("Dynamic Link")
			dl_doc.parent = contact
			dl_doc.parenttype = "Contact"
			dl_doc.parentfield = "links"
			dl_doc.link_doctype = "CRM Lead"
			dl_doc.link_name = lead.name
			dl_doc.insert(ignore_permissions=True)
		except Exception:
			pass

	frappe.db.commit()

	return {
		"success": True,
		"already_converted": False,
		"lead_name": lead.name,
		"message": _("Prospect successfully converted to Lead {0}.").format(lead.name),
	}


@frappe.whitelist()
def update_contact_social_links(
	contact: str,
	linkedin: str | None = None,
	upwork: str | None = None,
	website: str | None = None,
) -> dict[str, Any]:
	"""Update social links (LinkedIn, Upwork, Website) for a Contact."""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	ensure_contact_custom_fields()

	vals = {}
	if linkedin is not None:
		vals["custom_linkedin"] = linkedin.strip()
	if upwork is not None:
		vals["custom_upwork"] = upwork.strip()
	if website is not None:
		vals["custom_website"] = website.strip()

	if vals:
		frappe.db.set_value("Contact", contact, vals, update_modified=True)
		frappe.db.commit()

	return {
		"success": True,
		"custom_linkedin": frappe.db.get_value("Contact", contact, "custom_linkedin") or "",
		"custom_upwork": frappe.db.get_value("Contact", contact, "custom_upwork") or "",
		"custom_website": frappe.db.get_value("Contact", contact, "custom_website") or "",
	}
