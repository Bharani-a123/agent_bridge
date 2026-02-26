"""Engine that maps risk score to ALLOW/REVIEW/BLOCK decision."""

from __future__ import annotations

from ai_risk_gateway.constants import DEFAULT_ALLOW_MAX, DEFAULT_REVIEW_MAX
from ai_risk_gateway.models.decision import Decision, DecisionType
from ai_risk_gateway.models.violation import Violation


class DecisionEngine:
	"""Computes final decision based on configured thresholds."""

	def __init__(self, allow_max: int = DEFAULT_ALLOW_MAX, review_max: int = DEFAULT_REVIEW_MAX) -> None:
		"""Initialize decision thresholds.

		Args:
			allow_max: Highest score still considered ALLOW.
			review_max: Highest score still considered REVIEW; above this is BLOCK.
		"""
		if allow_max < 0 or review_max < allow_max:
			raise ValueError("Thresholds must satisfy 0 <= allow_max <= review_max.")
		self._allow_max = allow_max
		self._review_max = review_max

	def evaluate(self, risk_score: int, violations: list[Violation]) -> Decision:
		"""Return structured decision from risk score and violations."""
		if risk_score <= self._allow_max:
			return Decision(
				decision=DecisionType.ALLOW,
				risk_score=risk_score,
				violations=violations,
				requires_approval=False,
			)

		if risk_score <= self._review_max:
			return Decision(
				decision=DecisionType.REVIEW,
				risk_score=risk_score,
				violations=violations,
				requires_approval=True,
			)

		return Decision(
			decision=DecisionType.BLOCK,
			risk_score=risk_score,
			violations=violations,
			requires_approval=False,
		)