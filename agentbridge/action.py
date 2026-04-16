import inspect
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


PERMISSION_LEVELS = [
    "read_only",
    "write",
    "requires_approval",
    "restricted"
]


@dataclass
class ActionDefinition:
    """Represents a single registered action in the AgentBridge registry."""
    name: str
    description: str
    permissions: List[str]
    func: Callable
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    examples: Optional[List[Dict]] = field(default_factory=list)
    tags: Optional[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize action definition to Web MCP compatible dict."""
        return {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "permissions": self.permissions,
            "examples": self.examples or [],
            "tags": self.tags or []
        }


def extract_inputs_from_function(func: Callable) -> Dict[str, Any]:
    """
    Automatically extract input schema from Python function
    type annotations — no manual schema writing needed.
    """
    sig = inspect.signature(func)
    hints = func.__annotations__

    inputs = {}
    for param_name, param in sig.parameters.items():
        if param_name == "return":
            continue

        param_type = hints.get(param_name, Any)
        type_name = getattr(param_type, "__name__", str(param_type))

        inputs[param_name] = {
            "type": type_name,
            "required": param.default is inspect.Parameter.empty
        }

        # Include default value if present
        if param.default is not inspect.Parameter.empty:
            inputs[param_name]["default"] = param.default

    return inputs


def action(
    name: str,
    description: str,
    permissions: Optional[List[str]] = None,
    schema: Optional[Any] = None,
    outputs: Optional[Dict] = None,
    examples: Optional[List[Dict]] = None,
    tags: Optional[List[str]] = None
):
    """
    Decorator to register a function as an AgentBridge action.

    Usage:
        @bridge.action(
            name="get_order_status",
            description="Get the current status of a customer order",
            permissions=["read_only"]
        )
        def get_order_status(order_id: str):
            return {"status": "shipped"}
    """
    if permissions is None:
        permissions = ["read_only"]

    # Validate permissions
    for perm in permissions:
        if perm not in PERMISSION_LEVELS:
            raise ValueError(
                f"Invalid permission '{perm}'. "
                f"Must be one of: {PERMISSION_LEVELS}"
            )

    def decorator(func: Callable) -> Callable:
        # Prefer explicit schemas when provided, otherwise infer from type hints.
        if schema is not None and hasattr(schema, "inputs_to_dict"):
            inputs = schema.inputs_to_dict()
        else:
            inputs = extract_inputs_from_function(func)

        if schema is not None and hasattr(schema, "outputs_to_dict"):
            resolved_outputs = schema.outputs_to_dict()
        else:
            resolved_outputs = outputs or {}

        # Build the action definition
        action_def = ActionDefinition(
            name=name,
            description=description,
            permissions=permissions,
            func=func,
            inputs=inputs,
            outputs=resolved_outputs,
            examples=examples or [],
            tags=tags or []
        )

        # Attach metadata to the function for bridge to discover
        func._agentbridge_action = action_def
        return func

    return decorator
