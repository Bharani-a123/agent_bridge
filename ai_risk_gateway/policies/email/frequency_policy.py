"""Policy enforcing action frequency limits."""

from __future__ import annotations

from ai_risk_gateway.constants import (
	DEFAULT_FREQUENCY_MAX_ACTIONS,
	DEFAULT_FREQUENCY_POLICY_WEIGHT,
	DEFAULT_FREQUENCY_TIMEFRAME_SECONDS,
)
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.violation import Violation
from ai_risk_gateway.policies.base import BasePolicy


class FrequencyPolicy(BasePolicy):
	"""Flags actions that exceed a maximum frequency per timeframe."""

	def __init__(
		self,
		max_actions: int = DEFAULT_FREQUENCY_MAX_ACTIONS,
		timeframe_seconds: int = DEFAULT_FREQUENCY_TIMEFRAME_SECONDS,
		weight: int = DEFAULT_FREQUENCY_POLICY_WEIGHT,
	) -> None:
		"""Initialize limits and risk weight for the frequency policy."""
		self._max_actions = max_actions
		self._timeframe_seconds = timeframe_seconds
		self._weight = weight

	def evaluate(self, action: Action, context: Context) -> Violation | None:
		"""Return violation if frequency threshold is exceeded."""
		current_count = context.state_provider.get_action_count(
			agent_id=action.agent_id,
			action_type=action.action_type,
			timeframe_seconds=self._timeframe_seconds,
		)

		if current_count < self._max_actions:
			return None

		return Violation(
			policy_name=self.name,
			message=(
				f"Action frequency exceeded: {current_count} actions in "
				f"{self._timeframe_seconds}s (max {self._max_actions})."
			),
			weight=self._weight,
			code="ACTION_RATE_LIMIT_EXCEEDED",
			details={
				"current_count": current_count,
				"max_actions": self._max_actions,
				"timeframe_seconds": self._timeframe_seconds,
			},
		)