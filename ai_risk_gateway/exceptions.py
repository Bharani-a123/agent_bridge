"""Custom exceptions for ai_risk_gateway."""

from __future__ import annotations


class RiskGatewayError(Exception):
	"""Base exception for all ai_risk_gateway errors."""


class ActionValidationError(RiskGatewayError):
	"""Raised when an incoming action payload is invalid."""


class PolicyEvaluationError(RiskGatewayError):
	"""Raised when a policy fails during evaluation."""