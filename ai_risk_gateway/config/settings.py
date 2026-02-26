"""Configuration models for ai_risk_gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_risk_gateway.constants import DEFAULT_ALLOW_MAX, DEFAULT_REVIEW_MAX


@dataclass(frozen=True)
class GatewaySettings:
	"""Configuration object for RiskGateway behavior."""

	allow_max: int = DEFAULT_ALLOW_MAX
	review_max: int = DEFAULT_REVIEW_MAX

	def to_dict(self) -> dict[str, Any]:
		"""Return dictionary representation for context propagation."""
		return {
			"allow_max": self.allow_max,
			"review_max": self.review_max,
		}