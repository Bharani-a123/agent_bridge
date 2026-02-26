"""In-memory implementation of state provider."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from ai_risk_gateway.models.action import Action
from ai_risk_gateway.providers.base_state_provider import BaseStateProvider


class InMemoryStateProvider(BaseStateProvider):
	"""Dictionary-backed state store suitable for local/testing usage."""

	def __init__(self) -> None:
		"""Initialize in-memory event storage."""
		self._events: dict[tuple[str, str], list[datetime]] = defaultdict(list)

	def get_action_count(self, agent_id: str, action_type: str, timeframe_seconds: int) -> int:
		"""Return number of matching actions observed in timeframe."""
		if timeframe_seconds < 0:
			raise ValueError("timeframe_seconds must be >= 0")

		key = (agent_id, action_type)
		now = datetime.now(timezone.utc)
		cutoff = now - timedelta(seconds=timeframe_seconds)

		events = self._events.get(key, [])
		recent_events = [timestamp for timestamp in events if timestamp >= cutoff]
		self._events[key] = recent_events
		return len(recent_events)

	def record_action(self, action: Action) -> None:
		"""Persist action timestamp in memory."""
		key = (action.agent_id, action.action_type)
		self._events[key].append(action.timestamp)