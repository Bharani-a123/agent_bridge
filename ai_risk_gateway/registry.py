"""Policy registry utilities."""

from __future__ import annotations

from collections import OrderedDict

from ai_risk_gateway.policies.base import BasePolicy


class PolicyRegistry:
	"""Registry for adding and retrieving policy instances by name."""

	def __init__(self) -> None:
		"""Initialize an empty policy registry."""
		self._policies: "OrderedDict[str, BasePolicy]" = OrderedDict()

	def register(self, policy: BasePolicy) -> None:
		"""Register or replace a policy using its declared name."""
		self._policies[policy.name] = policy

	def list_policies(self) -> list[BasePolicy]:
		"""Return policies in insertion order."""
		return list(self._policies.values())