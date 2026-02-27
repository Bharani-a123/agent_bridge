"""Policy enforcing a configurable refund amount cap."""

from __future__ import annotations

from ai_risk_gateway.constants import DEFAULT_REFUND_LIMIT_POLICY_WEIGHT
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.violation import Violation
from ai_risk_gateway.policies.base import BasePolicy


class RefundLimitPolicy(BasePolicy):
    """Flags refund actions with amount above permitted cap."""

    def __init__(self, max_refund_amount: float, weight: int = DEFAULT_REFUND_LIMIT_POLICY_WEIGHT) -> None:
        """Initialize max refund amount and violation weight."""
        self._max_refund_amount = float(max_refund_amount)
        self._weight = weight

    def evaluate(self, action: Action, context: Context) -> Violation | None:
        """Return a violation if refund amount exceeds configured limit."""
        if action.action_type != "refund":
            return None

        amount = action.payload.get("amount")
        if not isinstance(amount, (int, float)):
            return Violation(
                policy_code="REFUND_AMOUNT_INVALID",
                severity="LOW",
                weight=self._weight,
                message="Refund action missing numeric 'amount'.",
            )

        numeric_amount = float(amount)
        if numeric_amount <= self._max_refund_amount:
            return None

        return Violation(
            policy_code="REFUND_LIMIT_EXCEEDED",
            severity="HIGH",
            weight=self._weight,
            message=(
                f"Refund amount {numeric_amount:.2f} exceeds allowed "
                f"limit of {self._max_refund_amount:.2f}."
            ),
            details={
                "amount": numeric_amount,
                "max_refund_amount": self._max_refund_amount,
            },
        )
