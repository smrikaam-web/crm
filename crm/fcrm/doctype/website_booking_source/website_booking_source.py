# Copyright (c) 2026, Smrikaam and contributors
# For license information, please see license.txt

import hashlib
import secrets
import frappe
from frappe.model.document import Document


class WebsiteBookingSource(Document):
	def validate(self):
		if self.domain:
			self.domain = self.domain.strip().lower()
			if self.domain.startswith("https://"):
				self.domain = self.domain[8:]
			elif self.domain.startswith("http://"):
				self.domain = self.domain[7:]
			self.domain = self.domain.split("/")[0].split(":")[0]
			if self.domain.startswith("www."):
				self.domain = self.domain[4:]

		if not self.source_id:
			base_slug = frappe.scrub(self.source_name or "source")
			self.source_id = f"src_{base_slug}_{secrets.token_hex(4)}"

	def generate_credentials(self) -> tuple[str, str]:
		"""Generates a new API key and secret pair.
		Returns (api_key, raw_api_secret).
		The secret is stored ONLY as a secure SHA-256 hash.
		"""
		api_key = f"wbs_live_{secrets.token_urlsafe(18)}"
		raw_secret = f"sec_{secrets.token_urlsafe(32)}"
		secret_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

		self.api_key = api_key
		self.api_secret_hash = secret_hash
		self.credential_reference = f"{raw_secret[:8]}...{raw_secret[-4:]}"
		return api_key, raw_secret

	def verify_secret(self, raw_secret: str) -> bool:
		if not self.api_secret_hash or not raw_secret:
			return False
		candidate_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
		return secrets.compare_digest(self.api_secret_hash, candidate_hash)
