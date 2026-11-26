import frappe


def execute():
	frappe.reload_doc("fcrm", "doctype", "crm_prospect_status_update", force=True)
	if frappe.db.table_exists("CRM Prospect Status Update") and not frappe.db.has_column(
		"CRM Prospect Status Update", "sub_status"
	):
		frappe.db.add_column(
			doctype="CRM Prospect Status Update",
			column_name="sub_status",
			type="VARCHAR(140)",
		)
