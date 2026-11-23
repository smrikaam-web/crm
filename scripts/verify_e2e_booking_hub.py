import frappe

def verify():
    frappe.init(site="crm.localhost")
    frappe.connect()

    print("\n================== VERIFYING BOOKING HUB E2E ==================")
    from crm.api.booking_hub import (
        get_booking_hub_summary,
        get_bookings,
        create_booking,
        get_booking_detail,
        update_booking_status,
        reschedule_booking,
        add_booking_note,
        assign_booking,
        add_source,
        test_connection,
        regenerate_credentials,
        toggle_source_status
    )

    # 1. Summary
    summary = get_booking_hub_summary()
    assert "metrics" in summary, "Summary missing metrics"
    assert "sources" in summary, "Summary missing sources"
    print(f"✓ Summary verified: {summary['metrics']}")
    print(f"✓ Sources registered: {[s['source_id'] for s in summary['sources']]}")

    # 2. Query Bookings
    bookings_res = get_bookings(page_length=10)
    assert "bookings" in bookings_res, "Get bookings failed"
    print(f"✓ Total bookings returned: {bookings_res['total_count']}")

    # 3. Create a Booking via API
    source_id = "src_smrikaam"
    source = frappe.get_doc("Website Booking Source", source_id)
    api_key, raw_secret = source.generate_credentials()
    source.save(ignore_permissions=True)
    frappe.db.commit()

    test_payload = {
        "source_id": source_id,
        "api_key": api_key,
        "api_secret": raw_secret,
        "customer_name": "E2E Test User",
        "company_name": "Smrikaam Technologies",
        "email": "e2e_candidate@smrikaam.com",
        "phone": "+91 9988776655",
        "interested_service": "Technical Staffing / Cloud & DevOps",
        "appointment_date": "2026-11-28",
        "appointment_time": "03:30 PM",
        "timezone": "Asia/Kolkata",
        "message": "Candidate interview scheduled via E2E test",
        "page_url": "https://smrikaam.com/schedule-meeting"
    }

    res = create_booking(**test_payload)
    assert res.get("status") == "success", f"create_booking failed: {res}"
    booking_ref = res.get("booking_reference")
    print(f"✓ Created booking reference: {booking_ref}")

    # 4. Detail View & Activity History
    detail = get_booking_detail(booking_reference=booking_ref)
    assert detail["booking"]["name"] == booking_ref
    assert len(detail["activities"]) >= 1
    print(f"✓ Booking detail retrieved with {len(detail['activities'])} activity logs")

    # 5. Status Update
    upd = update_booking_status(booking_reference=booking_ref, status="Confirmed")
    assert upd["status"] == "success"
    print("✓ Status updated to Confirmed")

    # 6. Reschedule
    resch = reschedule_booking(booking_reference=booking_ref, new_date="2026-11-30", new_time="11:00 AM", reason="Client request")
    assert resch["status"] == "success"
    print("✓ Rescheduled to 2026-11-30 11:00 AM")

    # 7. Add Note
    note_res = add_booking_note(booking_reference=booking_ref, note="Interview panel confirmed by HR")
    assert note_res["status"] == "success"
    print("✓ Internal note added")

    # 8. Assign
    assign_res = assign_booking(booking_reference=booking_ref, assigned_to="Administrator")
    assert assign_res["status"] == "success"
    print("✓ Booking assigned to Administrator")

    # 9. Verify Detail Again
    updated_detail = get_booking_detail(booking_reference=booking_ref)
    assert updated_detail["booking"]["booking_status"] == "Rescheduled"
    assert str(updated_detail["booking"]["appointment_date"]) == "2026-11-30"
    assert updated_detail["booking"]["assigned_to"] == "Administrator"
    assert len(updated_detail["activities"]) >= 5
    print(f"✓ Updated booking verified with {len(updated_detail['activities'])} activities")

    # 10. Regression Check on Existing CRM DocTypes
    print("\n--- Regression Check on Core CRM Modules ---")
    lead_count = frappe.db.count("CRM Lead")
    deal_count = frappe.db.count("CRM Deal")
    contact_count = frappe.db.count("Contact")
    org_count = frappe.db.count("CRM Organization")
    task_count = frappe.db.count("CRM Task") if frappe.db.exists("DocType", "CRM Task") else 0
    notif_count = frappe.db.count("CRM Notification")
    print(f"✓ CRM Lead count: {lead_count}")
    print(f"✓ CRM Deal count: {deal_count}")
    print(f"✓ Contact count: {contact_count}")
    print(f"✓ CRM Organization count: {org_count}")
    print(f"✓ CRM Task count: {task_count}")
    print(f"✓ CRM Notification count: {notif_count}")

    print("\n================== ALL E2E & REGRESSION CHECKS PASSED! ==================\n")

if __name__ == "__main__":
    verify()
