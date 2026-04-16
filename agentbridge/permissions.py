from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class PermissionLevel(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    REQUIRES_APPROVAL = "requires_approval"
    RESTRICTED = "restricted"


@dataclass
class PermissionPolicy:
    """
    Defines a permission policy for an agent role.
    Use this to control what different agents can access.

    Example:
        policy = PermissionPolicy(
            name="customer_service_agent",
            allowed_actions=["get_order_status", "list_products"],
            denied_actions=["cancel_order", "delete_customer"]
        )
    """
    name: str
    allowed_actions: Optional[List[str]] = None   # None means all allowed
    denied_actions: Optional[List[str]] = None    # None means none denied
    max_permission_level: PermissionLevel = PermissionLevel.READ_ONLY

    def can_execute(self, action_name: str, action_permissions: List[str]) -> bool:
        """Check if this policy allows execution of a given action."""

        # Restricted actions are always blocked
        if PermissionLevel.RESTRICTED in action_permissions:
            return False

        # Check denied list
        if self.denied_actions and action_name in self.denied_actions:
            return False

        # Check allowed list
        if self.allowed_actions and action_name not in self.allowed_actions:
            return False

        # Check permission level ceiling
        permission_order = [
            PermissionLevel.READ_ONLY,
            PermissionLevel.WRITE,
            PermissionLevel.REQUIRES_APPROVAL,
            PermissionLevel.RESTRICTED
        ]

        max_index = permission_order.index(self.max_permission_level)
        for perm in action_permissions:
            try:
                perm_level = PermissionLevel(perm)
                if permission_order.index(perm_level) > max_index:
                    return False
            except ValueError:
                continue

        return True


class PermissionManager:
    """
    Manages permission policies for AgentBridge.
    Allows different agents to have different access levels.

    Example:
        manager = PermissionManager()

        manager.add_policy(PermissionPolicy(
            name="readonly_agent",
            max_permission_level=PermissionLevel.READ_ONLY
        ))

        manager.add_policy(PermissionPolicy(
            name="ops_agent",
            allowed_actions=["get_order_status", "cancel_order"],
            max_permission_level=PermissionLevel.WRITE
        ))
    """

    def __init__(self):
        self._policies: Dict[str, PermissionPolicy] = {}
        self._default_policy = PermissionPolicy(
            name="default",
            max_permission_level=PermissionLevel.WRITE
        )

    def add_policy(self, policy: PermissionPolicy):
        """Register a named permission policy."""
        self._policies[policy.name] = policy
        print(f"[AgentBridge] Permission policy registered: '{policy.name}'")

    def set_default_policy(self, policy: PermissionPolicy):
        """Set the default policy applied when no specific policy is matched."""
        self._default_policy = policy

    def get_policy(self, policy_name: Optional[str] = None) -> PermissionPolicy:
        """Retrieve a policy by name, or return default."""
        if policy_name and policy_name in self._policies:
            return self._policies[policy_name]
        return self._default_policy

    def check(
        self,
        action_name: str,
        action_permissions: List[str],
        policy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if an action can be executed under a given policy.
        Returns a result dict with allowed status and reason.
        """
        policy = self.get_policy(policy_name)

        if PermissionLevel.RESTRICTED in action_permissions:
            return {
                "allowed": False,
                "reason": f"Action '{action_name}' is restricted",
                "policy": policy.name
            }

        if PermissionLevel.REQUIRES_APPROVAL in action_permissions:
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": f"Action '{action_name}' requires human approval",
                "policy": policy.name
            }

        allowed = policy.can_execute(action_name, action_permissions)

        return {
            "allowed": allowed,
            "reason": "Permission granted" if allowed else f"Policy '{policy.name}' does not allow this action",
            "policy": policy.name
        }