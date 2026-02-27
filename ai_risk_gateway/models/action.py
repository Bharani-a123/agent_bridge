"""Action model representing an incoming agent request."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ai_risk_gateway.exceptions import ActionValidationError


@dataclass(frozen=True)
class Action:
    """Represents an action request emitted by an AI agent.

    Schema:
        action_id  – unique identifier (auto-generated UUID4 if omitted)
        agent_id   – identity of the agent issuing the action
        source     – originating framework name (e.g. "langgraph", "custom")
        action_type – logical operation type (e.g. "send_email", "refund")
        target     – target resource/recipient (e.g. email address, endpoint)
        payload    – tool arguments
        timestamp  – UTC ISO-8601 creation time (auto-set if omitted)
    """

    action_id: str
    agent_id: str
    action_type: str
    source: str = "unknown"
    target: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Action":
        """Validate and construct an Action from a dictionary payload.

        ``action_id`` and ``timestamp`` are auto-generated when absent.
        """
        if not isinstance(data, Mapping):
            raise ActionValidationError("Action input must be a dictionary-like mapping.")

        agent_id = data.get("agent_id")
        action_type = data.get("action_type")

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ActionValidationError("'agent_id' is required and must be a non-empty string.")
        if not isinstance(action_type, str) or not action_type.strip():
            raise ActionValidationError("'action_type' is required and must be a non-empty string.")

        # Auto-generate action_id when not provided
        action_id = data.get("action_id")
        if not isinstance(action_id, str) or not action_id.strip():
            action_id = str(uuid.uuid4())

        # Auto-set timestamp when not provided
        raw_ts = data.get("timestamp")
        if isinstance(raw_ts, datetime):
            timestamp = raw_ts
        elif isinstance(raw_ts, str):
            try:
                timestamp = datetime.fromisoformat(raw_ts)
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        payload = data.get("payload") or {}
        metadata = data.get("metadata") or {}

        if not isinstance(payload, dict):
            raise ActionValidationError("'payload' must be a dictionary when provided.")
        if not isinstance(metadata, dict):
            raise ActionValidationError("'metadata' must be a dictionary when provided.")

        source = data.get("source", "unknown")
        if not isinstance(source, str):
            source = "unknown"

        target = data.get("target", "")
        if not isinstance(target, str):
            target = ""

        return cls(
            action_id=action_id.strip(),
            agent_id=agent_id.strip(),
            action_type=action_type.strip(),
            source=source,
            target=target,
            payload=payload,
            metadata=metadata,
            timestamp=timestamp,
        )
