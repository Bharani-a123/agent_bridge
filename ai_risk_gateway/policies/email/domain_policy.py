"""Policy to restrict outbound email domains."""

from __future__ import annotations

from collections.abc import Iterable

from ai_risk_gateway.constants import DEFAULT_DOMAIN_POLICY_WEIGHT
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.violation import Violation
from ai_risk_gateway.policies.base import BasePolicy


class DomainPolicy(BasePolicy):
	"""Blocks/reviews email actions sent to non-allowlisted domains."""

	def __init__(self, allowed_domains: Iterable[str], weight: int = DEFAULT_DOMAIN_POLICY_WEIGHT) -> None:
		"""Initialize domain allowlist and violation weight."""
		self._allowed_domains = {domain.lower().strip() for domain in allowed_domains if domain.strip()}
		self._weight = weight

	def evaluate(self, action: Action, context: Context) -> Violation | None:
		"""Return a violation when email recipient domain is not allowlisted."""
		if action.action_type != "send_email":
			return None

		recipient = action.payload.get("to")
		if not isinstance(recipient, str) or "@" not in recipient:
			return Violation(
				policy_name=self.name,
				message="Email recipient is missing or invalid.",
				weight=self._weight,
				code="EMAIL_RECIPIENT_INVALID",
			)

		domain = recipient.rsplit("@", maxsplit=1)[-1].lower().strip()
		if domain in self._allowed_domains:
			return None

		return Violation(
			policy_name=self.name,
			message=f"Email domain '{domain}' is not allowlisted.",
			weight=self._weight,
			code="EMAIL_DOMAIN_RESTRICTED",
			details={"domain": domain},
		)