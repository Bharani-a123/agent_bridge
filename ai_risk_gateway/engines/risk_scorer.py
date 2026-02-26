"""Engine for deterministic risk score aggregation."""

from __future__ import annotations

from ai_risk_gateway.models.violation import Violation


class RiskScorer:
	"""Aggregates violation weights into a total integer risk score."""

	def score(self, violations: list[Violation]) -> int:
		"""Return total risk score from all violations."""
		return int(sum(max(0, violation.weight) for violation in violations))