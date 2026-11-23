import frappe
from frappe.utils.typing_validations import transform_parameter_types

def test_add_source():
    frappe.init(site="crm.localhost")
    frappe.connect()
    frappe.set_user("Administrator")

    print("\n--- 1. Testing transform_parameter_types with force_types=True ---")
    from crm.api.booking_hub import add_source, get_bookings, get_booking_detail, update_booking_status

    # Test typing validation on add_source
    test_kwargs = {
        "source_name": "Test Partner Portal",
        "domain": "https://www.testpartnerportal123.com/",
        "website_type": "Corporate",
        "description": "Testing RPC type checks",
        "is_active": 1,
    }
    args, kwargs = transform_parameter_types(add_source, (), test_kwargs, force_types=True)
    print("✓ transform_parameter_types passed without FrappeTypeError!")

    # Clean up test source if already exists
    cleaned_domain = "testpartnerportal123.com"
    existing = frappe.db.get_value("Website Booking Source", {"domain": cleaned_domain}, "name")
    if existing:
        frappe.delete_doc("Website Booking Source", existing, force=1)
        frappe.db.commit()

    print("\n--- 2. Testing Execution of add_source ---")
    res = add_source(**kwargs)
    assert res.get("status") == "success", f"add_source failed: {res}"
    assert "source_id" in res, "source_id missing from top-level response"
    assert "source" in res, "source dict missing from response"
    assert res["connection_status"] == "Pending Setup", f"Expected Pending Setup, got {res['connection_status']}"
    assert res["is_active"] == 1, "Expected is_active=1"
    print(f"✓ Source created successfully: {res['source_id']} ({res['domain']})")
    print(f"✓ Connection status: {res['connection_status']} (Form Active: {res['is_active']})")
    print(f"✓ One-time API Secret generated: {res['api_secret'][:8]}...")

    print("\n--- 3. Testing Duplicate Domain Rejection ---")
    try:
        add_source(
            source_name="Duplicate Portal",
            domain="https://www.testpartnerportal123.com/",
            website_type="Corporate",
            description="",
            is_active=1
        )
        assert False, "Should have thrown duplicate domain error!"
    except Exception as e:
        print(f"✓ Duplicate domain cleanly rejected: {str(e)}")

    print("\n--- 4. Testing Empty / Invalid Inputs ---")
    try:
        add_source(
            source_name="",
            domain="valid.com",
            website_type="Corporate",
            description="",
            is_active=1
        )
        assert False, "Should have thrown mandatory source_name error"
    except Exception as e:
        print(f"✓ Empty source name rejected: {str(e)}")

    try:
        add_source(
            source_name="Valid Name",
            domain="",
            website_type="Corporate",
            description="",
            is_active=1
        )
        assert False, "Should have thrown mandatory domain error"
    except Exception as e:
        print(f"✓ Empty domain rejected: {str(e)}")

    # Clean up test source
    frappe.delete_doc("Website Booking Source", res["source_id"], force=1)
    frappe.db.commit()
    print("✓ Test source cleaned up")

    print("\n================== ALL ADD_SOURCE RPC TESTS PASSED! ==================\n")

if __name__ == "__main__":
    test_add_source()
