"""Runtime context model enriched for policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_risk_gateway.providers.base_state_provider import BaseStateProvider


@dataclass(frozen=True)
class Context:
	"""Context used by policies at evaluation time."""

	state_provider: BaseStateProvider
	config: dict[str, Any] = field(default_factory=dict)
	features: dict[str, Any] = field(default_factory=dict)