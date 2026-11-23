# Copyright (c) 2026, Smrikaam and contributors
# For license information, please see license.txt

import datetime
import hashlib
import json
import re
import secrets
import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, validate_email_address


# ==============================================================================
# SECURE PUBLIC BOOKING SUBMISSION API
# ==============================================================================

def _get_header(key, default=None):
	try:
		if getattr(frappe, "request", None) and hasattr(frappe.request, "headers"):
			return frappe.request.headers.get(key, default)
	except Exception:
		pass
	return default


def _set_status(code):
	try:
		if hasattr(frappe.local, "response") and isinstance(frappe.local.response, dict):
			frappe.local.response.http_status_code = code
	except Exception:
		pass


@frappe.whitelist(allow_guest=True)
def create_booking(**kwargs):
	"""
	Publicly accessible endpoint for external websites to submit bookings.
	Requires website-specific API key and secret authentication.
	"""
	# Extract parameters from kwargs, form_dict, or JSON body
	params = {}
	if hasattr(frappe.local, "form_dict"):
		params.update(frappe.local.form_dict)
	params.update(kwargs)

	if getattr(frappe, "request", None) and getattr(frappe.request, "is_json", False):
		try:
			json_data = frappe.request.get_json() or {}
			if isinstance(json_data, dict):
				params.update(json_data)
		except Exception:
			pass

	# 1. Retrieve Authentication Credentials
	api_key = (
		_get_header("X-Booking-API-Key")
		or _get_header("X-API-Key")
		or params.get("api_key")
	)
	api_secret = (
		_get_header("X-Booking-API-Secret")
		or _get_header("X-API-Secret")
		or params.get("api_secret")
	)

	source_id = (
		_get_header("X-Booking-Source-ID")
		or params.get("source_id")
	)

	if not source_id:
		_set_status(400)
		return {
			"status": "error",
			"error_code": "MISSING_SOURCE_ID",
			"message": _("Source ID is required."),
		}

	# 2. Validate Source Existence & State
	if not frappe.db.exists("Website Booking Source", source_id):
		_set_status(404)
		return {
			"status": "error",
			"error_code": "SOURCE_NOT_FOUND",
			"message": _("Registered booking source not found."),
		}

	source = frappe.get_doc("Website Booking Source", source_id)

	if not source.is_active:
		_set_status(403)
		return {
			"status": "error",
			"error_code": "SOURCE_INACTIVE",
			"message": _("Booking source is currently inactive."),
		}

	# 3. Authenticate Website Credentials
	if not api_key or not api_secret:
		_set_status(401)
		return {
			"status": "error",
			"error_code": "UNAUTHORIZED",
			"message": _("Missing API key or secret in request headers or payload."),
		}

	if source.api_key != api_key or not source.verify_secret(api_secret):
		_set_status(401)
		return {
			"status": "error",
			"error_code": "INVALID_CREDENTIALS",
			"message": _("Invalid API credentials for this source."),
		}

	# 4. Domain Validation
	request_domain = (
		_get_header("X-Request-Domain")
		or _get_header("Origin")
		or _get_header("Referer")
		or params.get("request_domain")
	)

	if request_domain and source.domain:
		cleaned_req_domain = clean_domain_string(request_domain)
		cleaned_source_domain = clean_domain_string(source.domain)
		# Allow matching domain or standard localhost/dev patterns
		is_dev = cleaned_req_domain in ["localhost", "127.0.0.1", "0.0.0.0"]
		if not is_dev and cleaned_req_domain != cleaned_source_domain:
			# If subdomain, check if base domain matches
			if not cleaned_req_domain.endswith("." + cleaned_source_domain):
				_set_status(403)
				return {
					"status": "error",
					"error_code": "DOMAIN_MISMATCH",
					"message": _("Request origin does not match the registered domain for this source."),
				}

	# 5. Rate Limiting Check (e.g. max 120 submissions per minute per source)
	cache = frappe.cache()
	rate_key = f"rate_limit_booking_{source_id}"
	current_hits = cache.get_value(rate_key) or 0
	if current_hits > 120:
		_set_status(429)
		return {
			"status": "error",
			"error_code": "RATE_LIMIT_EXCEEDED",
			"message": _("Too many requests. Please try again later."),
		}
	cache.set_value(rate_key, current_hits + 1, expires_in_sec=60)

	# 6. Validate Required Fields
	booking_ref = (params.get("booking_reference") or "").strip()
	if not booking_ref:
		prefix = "BK-" + (source.source_name[:3].upper() if source.source_name else "SRC")
		random_suffix = frappe.generate_hash(length=6).upper()
		timestamp_str = frappe.utils.now_datetime().strftime("%Y%m%d%H%M")
		booking_ref = f"{prefix}-{timestamp_str}-{random_suffix}"

	customer_name = (params.get("customer_name") or "").strip()
	email = (params.get("email") or "").strip()
	appointment_date = (params.get("appointment_date") or "").strip()
	appointment_time = (params.get("appointment_time") or "").strip()

	missing_fields = []
	if not customer_name:
		missing_fields.append("customer_name")
	if not email:
		missing_fields.append("email")
	if not appointment_date:
		missing_fields.append("appointment_date")
	if not appointment_time:
		missing_fields.append("appointment_time")

	if missing_fields:
		_set_status(400)
		return {
			"status": "error",
			"error_code": "MISSING_REQUIRED_FIELDS",
			"message": _("Missing mandatory fields: {0}").format(", ".join(missing_fields)),
		}

	# 7. Validate Email
	try:
		validate_email_address(email, throw=True)
	except Exception:
		_set_status(400)
		return {
			"status": "error",
			"error_code": "INVALID_EMAIL",
			"message": _("Invalid customer email address format."),
		}

	# 8. Validate Appointment Date & Time
	try:
		parsed_date = datetime.date.fromisoformat(appointment_date)
	except Exception:
		_set_status(400)
		return {
			"status": "error",
			"error_code": "INVALID_DATE_FORMAT",
			"message": _("Invalid appointment date. Expected ISO format (YYYY-MM-DD)."),
		}

	# 9. Idempotency / Duplicate Booking Check
	if frappe.db.exists("Website Booking", booking_ref):
		_set_status(409)
		return {
			"status": "error",
			"error_code": "DUPLICATE_BOOKING",
			"message": _("A booking with reference '{0}' has already been processed.").format(booking_ref),
			"booking_reference": booking_ref,
		}

	# 10. Store Booking Record
	submitted_at = params.get("submitted_at")
	if submitted_at:
		try:
			submitted_at = get_datetime(submitted_at)
		except Exception:
			submitted_at = now_datetime()
	else:
		submitted_at = now_datetime()

	booking_doc = frappe.new_doc("Website Booking")
	booking_doc.booking_reference = booking_ref
	booking_doc.source = source.name
	booking_doc.source_name = source.source_name
	booking_doc.customer_name = customer_name
	booking_doc.company_name = (params.get("company_name") or "").strip()
	booking_doc.email = email
	booking_doc.phone = (params.get("phone") or "").strip()
	booking_doc.interested_service = (params.get("interested_service") or "").strip()
	booking_doc.appointment_date = parsed_date
	booking_doc.appointment_time = appointment_time
	booking_doc.timezone = (params.get("timezone") or "UTC").strip()
	booking_doc.message = (params.get("message") or "").strip()
	booking_doc.page_url = (params.get("page_url") or "").strip()
	booking_doc.submitted_at = submitted_at
	booking_doc.booking_status = "New"
	booking_doc.insert(ignore_permissions=True)

	# 11. Update Source Status & Counters
	source.last_successful_booking = now_datetime()
	if source.connection_status in ["Pending Setup", "Testing", "Connection Failed"]:
		source.connection_status = "Connected"
	source.save(ignore_permissions=True)

	# 12. Record Activity History
	log_booking_activity(
		booking_id=booking_doc.name,
		activity_type="Created",
		subject=_("Booking created via website API"),
		details=_("Received from source {0} ({1}) with reference {2}").format(
			source.source_name, source.domain, booking_ref
		),
		by_user="Administrator",
	)

	# 13. Create CRM Notifications for Authorized Users
	send_booking_notification(booking_doc, source)

	frappe.db.commit()

	return {
		"status": "success",
		"message": _("Booking submitted successfully."),
		"booking_id": booking_doc.name,
		"booking_reference": booking_doc.booking_reference,
		"source": source.source_name,
	}


# ==============================================================================
# BOOKING HUB DASHBOARD & SUMMARY APIS (AUTHORIZED CRM USERS)
# ==============================================================================

@frappe.whitelist()
def get_booking_hub_summary():
	"""
	Returns real-time dashboard counts and registered website sources.
	Strictly calculates counts from database records.
	"""
	# Summary card metrics
	total_bookings = frappe.db.count("Website Booking")
	new_bookings = frappe.db.count("Website Booking", {"booking_status": "New"})
	upcoming_appointments = frappe.db.count(
		"Website Booking",
		{"booking_status": ["in", ["Upcoming", "Confirmed", "Rescheduled"]]},
	)
	completed_appointments = frappe.db.count(
		"Website Booking",
		{"booking_status": "Completed"},
	)
	cancelled_appointments = frappe.db.count(
		"Website Booking",
		{"booking_status": "Cancelled"},
	)

	# Fetch all registered website sources
	sources = frappe.get_all(
		"Website Booking Source",
		fields=[
			"name",
			"source_id",
			"source_name",
			"domain",
			"website_type",
			"description",
			"connection_status",
			"is_active",
			"credential_reference",
			"last_successful_booking",
			"total_bookings",
			"new_bookings",
			"creation",
		],
		order_by="creation asc",
	)

	# Recalculate per-source booking counts from live records to ensure 100% accuracy
	for src in sources:
		src["total_bookings"] = frappe.db.count("Website Booking", {"source": src["name"]})
		src["new_bookings"] = frappe.db.count(
			"Website Booking", {"source": src["name"], "booking_status": "New"}
		)

	counts = {
		"total_bookings": total_bookings,
		"new_bookings": new_bookings,
		"upcoming_appointments": upcoming_appointments,
		"completed_appointments": completed_appointments,
		"cancelled_appointments": cancelled_appointments,
	}

	return {
		"counts": counts,
		"metrics": counts,
		"sources": sources,
	}


@frappe.whitelist()
def get_bookings(
	source_id: str | None = None,
	booking_status: str | None = None,
	search: str | None = None,
	start: int = 0,
	page_length: int = 20,
	sort_by: str = "creation",
	sort_order: str = "desc",
):
	"""
	Server-side paginated list of bookings with filtering and search.
	"""
	start = int(start or 0)
	page_length = min(int(page_length or 20), 100)

	valid_sort_fields = {
		"creation",
		"appointment_date",
		"customer_name",
		"company_name",
		"booking_status",
		"source",
	}
	if sort_by not in valid_sort_fields:
		sort_by = "creation"

	sort_order = "desc" if str(sort_order).lower() == "desc" else "asc"

	filters = {}
	if source_id and source_id != "all":
		filters["source"] = source_id

	if booking_status and booking_status != "all":
		filters["booking_status"] = booking_status

	or_filters = []
	if search and search.strip():
		s = f"%{search.strip()}%"
		or_filters = [
			["Website Booking", "customer_name", "like", s],
			["Website Booking", "company_name", "like", s],
			["Website Booking", "email", "like", s],
			["Website Booking", "phone", "like", s],
			["Website Booking", "booking_reference", "like", s],
			["Website Booking", "interested_service", "like", s],
		]

	if or_filters:
		total_count = len(
			frappe.get_all(
				"Website Booking",
				filters=filters,
				or_filters=or_filters,
				pluck="name",
			)
		)
	else:
		total_count = frappe.db.count("Website Booking", filters=filters)

	items = frappe.get_all(
		"Website Booking",
		fields=[
			"name",
			"booking_reference",
			"source",
			"source_name",
			"customer_name",
			"company_name",
			"email",
			"phone",
			"interested_service",
			"appointment_date",
			"appointment_time",
			"timezone",
			"booking_status",
			"assigned_to",
			"page_url",
			"submitted_at",
			"creation",
			"message",
			"internal_notes",
		],
		filters=filters,
		or_filters=or_filters if or_filters else None,
		order_by=f"{sort_by} {sort_order}",
		start=start,
		page_length=page_length,
	)

	return {
		"items": items,
		"bookings": items,
		"total_count": total_count,
		"start": start,
		"page_length": page_length,
	}


@frappe.whitelist()
def get_booking_detail(booking_id: str | None = None, booking_reference: str | None = None):
	"""
	Retrieves detailed booking information including source and full activity log.
	"""
	booking_id = booking_id or booking_reference
	if not booking_id:
		frappe.throw(_("Booking ID is required"), frappe.ValidationError)

	if not frappe.db.exists("Website Booking", booking_id):
		# Try lookup by booking_reference
		by_ref = frappe.db.get_value("Website Booking", {"booking_reference": booking_id}, "name")
		if by_ref:
			booking_id = by_ref
		else:
			frappe.throw(_("Booking not found"), frappe.DoesNotExistError)

	booking = frappe.get_doc("Website Booking", booking_id).as_dict()

	# Attach source details
	if booking.get("source"):
		source_doc = frappe.get_doc("Website Booking Source", booking["source"])
		booking["source_details"] = {
			"source_id": source_doc.source_id,
			"source_name": source_doc.source_name,
			"domain": source_doc.domain,
			"website_type": source_doc.website_type,
			"connection_status": source_doc.connection_status,
		}

	# Retrieve activity logs
	activities = frappe.get_all(
		"Website Booking Activity",
		fields=["name", "activity_type", "subject", "details", "by_user", "timestamp"],
		filters={"booking": booking_id},
		order_by="timestamp desc",
	)
	booking["activities"] = activities

	return {
		"booking": booking,
		"activities": activities,
		**booking,
	}


# ==============================================================================
# BOOKING ACTIONS (STATUS, RESCHEDULE, ASSIGNMENT, NOTES)
# ==============================================================================

@frappe.whitelist()
def update_booking_status(
	booking_id: str | None = None,
	status: str | None = None,
	booking_reference: str | None = None,
	note: str | None = None,
):
	"""
	Updates booking status (New, Upcoming, Confirmed, Completed, Cancelled).
	"""
	booking_id = booking_id or booking_reference
	allowed_statuses = ["New", "Upcoming", "Confirmed", "Completed", "Cancelled", "Rescheduled"]
	if status not in allowed_statuses:
		frappe.throw(_("Invalid booking status: {0}").format(status))

	booking = frappe.get_doc("Website Booking", booking_id)
	old_status = booking.booking_status
	booking.booking_status = status
	if note:
		booking.internal_notes = (
			f"{booking.internal_notes}\n[{now_datetime().strftime('%Y-%m-%d %H:%M')}] {note}"
			if booking.internal_notes
			else f"[{now_datetime().strftime('%Y-%m-%d %H:%M')}] {note}"
		)
	booking.save()

	log_booking_activity(
		booking_id=booking_id,
		activity_type="Status Change",
		subject=_("Status changed from {0} to {1}").format(old_status, status),
		details=note or "",
		by_user=frappe.session.user,
	)

	return {"status": "success", "booking_status": status}


@frappe.whitelist()
def reschedule_booking(
	booking_id: str | None = None,
	appointment_date: str | None = None,
	appointment_time: str | None = None,
	booking_reference: str | None = None,
	new_date: str | None = None,
	new_time: str | None = None,
	timezone: str | None = None,
	note: str | None = None,
	reason: str | None = None,
):
	"""
	Reschedules an appointment to a new date and time.
	"""
	booking_id = booking_id or booking_reference
	appointment_date = appointment_date or new_date
	appointment_time = appointment_time or new_time
	note = note or reason

	booking = frappe.get_doc("Website Booking", booking_id)
	old_date = booking.appointment_date
	old_time = booking.appointment_time

	booking.appointment_date = appointment_date
	booking.appointment_time = appointment_time
	if timezone:
		booking.timezone = timezone
	booking.booking_status = "Rescheduled"
	booking.save()

	details_msg = _("Rescheduled from {0} at {1} to {2} at {3}").format(
		old_date, old_time, appointment_date, appointment_time
	)
	if note:
		details_msg += f". Note: {note}"

	log_booking_activity(
		booking_id=booking_id,
		activity_type="Rescheduled",
		subject=_("Appointment rescheduled"),
		details=details_msg,
		by_user=frappe.session.user,
	)

	return {"status": "success", "appointment_date": appointment_date, "appointment_time": appointment_time}


@frappe.whitelist()
def assign_booking(
	booking_id: str | None = None,
	assigned_to: str | None = None,
	booking_reference: str | None = None,
):
	"""
	Assigns booking to a CRM user and logs the action.
	"""
	booking_id = booking_id or booking_reference
	booking = frappe.get_doc("Website Booking", booking_id)
	old_assigned = booking.assigned_to
	booking.assigned_to = assigned_to
	booking.save()

	user_name = frappe.get_value("User", assigned_to, "full_name") or assigned_to

	log_booking_activity(
		booking_id=booking_id,
		activity_type="Assignment",
		subject=_("Assigned to {0}").format(user_name),
		details=_("Reassigned from {0} to {1}").format(old_assigned or "None", user_name),
		by_user=frappe.session.user,
	)

	# Notify assigned user
	if assigned_to and assigned_to != frappe.session.user:
		notify_doc = frappe.new_doc("CRM Notification")
		notify_doc.to_user = assigned_to
		notify_doc.from_user = frappe.session.user
		notify_doc.type = "Assignment"
		notify_doc.notification_text = _("You have been assigned booking <b>{0}</b> for <b>{1}</b>").format(
			booking.booking_reference, booking.customer_name
		)
		notify_doc.reference_doctype = "Website Booking"
		notify_doc.reference_name = booking.name
		notify_doc.read = 0
		notify_doc.insert(ignore_permissions=True)

	return {"status": "success", "assigned_to": assigned_to}


@frappe.whitelist()
def add_booking_note(
	booking_id: str | None = None,
	note: str | None = None,
	booking_reference: str | None = None,
):
	"""
	Appends an internal note to the booking.
	"""
	booking_id = booking_id or booking_reference
	if not note or not note.strip():
		frappe.throw(_("Note content cannot be empty."))

	booking = frappe.get_doc("Website Booking", booking_id)
	user_label = frappe.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	formatted_note = f"[{now_datetime().strftime('%Y-%m-%d %H:%M')} by {user_label}]:\n{note.strip()}"

	booking.internal_notes = (
		f"{booking.internal_notes}\n\n{formatted_note}"
		if booking.internal_notes
		else formatted_note
	)
	booking.save()

	log_booking_activity(
		booking_id=booking_id,
		activity_type="Note",
		subject=_("Internal note added"),
		details=note.strip(),
		by_user=frappe.session.user,
	)

	return {"status": "success", "internal_notes": booking.internal_notes}


# ==============================================================================
# SOURCE MANAGEMENT APIS (ADMINISTRATOR)
# ==============================================================================

@frappe.whitelist()
def add_source(
	source_name: str,
	domain: str,
	website_type: str = "Corporate",
	description: str | None = None,
	is_active: int | bool = 1,
):
	"""
	Add a new website source and generate secure API credentials.
	Returns the source details along with raw api_secret once for integration setup.
	"""
	# Check permissions
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" not in roles and "Sales Manager" not in roles:
		frappe.throw(_("Not authorized to manage website sources."), frappe.PermissionError)

	if not source_name or not source_name.strip():
		frappe.throw(_("Source Name is mandatory."))

	if not domain or not domain.strip():
		frappe.throw(_("Website Domain is mandatory."))

	cleaned_domain = clean_domain_string(domain)
	if not is_valid_domain(cleaned_domain):
		frappe.throw(_("Invalid domain format: {0}. Please enter a valid domain like example.com.").format(domain))

	# Duplicate domain check
	existing_domain = frappe.db.get_value("Website Booking Source", {"domain": cleaned_domain}, "name")
	if existing_domain:
		frappe.throw(_("A website source with domain '{0}' is already registered.").format(cleaned_domain))

	# Normalize website_type to match DocType select options
	if website_type:
		if "corporate" in website_type.lower():
			norm_type = "Corporate"
		elif "product" in website_type.lower():
			norm_type = "Product"
		else:
			norm_type = "Other"
	else:
		norm_type = "Corporate"

	# Generate unique source_id
	base_slug = frappe.scrub(source_name)
	source_id = f"src_{base_slug}_{secrets.token_hex(3)}"
	while frappe.db.exists("Website Booking Source", source_id):
		source_id = f"src_{base_slug}_{secrets.token_hex(4)}"

	source = frappe.new_doc("Website Booking Source")
	source.source_id = source_id
	source.source_name = source_name.strip()
	source.domain = cleaned_domain
	source.website_type = norm_type
	source.description = (description or "").strip()
	source.is_active = 1 if is_active in [1, "1", True, "true"] else 0
	source.connection_status = "Pending Setup"

	# Generate API key & secret
	api_key, raw_api_secret = source.generate_credentials()
	source.insert()

	source_dict = {
		"source_id": source.source_id,
		"source_name": source.source_name,
		"domain": source.domain,
		"website_type": source.website_type,
		"connection_status": source.connection_status,
		"is_active": source.is_active,
		"api_key": api_key,
		"api_secret": raw_api_secret,  # Provided ONCE for administrator setup
		"credential_reference": source.credential_reference,
	}

	return {
		"status": "success",
		"message": _("Website source created successfully."),
		"source": source_dict,
		**source_dict,
	}


@frappe.whitelist()
def update_source(
	source_id: str,
	source_name: str | None = None,
	domain: str | None = None,
	website_type: str | None = None,
	description: str | None = None,
	is_active: int | bool | None = None,
):
	"""
	Updates source configuration.
	"""
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" not in roles and "Sales Manager" not in roles:
		frappe.throw(_("Not authorized to manage website sources."), frappe.PermissionError)

	source = frappe.get_doc("Website Booking Source", source_id)

	if source_name and source_name.strip():
		source.source_name = source_name.strip()

	if domain and domain.strip():
		cleaned_domain = clean_domain_string(domain)
		if not is_valid_domain(cleaned_domain):
			frappe.throw(_("Invalid domain format."))
		# Check duplicate
		duplicate = frappe.db.get_value(
			"Website Booking Source",
			{"domain": cleaned_domain, "name": ["!=", source.name]},
			"name",
		)
		if duplicate:
			frappe.throw(_("Domain '{0}' is already in use by another source.").format(cleaned_domain))
		source.domain = cleaned_domain

	if website_type:
		if "corporate" in website_type.lower():
			source.website_type = "Corporate"
		elif "product" in website_type.lower():
			source.website_type = "Product"
		else:
			source.website_type = "Other"

	if description is not None:
		source.description = description.strip()

	if is_active is not None:
		source.is_active = 1 if is_active in [1, "1", True, "true"] else 0

	source.save()
	return {"status": "success", "message": _("Source updated successfully.")}


@frappe.whitelist()
def regenerate_credentials(source_id: str):
	"""
	Regenerates API credentials for a source and returns the new secret once.
	"""
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" not in roles and "Sales Manager" not in roles:
		frappe.throw(_("Not authorized to regenerate credentials."), frappe.PermissionError)

	source = frappe.get_doc("Website Booking Source", source_id)
	api_key, raw_api_secret = source.generate_credentials()
	source.connection_status = "Pending Setup"
	source.save()

	return {
		"status": "success",
		"message": _("Credentials regenerated successfully."),
		"api_key": api_key,
		"api_secret": raw_api_secret,
		"credential_reference": source.credential_reference,
	}


@frappe.whitelist()
def revoke_credentials(source_id: str):
	"""
	Revokes API credentials for a source, immediately disabling external API access.
	"""
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" not in roles and "Sales Manager" not in roles:
		frappe.throw(_("Not authorized to revoke credentials."), frappe.PermissionError)

	source = frappe.get_doc("Website Booking Source", source_id)
	source.api_secret_hash = ""
	source.connection_status = "Inactive"
	source.credential_reference = "REVOKED"
	source.save()

	return {"status": "success", "message": _("Credentials revoked.")}


@frappe.whitelist()
def test_connection(source_id: str):
	"""
	Performs a health and validation check on the source.
	"""
	if not frappe.db.exists("Website Booking Source", source_id):
		frappe.throw(_("Source not found."))

	source = frappe.get_doc("Website Booking Source", source_id)

	if not source.is_active:
		return {
			"status": "error",
			"connection_status": "Inactive",
			"message": _("Source is marked inactive."),
		}

	if not source.api_key or not source.api_secret_hash:
		source.connection_status = "Connection Failed"
		source.save()
		return {
			"status": "error",
			"connection_status": "Connection Failed",
			"message": _("Source has missing or revoked credentials."),
		}

	# Connection test passed: mark as Connected
	source.connection_status = "Connected"
	source.save()

	return {
		"status": "success",
		"connection_status": "Connected",
		"message": _("Connection test successful. Source is ready to receive bookings."),
		"source": {
			"source_id": source.source_id,
			"source_name": source.source_name,
			"domain": source.domain,
			"connection_status": source.connection_status,
		},
	}


@frappe.whitelist()
def toggle_source_status(source_id: str, is_active: int | bool):
	"""
	Enables or disables a website source without destructive data deletion.
	"""
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" not in roles and "Sales Manager" not in roles:
		frappe.throw(_("Not authorized to modify sources."), frappe.PermissionError)

	source = frappe.get_doc("Website Booking Source", source_id)
	source.is_active = 1 if is_active in [1, "1", True, "true"] else 0
	if not source.is_active:
		source.connection_status = "Inactive"
	else:
		source.connection_status = "Connected" if source.last_successful_booking else "Pending Setup"
	source.save()

	return {
		"status": "success",
		"is_active": source.is_active,
		"connection_status": source.connection_status,
	}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def clean_domain_string(domain_str: str) -> str:
	if not domain_str:
		return ""
	s = domain_str.strip().lower()
	if s.startswith("https://"):
		s = s[8:]
	elif s.startswith("http://"):
		s = s[7:]
	s = s.split("/")[0].split(":")[0]
	if s.startswith("www."):
		s = s[4:]
	return s


def is_valid_domain(domain_str: str) -> bool:
	if not domain_str:
		return False
	# Standard domain regex allowing subdomains and localhost
	if domain_str in ["localhost", "127.0.0.1"]:
		return True
	pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
	return bool(re.match(pattern, domain_str))


def log_booking_activity(booking_id, activity_type, subject, details="", by_user=None):
	"""
	Creates a discrete activity log for a booking.
	"""
	try:
		activity = frappe.new_doc("Website Booking Activity")
		activity.booking = booking_id
		activity.activity_type = activity_type
		activity.subject = subject
		activity.details = details or ""
		activity.by_user = by_user or frappe.session.user or "Administrator"
		activity.timestamp = now_datetime()
		activity.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error("Failed to log booking activity", "Booking Hub")


def send_booking_notification(booking_doc, source_doc):
	"""
	Generates CRM notifications for authorized users when a new booking arrives.
	Avoids duplicate notifications.
	"""
	# Target recipients: Sales Managers & System Managers
	recipients = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Sales Manager", "System Manager"]], "parenttype": "User"},
		fields=["parent as user"],
		distinct=True,
	)

	recipient_users = {r["user"] for r in recipients if r["user"] not in ["Administrator", "Guest"]}
	# Fallback if no specific role found
	if not recipient_users:
		recipient_users = {"Administrator"}

	notification_text = _("New appointment booking from <b>{0}</b> via <b>{1}</b>").format(
		booking_doc.customer_name, source_doc.source_name
	)

	for user in recipient_users:
		# Idempotency: Avoid duplicate notification for same booking
		if frappe.db.exists(
			"CRM Notification",
			{
				"to_user": user,
				"reference_doctype": "Website Booking",
				"reference_name": booking_doc.name,
			},
		):
			continue

		try:
			notif = frappe.new_doc("CRM Notification")
			notif.to_user = user
			notif.from_user = "Administrator"
			notif.type = "Assignment"
			notif.notification_text = notification_text
			notif.reference_doctype = "Website Booking"
			notif.reference_name = booking_doc.name
			notif.read = 0
			notif.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(f"Failed to send booking notification to {user}", "Booking Hub")
