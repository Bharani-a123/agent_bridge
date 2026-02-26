"""Action model representing an incoming agent request."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ai_risk_gateway.exceptions import ActionValidationError


@dataclass(frozen=True)
class Action:
	"""Represents an action request emitted by an AI agent."""

	agent_id: str
	action_type: str
	payload: dict[str, Any] = field(default_factory=dict)
	metadata: dict[str, Any] = field(default_factory=dict)
	timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

	@classmethod
	def from_dict(cls, data: Mapping[str, Any]) -> "Action":
		"""Validate and construct an Action from a dictionary payload."""
		if not isinstance(data, Mapping):
			raise ActionValidationError("Action input must be a dictionary-like mapping.")

		agent_id = data.get("agent_id")
		action_type = data.get("action_type")

		if not isinstance(agent_id, str) or not agent_id.strip():
			raise ActionValidationError("'agent_id' is required and must be a non-empty string.")
		if not isinstance(action_type, str) or not action_type.strip():
			raise ActionValidationError("'action_type' is required and must be a non-empty string.")

		payload = data.get("payload", {})
		metadata = data.get("metadata", {})

		if payload is None:
			payload = {}
		if metadata is None:
			metadata = {}

		if not isinstance(payload, dict):
			raise ActionValidationError("'payload' must be a dictionary when provided.")
		if not isinstance(metadata, dict):
			raise ActionValidationError("'metadata' must be a dictionary when provided.")

		return cls(
			agent_id=agent_id.strip(),
			action_type=action_type.strip(),
			payload=payload,
			metadata=metadata,
		)