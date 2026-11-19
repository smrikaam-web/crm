import frappe


def execute():
	"""Add performance indexes for CRM Daily Allocation and CRM Call Log."""
	if frappe.db.table_exists("CRM Daily Allocation"):
		frappe.db.add_index("CRM Daily Allocation", ["assigned_to", "allocation_date"], "idx_assigned_allocation_date")
		frappe.db.add_index("CRM Daily Allocation", ["contact"], "idx_contact")
		frappe.db.add_index("CRM Daily Allocation", ["status"], "idx_status")

	if frappe.db.table_exists("CRM Call Log"):
		frappe.db.add_index("CRM Call Log", ["status"], "idx_status")
