import frappe
from frappe.contacts.doctype.contact.contact import Contact


def contact_on_trash(doc, method=None):
	"""Clean up all dependent/linked records before contact is deleted so LinkExistsError never occurs."""
	name = getattr(doc, "name", None) or str(doc)
	if not name:
		return

	# 1. Clean up CRM Daily Allocation tasks referencing this contact
	frappe.db.delete("CRM Daily Allocation", {"contact": name})

	# 2. Clean up CRM Contacts child table in CRM Deals
	frappe.db.delete("CRM Contacts", {"contact": name})

	# 3. Clear direct contact field on CRM Deals
	frappe.db.set_value("CRM Deal", {"contact": name}, "contact", None)

	# 4. Clean up Dynamic Link records pointing to this contact
	frappe.db.delete("Dynamic Link", {"link_doctype": "Contact", "link_name": name})

	# 5. Clean up CRM Call Log dynamic references
	frappe.db.set_value(
		"CRM Call Log",
		{"reference_doctype": "Contact", "reference_docname": name},
		{"reference_doctype": None, "reference_docname": None},
	)

	# 6. Clean up FCRM Note dynamic references
	frappe.db.set_value(
		"FCRM Note",
		{"reference_doctype": "Contact", "reference_docname": name},
		{"reference_doctype": None, "reference_docname": None},
	)

	# 7. Clean up ToDo assignments for this contact
	frappe.db.delete("ToDo", {"reference_type": "Contact", "reference_name": name})

	# 8. Clean up CRM Notification references
	frappe.db.delete("CRM Notification", {"reference_doctype": "Contact", "reference_name": name})


class CustomContact(Contact):
	def on_trash(self):
		contact_on_trash(self)
		if hasattr(super(), "on_trash"):
			super().on_trash()

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "full_name",
				"width": "17rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email_id",
				"width": "12rem",
			},
			{
				"label": "Phone",
				"type": "Data",
				"key": "mobile_no",
				"width": "12rem",
			},
			{
				"label": "Organization",
				"type": "Data",
				"key": "company_name",
				"width": "12rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"full_name",
			"company_name",
			"designation",
			"email_id",
			"mobile_no",
			"custom_country",
			"country",
			"custom_timezone",
			"timezone",
			"creation",
			"modified",
			"image",
			"_assign",
			"custom_is_dropped",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def parse_list_data(data):
		"""Enrich contact list data with resolved Country and Timezone matching My Tasks."""
		if not data:
			return data

		from crm.api.daily_allocation import (
			resolve_country_for_contact,
			get_timezone_for_country,
			format_timezone_label,
		)

		for row in data:
			c_name = row.get("name")
			org_name = row.get("company_name")

			# 1. Country resolution (matching My Tasks)
			c_val = row.get("custom_country") or row.get("country")
			if not c_val or c_val == "Not Available" or c_val == "—":
				c_val = resolve_country_for_contact(c_name, org_name)
			display_country = c_val if c_val and c_val != "Not Available" else "—"

			# 2. Timezone resolution (matching My Tasks)
			tz_val = row.get("custom_timezone") or row.get("timezone")
			if not tz_val or tz_val == "Not Available" or tz_val == "—":
				tz_val = get_timezone_for_country(c_val) if (c_val and c_val != "—" and c_val != "Not Available") else "Not Available"
			display_timezone = (
				format_timezone_label(tz_val, c_val)
				if (tz_val and tz_val != "Not Available")
				else "—"
			)

			row["custom_country"] = display_country
			row["country"] = display_country
			row["custom_timezone"] = display_timezone
			row["timezone"] = display_timezone

		return data
