"""Main orchestration entrypoint for runtime risk evaluation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ai_risk_gateway.config.settings import GatewaySettings
from ai_risk_gateway.engines.decision_engine import DecisionEngine
from ai_risk_gateway.engines.policy_engine import PolicyEngine
from ai_risk_gateway.engines.risk_scorer import RiskScorer
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.decision import Decision
from ai_risk_gateway.policies.base import BasePolicy
from ai_risk_gateway.providers.base_state_provider import BaseStateProvider


class RiskGateway:
	"""Runtime policy enforcement layer for AI agent actions."""

	def __init__(
		self,
		state_provider: BaseStateProvider,
		policies: Iterable[BasePolicy],
		config: GatewaySettings | Mapping[str, Any] | None = None,
	) -> None:
		"""Initialize gateway with provider, policies, and optional config."""
		if config is None:
			settings = GatewaySettings()
		elif isinstance(config, GatewaySettings):
			settings = config
		else:
			settings = GatewaySettings(
				allow_max=int(config.get("allow_max", GatewaySettings.allow_max)),
				review_max=int(config.get("review_max", GatewaySettings.review_max)),
			)

		self._state_provider = state_provider
		self._settings = settings
		self._policy_engine = PolicyEngine(policies)
		self._risk_scorer = RiskScorer()
		self._decision_engine = DecisionEngine(
			allow_max=settings.allow_max,
			review_max=settings.review_max,
		)

	def evaluate(self, action_dict: dict[str, Any]) -> Decision:
		"""Evaluate an incoming action and return structured risk decision."""
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
		return decision