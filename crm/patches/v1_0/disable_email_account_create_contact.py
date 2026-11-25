import frappe


def execute():
	# 1. Disable create_contact on all existing Email Accounts
	frappe.db.sql("UPDATE `tabEmail Account` SET create_contact = 0")

	# 2. Add or update Property Setter so new Email Accounts default to create_contact = 0
	ps_name = "Email Account-create_contact-default"
	if not frappe.db.exists("Property Setter", ps_name):
		frappe.get_doc({
			"doctype": "Property Setter",
			"name": ps_name,
			"doctype_or_field": "DocField",
			"doc_type": "Email Account",
			"field_name": "create_contact",
			"property": "default",
			"property_type": "Check",
			"value": "0",
			"is_system_generated": 1,
		}).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("Property Setter", ps_name, "value", "0")

	# 3. Clean up Communication records erroneously pointing to bounce contact records
	bounce_contacts = ("Mailer Daemon", "Mailer Daemon-1", "Mailer Daemon-2", "Noreply")
	frappe.db.sql("""
		UPDATE `tabCommunication`
		SET reference_doctype = NULL, reference_name = NULL, delivery_status = 'Bounced'
		WHERE reference_doctype = 'Contact' AND reference_name IN %(bounce_contacts)s
	""", {"bounce_contacts": bounce_contacts})

	frappe.clear_cache(doctype="Email Account")
	frappe.clear_cache(doctype="Communication")
