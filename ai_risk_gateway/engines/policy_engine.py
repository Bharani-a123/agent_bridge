"""Engine that runs policies and aggregates violations."""

from __future__ import annotations

from typing import Iterable

from ai_risk_gateway.exceptions import PolicyEvaluationError
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.violation import Violation
from ai_risk_gateway.policies.base import BasePolicy


class PolicyEngine:
	"""Executes a set of policies for a given action and context."""

	def __init__(self, policies: Iterable[BasePolicy]) -> None:
		"""Create a policy engine with ordered policy instances."""
		self._policies = list(policies)

	def run(self, action: Action, context: Context) -> list[Violation]:
		"""Run all policies and return collected violations."""
		violations: list[Violation] = []
		for policy in self._policies:
			try:
				result = policy.evaluate(action, context)
			except Exception as exc:
				raise PolicyEvaluationError(
					f"Policy '{policy.name}' failed during evaluation."
				) from exc

			if result is not None:
				violations.append(result)

		return violations