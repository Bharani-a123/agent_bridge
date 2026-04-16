"""
AgentBridge Schemas

Defines typed input/output schemas for actions.
Use these to provide richer type information to AI agents
beyond what Python type hints alone can express.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


# ── Supported field types ─────────────────────────────────────────────────────

FIELD_TYPES = [
    "string",
    "int",
    "float",
    "bool",
    "array",
    "object",
    "any"
]


# ── Schema field definitions ──────────────────────────────────────────────────

@dataclass
class StringField:
    """A string input/output field."""
    description: str = ""
    required: bool = True
    default: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    enum: Optional[List[str]] = None  # Restrict to allowed values

    def to_dict(self) -> Dict:
        d = {"type": "string", "required": self.required}
        if self.description:
            d["description"] = self.description
        if self.default is not None:
            d["default"] = self.default
        if self.min_length is not None:
            d["min_length"] = self.min_length
        if self.max_length is not None:
            d["max_length"] = self.max_length
        if self.enum:
            d["enum"] = self.enum
        return d


@dataclass
class IntField:
    """An integer input/output field."""
    description: str = ""
    required: bool = True
    default: Optional[int] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None

    def to_dict(self) -> Dict:
        d = {"type": "int", "required": self.required}
        if self.description:
            d["description"] = self.description
        if self.default is not None:
            d["default"] = self.default
        if self.minimum is not None:
            d["minimum"] = self.minimum
        if self.maximum is not None:
            d["maximum"] = self.maximum
        return d


@dataclass
class FloatField:
    """A float input/output field."""
    description: str = ""
    required: bool = True
    default: Optional[float] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def to_dict(self) -> Dict:
        d = {"type": "float", "required": self.required}
        if self.description:
            d["description"] = self.description
        if self.default is not None:
            d["default"] = self.default
        if self.minimum is not None:
            d["minimum"] = self.minimum
        if self.maximum is not None:
            d["maximum"] = self.maximum
        return d


@dataclass
class BoolField:
    """A boolean input/output field."""
    description: str = ""
    required: bool = True
    default: Optional[bool] = None

    def to_dict(self) -> Dict:
        d = {"type": "bool", "required": self.required}
        if self.description:
            d["description"] = self.description
        if self.default is not None:
            d["default"] = self.default
        return d


@dataclass
class ArrayField:
    """An array input/output field."""
    description: str = ""
    required: bool = True
    items_type: str = "string"
    min_items: Optional[int] = None
    max_items: Optional[int] = None

    def to_dict(self) -> Dict:
        d = {
            "type": "array",
            "required": self.required,
            "items": {"type": self.items_type}
        }
        if self.description:
            d["description"] = self.description
        if self.min_items is not None:
            d["min_items"] = self.min_items
        if self.max_items is not None:
            d["max_items"] = self.max_items
        return d


@dataclass
class ObjectField:
    """A nested object input/output field."""
    description: str = ""
    required: bool = True
    properties: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = {"type": "object", "required": self.required}
        if self.description:
            d["description"] = self.description
        if self.properties:
            d["properties"] = {
                k: v.to_dict() if hasattr(v, "to_dict") else v
                for k, v in self.properties.items()
            }
        return d


# ── Full action schema ────────────────────────────────────────────────────────

class ActionSchema:
    """
    Define rich input/output schemas for AgentBridge actions.
    Use this when you want more control than Python type hints provide.

    Example:
        schema = ActionSchema(
            inputs={
                "order_id": StringField(description="The order ID to look up", min_length=3),
                "include_items": BoolField(description="Include line items", default=False)
            },
            outputs={
                "status": StringField(
                    description="Order status",
                    enum=["processing", "shipped", "delivered", "cancelled"]
                ),
                "delivery_date": StringField(description="Expected delivery date")
            }
        )

        @bridge.action(
            name="get_order_status",
            description="Get order status",
            permissions=["read_only"],
            schema=schema
        )
        def get_order_status(order_id: str, include_items: bool = False):
            ...
    """

    def __init__(
        self,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None
    ):
        self.inputs = inputs or {}
        self.outputs = outputs or {}

    def inputs_to_dict(self) -> Dict:
        return {
            k: v.to_dict() if hasattr(v, "to_dict") else v
            for k, v in self.inputs.items()
        }

    def outputs_to_dict(self) -> Dict:
        return {
            k: v.to_dict() if hasattr(v, "to_dict") else v
            for k, v in self.outputs.items()
        }

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate provided inputs against the schema.
        Returns dict with valid: bool and errors list.
        """
        errors = []

        for field_name, field_def in self.inputs.items():
            if not hasattr(field_def, "to_dict"):
                continue

            is_required = getattr(field_def, "required", True)
            has_default = getattr(field_def, "default", None) is not None

            # Check required fields
            if is_required and not has_default and field_name not in inputs:
                errors.append(f"Missing required field: '{field_name}'")
                continue

            if field_name not in inputs:
                continue

            value = inputs[field_name]

            # String validation
            if isinstance(field_def, StringField):
                if not isinstance(value, str):
                    errors.append(f"Field '{field_name}' must be a string")
                elif field_def.min_length and len(value) < field_def.min_length:
                    errors.append(f"Field '{field_name}' must be at least {field_def.min_length} characters")
                elif field_def.max_length and len(value) > field_def.max_length:
                    errors.append(f"Field '{field_name}' must be at most {field_def.max_length} characters")
                elif field_def.enum and value not in field_def.enum:
                    errors.append(f"Field '{field_name}' must be one of: {field_def.enum}")

            # Int validation
            elif isinstance(field_def, IntField):
                if not isinstance(value, int):
                    errors.append(f"Field '{field_name}' must be an integer")
                elif field_def.minimum is not None and value < field_def.minimum:
                    errors.append(f"Field '{field_name}' must be >= {field_def.minimum}")
                elif field_def.maximum is not None and value > field_def.maximum:
                    errors.append(f"Field '{field_name}' must be <= {field_def.maximum}")

            # Bool validation
            elif isinstance(field_def, BoolField):
                if not isinstance(value, bool):
                    errors.append(f"Field '{field_name}' must be a boolean")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }