"""Decision model returned by the gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ai_risk_gateway.models.violation import Violation


class DecisionType(str, Enum):
    """Supported gateway decisions."""

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class Decision:
    """Structured decision generated after policy and risk evaluation."""

    decision: DecisionType
    risk_score: int
    violations: list[Violation] = field(default_factory=list)
    requires_approval: bool = False
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_allowed(self) -> bool:
        """Return True when the decision is ALLOW."""
        return self.decision == DecisionType.ALLOW

    @property
    def is_blocked(self) -> bool:
        """Return True when the decision is BLOCK."""
        return self.decision == DecisionType.BLOCK

    @property
    def is_review(self) -> bool:
        """Return True when the decision is REVIEW."""
        return self.decision == DecisionType.REVIEW
