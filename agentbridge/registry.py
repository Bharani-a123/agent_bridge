from typing import Any, Dict, List, Optional
from datetime import datetime
from .action import ActionDefinition

AGENTBRIDGE_VERSION = "0.1.0"
SPEC_VERSION = "web-mcp-1.0"


class Registry:
    """
    Builds and maintains the structured action registry.
    Outputs Web MCP compatible JSON that any AI agent can read.
    """

    def __init__(
        self,
        system_name: str = "AgentBridge System",
        system_description: str = "",
        version: str = "1.0.0"
    ):
        self.system_name = system_name
        self.system_description = system_description
        self.version = version
        self._actions: Dict[str, ActionDefinition] = {}

    def register(self, action_def: ActionDefinition):
        """Register an action definition into the registry."""
        if action_def.name in self._actions:
            raise ValueError(
                f"Action '{action_def.name}' is already registered. "
                f"Each action must have a unique name."
            )
        self._actions[action_def.name] = action_def
        print(f"[AgentBridge] Registered action: '{action_def.name}'")

    def get_action(self, name: str) -> Optional[ActionDefinition]:
        """Retrieve a single action by name."""
        return self._actions.get(name)

    def all_actions(self) -> List[ActionDefinition]:
        """Return all registered actions."""
        return list(self._actions.values())

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the full registry to a Web MCP compatible dict.
        This is what gets served at /agent-registry endpoint.
        """
        return {
            "agentbridge_version": AGENTBRIDGE_VERSION,
            "spec_version": SPEC_VERSION,
            "web_mcp_compatible": True,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "system": {
                "name": self.system_name,
                "description": self.system_description,
                "version": self.version
            },
            "actions": [
                action.to_dict()
                for action in self._actions.values()
            ],
            "meta": {
                "total_actions": len(self._actions),
                "permission_levels": [
                    "read_only",
                    "write",
                    "requires_approval",
                    "restricted"
                ]
            }
        }

    def summary(self) -> str:
        """Print a human readable summary of the registry."""
        lines = [
            f"\n{'='*50}",
            f"AgentBridge Registry — {self.system_name}",
            f"{'='*50}",
            f"Total actions registered: {len(self._actions)}",
            ""
        ]
        for name, action in self._actions.items():
            lines.append(f"  ✓ {name}")
            lines.append(f"    {action.description}")
            lines.append(f"    Permissions: {', '.join(action.permissions)}")
            lines.append("")
        lines.append("="*50)
        return "\n".join(lines)