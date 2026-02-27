"""Engine that runs policies and aggregates violations."""

from __future__ import annotations

from typing import Iterable

from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.violation import Violation
from ai_risk_gateway.policies.base import BasePolicy

# Weight high enough to guarantee a BLOCK outcome on its own
_POLICY_ERROR_WEIGHT = 100


class PolicyEngine:
    """Executes a set of policies for a given action and context."""

    def __init__(self, policies: Iterable[BasePolicy]) -> None:
        """Create a policy engine with ordered policy instances."""
        self._policies = list(policies)

    def run(self, action: Action, context: Context) -> list[Violation]:
        """Run all policies and return collected violations.

        If a policy raises an unexpected exception the system fails
        **closed**: a HIGH-severity POLICY_ERROR violation is recorded
        and evaluation continues with the remaining policies.
        """
        violations: list[Violation] = []
        for policy in self._policies:
            try:
                result = policy.evaluate(action, context)
            except Exception as exc:
                violations.append(
                    Violation(
                        policy_code="POLICY_ERROR",
                        severity="HIGH",
                        weight=_POLICY_ERROR_WEIGHT,
                        message=(
                            f"Policy '{policy.name}' raised an unexpected error: {exc}"
                        ),
                    )
                )
                continue

            if result is not None:
                violations.append(result)

        return violations
