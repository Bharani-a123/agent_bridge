"""ai_risk_gateway package.

Example:
	from ai_risk_gateway import (
		RiskGateway,
		InMemoryStateProvider,
		DomainPolicy,
		FrequencyPolicy,
		RefundLimitPolicy,
	)

	gateway = RiskGateway(
		state_provider=InMemoryStateProvider(),
		policies=[
			DomainPolicy(allowed_domains=["company.com"]),
			FrequencyPolicy(max_actions=3, timeframe_seconds=60),
			RefundLimitPolicy(max_refund_amount=500.0),
		],
		mode="strict",  # strict | advisory | monitor
	)

	decision = gateway.evaluate(
		{
			"agent_id": "agent-123",
			"action_type": "send_email",
			"payload": {"to": "user@company.com"},
		}
	)

	# Optionally apply enforcement mode override:
	enforced = gateway.enforce(decision)
"""

from ai_risk_gateway.config.settings import GatewaySettings
from ai_risk_gateway.exceptions import ActionValidationError, PolicyEvaluationError, RiskGatewayError
from ai_risk_gateway.gateway import EnforcementMode, RiskGateway
from ai_risk_gateway.models.action import Action
from ai_risk_gateway.models.context import Context
from ai_risk_gateway.models.decision import Decision, DecisionType
from ai_risk_gateway.models.violation import SeverityLevel, Violation
from ai_risk_gateway.policies.base import BasePolicy
from ai_risk_gateway.policies.email.domain_policy import DomainPolicy
from ai_risk_gateway.policies.email.frequency_policy import FrequencyPolicy
from ai_risk_gateway.policies.financial.refund_limit_policy import RefundLimitPolicy
from ai_risk_gateway.providers.base_state_provider import BaseStateProvider
from ai_risk_gateway.providers.in_memory_provider import InMemoryStateProvider
from ai_risk_gateway.registry import PolicyRegistry

__all__ = [
	"Action",
	"ActionValidationError",
	"BasePolicy",
	"BaseStateProvider",
	"Context",
	"Decision",
	"DecisionType",
	"DomainPolicy",
	"EnforcementMode",
	"FrequencyPolicy",
	"GatewaySettings",
	"InMemoryStateProvider",
	"PolicyEvaluationError",
	"PolicyRegistry",
	"RefundLimitPolicy",
	"RiskGateway",
	"RiskGatewayError",
	"SeverityLevel",
	"Violation",
]
