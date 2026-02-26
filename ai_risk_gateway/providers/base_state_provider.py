"""State provider abstraction for action history lookup and recording."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_risk_gateway.models.action import Action


class BaseStateProvider(ABC):
	"""Contract for runtime state providers used by policies."""

	@abstractmethod
	def get_action_count(self, agent_id: str, action_type: str, timeframe_seconds: int) -> int:
		"""Return count of actions for an agent/type within the timeframe."""

	@abstractmethod
	def record_action(self, action: Action) -> None:
		"""Record an action for future state-based policy checks."""