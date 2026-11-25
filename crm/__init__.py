__version__ = "1.89.2"
__title__ = "Frappe CRM"


def _patch_communication_get_contacts():
	"""Ensure email synchronization never automatically creates Contact records in Smrikaam CRM."""
	try:
		import frappe.core.doctype.communication.communication as comm_module

		if not hasattr(comm_module, "_crm_original_get_contacts"):
			comm_module._crm_original_get_contacts = comm_module.get_contacts

			def _crm_safe_get_contacts(email_strings, auto_create_contact=False):
				# Smrikaam CRM Core Business Rule: Contacts must only be created through
				# intentional CRM operations (Admin CSV/Excel imports, Lead conversion,
				# or permitted manual creation). Email sync must NEVER auto-create Contacts.
				return comm_module._crm_original_get_contacts(email_strings, auto_create_contact=False)

			comm_module.get_contacts = _crm_safe_get_contacts
	except Exception:
		pass


_patch_communication_get_contacts()
