"""Main orchestration entrypoint for runtime risk evaluation."""

from __future__ import annotations

import sys
from typing import Any, Iterable, Literal, Mapping

from ai_risk_gateway.config.settings import GatewaySettings
from ai_risk_gateway.engines.decision_engine import DecisionEngine
from ai_risk_gateway.engines.policy_engine import PolicyEngine
from ai_risk_gateway.engines.risk_scorer import RiskScorer
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.decision import Decision, DecisionType
from ai_risk_gateway.policies.base import BasePolicy
from ai_risk_gateway.providers.base_state_provider import BaseStateProvider

EnforcementMode = Literal["strict", "advisory", "monitor"]

_SEVERITY_ICON = {"LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴"}


class RiskGateway:
    """Runtime policy enforcement layer for AI agent actions.

    Enforcement modes
    -----------------
    strict   – BLOCK decisions are fully enforced (default).
    advisory – Violations are logged but execution is never blocked.
    monitor  – Never blocks; only computes and logs the risk score.
    """

    def __init__(
        self,
        state_provider: BaseStateProvider,
        policies: Iterable[BasePolicy],
        config: GatewaySettings | Mapping[str, Any] | None = None,
        mode: EnforcementMode = "strict",
    ) -> None:
        """Initialize gateway with provider, policies, config, and mode."""
        if config is None:
            settings = GatewaySettings()
        elif isinstance(config, GatewaySettings):
            settings = config
        else:
            settings = GatewaySettings(
                allow_max=int(config.get("allow_max", GatewaySettings.allow_max)),
                review_max=int(config.get("review_max", GatewaySettings.review_max)),
            )

        if mode not in ("strict", "advisory", "monitor"):
            raise ValueError(f"Unknown enforcement mode: '{mode}'. Choose strict | advisory | monitor.")

        self._state_provider = state_provider
        self._settings = settings
        self._mode = mode
        self._policy_engine = PolicyEngine(policies)
        self._risk_scorer = RiskScorer()
        self._decision_engine = DecisionEngine(
            allow_max=settings.allow_max,
            review_max=settings.review_max,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, action_dict: dict[str, Any]) -> Decision:
        """Evaluate an incoming action and return a structured risk decision.

        The raw decision reflects what the policies found, regardless of mode.
        Call :meth:`enforce` (or rely on the returned Decision) to act on it.
        """
        action = Action.from_dict(action_dict)
        context = Context(
            state_provider=self._state_provider,
            config=self._settings.to_dict(),
            features={},
        )

        violations = self._policy_engine.run(action=action, context=context)
        risk_score = self._risk_scorer.score(violations)
        decision = self._decision_engine.evaluate(risk_score=risk_score, violations=violations)

        self._state_provider.record_action(action)
        self._log(action, decision)
        return decision

    def enforce(self, decision: Decision) -> Decision:
        """Apply the enforcement mode to a decision.

        - strict  : returns the decision unchanged (caller must honour BLOCK).
        - advisory: downgrades BLOCK → ALLOW, logs the override.
        - monitor : always returns ALLOW, logs that we are in monitor mode.

        Returns the (possibly overridden) Decision.
        """
        if self._mode == "strict":
            return decision

        if self._mode == "advisory":
            if decision.is_blocked or decision.is_review:
                print(
                    f"  [advisory] Enforcement overridden — action would have been "
                    f"{decision.decision.value} (score={decision.risk_score}). "
                    f"Execution proceeding."
                )
            return Decision(
                decision=DecisionType.ALLOW,
                risk_score=decision.risk_score,
                violations=decision.violations,
                requires_approval=False,
                evaluated_at=decision.evaluated_at,
            )

        # monitor mode
        print(
            f"  [monitor] Mode=monitor — risk score={decision.risk_score}, "
            f"raw decision would be {decision.decision.value}. No enforcement applied."
        )
        return Decision(
            decision=DecisionType.ALLOW,
            risk_score=decision.risk_score,
            violations=decision.violations,
            requires_approval=False,
            evaluated_at=decision.evaluated_at,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, action: Action, decision: Decision) -> None:
        """Print a structured interception summary to the console."""
        # Ensure the terminal can display UTF-8 / emoji on all platforms.
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass

        icon = "🔒"
        separator = "─" * 48

        print(f"\n{separator}")
        print(f"{icon} AI Risk Gateway — Action Intercepted")
        print(separator)
        print(f"  Action ID  : {action.action_id}")
        print(f"  Agent      : {action.agent_id}")
        print(f"  Source     : {action.source}")
        print(f"  Type       : {action.action_type}")
        if action.target:
            print(f"  Target     : {action.target}")
        print(f"  Timestamp  : {action.timestamp.isoformat()}")
        print(f"  Mode       : {self._mode}")
        print(separator)
        print(f"  Risk Score : {decision.risk_score}")
        print(f"  Decision   : {decision.decision.value}")
        print(f"  Evaluated  : {decision.evaluated_at.isoformat()}")

        if decision.violations:
            print(f"  Violations :")
            for v in decision.violations:
                sev_icon = _SEVERITY_ICON.get(v.severity, "⚪")
                print(f"    {sev_icon} [{v.policy_code} | {v.severity}] {v.message}")
        else:
            print("  Violations : none")

        if decision.is_blocked:
            print(f"\n  🛡  Enforcement Applied — action BLOCKED")
        elif decision.is_review:
            print(f"\n  👁  Action flagged for REVIEW — approval required")
        else:
            print(f"\n  ✅ Action ALLOWED")

        print(separator)
