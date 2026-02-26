"""Base abstraction for all risk policies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.violation import Violation


class BasePolicy(ABC):
	"""Abstract base class for independently pluggable policies."""

	@property
	def name(self) -> str:
		"""Return policy name used in violation metadata."""
		return self.__class__.__name__

	@abstractmethod
	def evaluate(self, action: Action, context: Context) -> Violation | None:
		"""Evaluate an action and return a violation if policy is breached."""