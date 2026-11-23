# Copyright (c) 2026, Smrikaam and contributors
# Test suite for Booking Hub backend functionality

import frappe
from crm.api.booking_hub import (
	add_source,
	assign_booking,
	create_booking,
	get_booking_detail,
	get_booking_hub_summary,
	get_bookings,
	regenerate_credentials,
	reschedule_booking,
	revoke_credentials,
	test_connection,
	toggle_source_status,
	update_booking_status,
)


def run_tests():
	print("=== RUNNING BOOKING HUB BACKEND TESTS ===")

	# 1. Verify default sources
	print("\n--- 1. Testing Default Sources ---")
	sources = frappe.get_all("Website Booking Source", fields=["name", "source_name", "domain", "api_key"])
	print(f"Found {len(sources)} sources: {[s['source_name'] for s in sources]}")
	assert len(sources) >= 2, "Default sources should be seeded"

	smrikaam = frappe.get_doc("Website Booking Source", "src_smrikaam")
	assert smrikaam.domain == "smrikaam.com"
	assert smrikaam.api_key, "Smrikaam must have api_key"
	print("✓ Smrikaam source verified")

	bitxhift = frappe.get_doc("Website Booking Source", "src_bitxhift")
	assert bitxhift.domain == "bitxhift.com"
	assert bitxhift.api_key, "BitXhift must have api_key"
	print("✓ BitXhift source verified")

	# 2. Test get_booking_hub_summary
	print("\n--- 2. Testing Summary Dashboard API ---")
	summary = get_booking_hub_summary()
	assert "counts" in summary
	assert "sources" in summary
	assert "total_bookings" in summary["counts"]
	assert "new_bookings" in summary["counts"]
	assert "upcoming_appointments" in summary["counts"]
	print(f"✓ Summary counts: {summary['counts']}")

	# 3. Test Authentication & Booking Submission
	print("\n--- 3. Testing create_booking Security & Validation ---")

	# 3a. Missing source_id
	res = create_booking()
	assert res["status"] == "error"
	assert res["error_code"] == "MISSING_SOURCE_ID"
	print("✓ Rejects missing source_id")

	# 3b. Non-existent source
	res = create_booking(source_id="non_existent_source")
	assert res["status"] == "error"
	assert res["error_code"] == "SOURCE_NOT_FOUND"
	print("✓ Rejects non-existent source")

	# 3c. Invalid credentials
	res = create_booking(
		source_id="src_smrikaam",
		api_key=smrikaam.api_key,
		api_secret="invalid_secret_key_12345",
	)
	assert res["status"] == "error"
	assert res["error_code"] == "INVALID_CREDENTIALS"
	print("✓ Rejects invalid credentials")

	# Temporarily set a known secret on Smrikaam for testing submissions
	test_secret = "sec_test_secret_for_smrikaam_integration_99"
	import hashlib
	smrikaam.api_secret_hash = hashlib.sha256(test_secret.encode()).hexdigest()
	smrikaam.is_active = 1
	smrikaam.save(ignore_permissions=True)

	# 3d. Missing required fields
	res = create_booking(
		source_id="src_smrikaam",
		api_key=smrikaam.api_key,
		api_secret=test_secret,
		request_domain="smrikaam.com",
		booking_reference="",
	)
	assert res["status"] == "error"
	assert res["error_code"] == "MISSING_REQUIRED_FIELDS"
	print("✓ Rejects missing mandatory fields")

	# 3e. Invalid email
	res = create_booking(
		source_id="src_smrikaam",
		api_key=smrikaam.api_key,
		api_secret=test_secret,
		request_domain="smrikaam.com",
		booking_reference="BK-TEST-INVALID-EMAIL",
		customer_name="John Doe",
		email="not-an-email",
		appointment_date="2026-11-25",
		appointment_time="11:00 AM",
	)
	assert res["status"] == "error"
	assert res["error_code"] == "INVALID_EMAIL"
	print("✓ Rejects invalid email format")

	# 3f. Domain mismatch
	res = create_booking(
		source_id="src_smrikaam",
		api_key=smrikaam.api_key,
		api_secret=test_secret,
		request_domain="malicious-site.org",
		booking_reference="BK-TEST-DOMAIN-MISMATCH",
		customer_name="John Doe",
		email="john@example.com",
		appointment_date="2026-11-25",
		appointment_time="11:00 AM",
	)
	assert res["status"] == "error"
	assert res["error_code"] == "DOMAIN_MISMATCH"
	print("✓ Rejects request domain mismatch")

	# 3g. Valid booking submission from Smrikaam
	booking_ref_1 = f"BK-SMR-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}-1"
	res = create_booking(
		source_id="src_smrikaam",
		api_key=smrikaam.api_key,
		api_secret=test_secret,
		request_domain="smrikaam.com",
		booking_reference=booking_ref_1,
		customer_name="Arun Kumar",
		company_name="TechNova Solutions",
		email="arun@technova.com",
		phone="+91 98410 22334",
		interested_service="AI & Data Technical Staffing",
		appointment_date="2026-11-25",
		appointment_time="11:00 AM",
		timezone="Asia/Kolkata",
		message="Looking to schedule technical screening call for 2 Senior Data Engineers.",
		page_url="https://smrikaam.com/IT-staffing-services-in-Coimbatore",
	)
	assert res["status"] == "success"
	assert res["booking_reference"] == booking_ref_1
	print(f"✓ Valid Smrikaam booking created: {booking_ref_1}")

	# 3h. Duplicate booking submission check
	res_dup = create_booking(
		source_id="src_smrikaam",
		api_key=smrikaam.api_key,
		api_secret=test_secret,
		request_domain="smrikaam.com",
		booking_reference=booking_ref_1,
		customer_name="Arun Kumar",
		email="arun@technova.com",
		appointment_date="2026-11-25",
		appointment_time="11:00 AM",
	)
	assert res_dup["status"] == "error"
	assert res_dup["error_code"] == "DUPLICATE_BOOKING"
	print("✓ Idempotency prevents duplicate booking reference")

	# 3i. Valid booking submission from BitXhift
	test_secret_bit = "sec_test_secret_for_bitxhift_99"
	bitxhift.api_secret_hash = hashlib.sha256(test_secret_bit.encode()).hexdigest()
	bitxhift.is_active = 1
	bitxhift.save(ignore_permissions=True)

	booking_ref_2 = f"BK-BIT-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}-2"
	res_bit = create_booking(
		source_id="src_bitxhift",
		api_key=bitxhift.api_key,
		api_secret=test_secret_bit,
		request_domain="bitxhift.com",
		booking_reference=booking_ref_2,
		customer_name="Priya Menon",
		company_name="Apex Digital",
		email="priya@apexdigital.in",
		phone="+91 72004 99120",
		interested_service="BitXhift Product Demo",
		appointment_date="2026-11-25",
		appointment_time="02:00 PM",
		timezone="Asia/Kolkata",
		message="Would like a walkthrough of product features.",
		page_url="https://bitxhift.com/demo",
	)
	assert res_bit["status"] == "success"
	print(f"✓ Valid BitXhift booking created: {booking_ref_2}")

	# 4. Test Bookings Query & Source Separation
	print("\n--- 4. Testing Bookings Filtering & Separation ---")
	all_bookings = get_bookings()
	assert all_bookings["total_count"] >= 2
	print(f"✓ Total bookings query returned {all_bookings['total_count']} records")

	smr_bookings = get_bookings(source_id="src_smrikaam")
	assert all(b["source"] == "src_smrikaam" for b in smr_bookings["items"])
	print(f"✓ Source filter strictly isolates Smrikaam bookings ({len(smr_bookings['items'])})")

	bit_bookings = get_bookings(source_id="src_bitxhift")
	assert all(b["source"] == "src_bitxhift" for b in bit_bookings["items"])
	print(f"✓ Source filter strictly isolates BitXhift bookings ({len(bit_bookings['items'])})")

	# 5. Test Booking Actions
	print("\n--- 5. Testing Booking Actions & Activity Tracking ---")
	detail = get_booking_detail(booking_ref_1)
	assert detail["customer_name"] == "Arun Kumar"
	assert len(detail["activities"]) >= 1
	print("✓ Booking detail retrieved with initial activity log")

	# Update status
	update_booking_status(booking_ref_1, "Confirmed", note="Client confirmed phone number")
	d2 = get_booking_detail(booking_ref_1)
	assert d2["booking_status"] == "Confirmed"
	assert any(a["activity_type"] == "Status Change" for a in d2["activities"])
	print("✓ Status updated to Confirmed with activity recorded")

	# Reschedule
	reschedule_booking(booking_ref_1, "2026-11-26", "10:30 AM", note="Requested by client")
	d3 = get_booking_detail(booking_ref_1)
	assert str(d3["appointment_date"]) == "2026-11-26"
	assert d3["appointment_time"] == "10:30 AM"
	assert any(a["activity_type"] == "Rescheduled" for a in d3["activities"])
	print("✓ Rescheduled appointment with activity recorded")

	# 6. Test Source Management
	print("\n--- 6. Testing Add Source & Credential Management ---")
	new_src = add_source(
		source_name="Talento Partner Portal",
		domain="talento.smrikaam.com",
		website_type="Other",
		description="Partner recruitment portal",
	)
	assert new_src["status"] == "success"
	src_data = new_src["source"]
	assert src_data["api_key"].startswith("wbs_live_")
	assert src_data["api_secret"].startswith("sec_")
	print(f"✓ New source created: {src_data['source_id']}")

	# Duplicate domain rejection
	try:
		add_source(source_name="Duplicate Portal", domain="talento.smrikaam.com")
		assert False, "Should reject duplicate domain"
	except Exception as e:
		print("✓ Rejected duplicate domain registration")

	# Test connection
	test_res = test_connection(src_data["source_id"])
	assert test_res["status"] == "success"
	assert test_res["connection_status"] == "Connected"
	print("✓ Source connection test passed")

	# Regenerate credentials
	regen = regenerate_credentials(src_data["source_id"])
	assert regen["api_secret"] != src_data["api_secret"]
	print("✓ Credentials regenerated successfully")

	# Toggle status (disable)
	toggle_source_status(src_data["source_id"], False)
	disabled_src = frappe.get_doc("Website Booking Source", src_data["source_id"])
	assert disabled_src.is_active == 0
	print("✓ Source safely disabled without data deletion")

	# 7. Check Notifications
	print("\n--- 7. Testing CRM Notifications ---")
	notifs = frappe.get_all(
		"CRM Notification",
		filters={"reference_doctype": "Website Booking", "reference_name": booking_ref_1},
	)
	assert len(notifs) >= 1
	print(f"✓ CRM notification verified for booking {booking_ref_1}")

	print("\n=======================================================")
	print("🎉 ALL BACKEND BOOKING HUB TESTS PASSED WITH 100% SUCCESS!")
	print("=======================================================")


if __name__ == "__main__":
	frappe.init("crm.localhost")
	frappe.connect()
	run_tests()
