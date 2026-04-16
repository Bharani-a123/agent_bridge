# AgentBridge

Make Python systems agent-ready with a structured action registry for AI agents.

AgentBridge helps developers expose machine-readable actions instead of forcing agents to scrape pages, click buttons, or rely on brittle UI automation. It is designed as an open, practical bridge between agent frameworks and the messy reality of existing software systems.

## Why AgentBridge

Most software is still built for humans first:

- Agents scrape HTML instead of reading structured actions
- UI changes break automations in production
- Permissions are unclear or bolted on later
- Error handling and auditability are inconsistent

AgentBridge gives your application a clean, declared interface that agents can discover and use safely.

## What It Does

- Registers actions from normal Python functions
- Extracts input schemas from type hints
- Exposes a structured `/agent-registry` endpoint
- Executes actions through a stable `/execute` endpoint
- Adds permission-aware execution controls
- Supports framework adapters for FastAPI, Flask, and Django

## Install

```bash
pip install agentbridge
```

Optional extras:

```bash
pip install "agentbridge[fastapi]"
pip install "agentbridge[flask]"
pip install "agentbridge[django]"
pip install "agentbridge[all]"
```

## Quickstart

```python
from agentbridge.bridge import AgentBridge

bridge = AgentBridge(
    system_name="Demo E-Commerce System",
    system_description="Order management and product catalog",
    port=8090,
)

@bridge.action(
    name="get_order_status",
    description="Get the current status of a customer order",
    permissions=["read_only"],
    tags=["orders"],
)
def get_order_status(order_id: str):
    return {"status": "shipped", "delivery_date": "2026-04-15"}

bridge.serve()
```

Once running, AgentBridge exposes:

- `GET /agent-registry`
- `POST /execute`
- `GET /health`

## Example Registry Output

```json
{
  "agentbridge_version": "0.1.0",
  "spec_version": "web-mcp-1.0",
  "web_mcp_compatible": true,
  "system": {
    "name": "Demo E-Commerce System",
    "description": "Order management and product catalog",
    "version": "1.0.0"
  },
  "actions": [
    {
      "name": "get_order_status",
      "description": "Get the current status of a customer order",
      "inputs": {
        "order_id": {
          "type": "str",
          "required": true
        }
      },
      "outputs": {},
      "permissions": ["read_only"],
      "examples": [],
      "tags": ["orders"]
    }
  ]
}
```

## Execute an Action

```bash
curl -X POST http://localhost:8090/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"action\":\"get_order_status\",\"inputs\":{\"order_id\":\"ORD001\"}}"
```

Example response:

```json
{
  "success": true,
  "action": "get_order_status",
  "result": {
    "status": "shipped",
    "delivery_date": "2026-04-15"
  }
}
```

## Permissions

Supported permission levels:

- `read_only`
- `write`
- `requires_approval`
- `restricted`

You can also define named policies:

```python
from agentbridge.permissions import PermissionPolicy, PermissionLevel

bridge.permissions.add_policy(PermissionPolicy(
    name="readonly_agent",
    max_permission_level=PermissionLevel.READ_ONLY,
))
```

Then execute using that policy:

```python
result = bridge.execute(
    "get_order_status",
    {"order_id": "ORD001"},
    agent_id="agent-123",
    policy_name="readonly_agent",
)
```

## Framework Adapters

AgentBridge includes adapters for:

- FastAPI
- Flask
- Django

See the `adapters/` directory and `examples/` for integration patterns.

## Project Layout

```text
agentbridge/
├── agentbridge/
├── adapters/
├── examples/
├── tests/
├── docs/
└── .github/workflows/
```

## Docs

- [Quickstart](./docs/quickstart.md)
- [Spec](./docs/spec.md)
- [Web MCP compatibility notes](./docs/web-mcp-compatibility.md)
- [Contributing](./CONTRIBUTING.md)

## Status

AgentBridge is currently alpha software. The core idea is in place, and the project is intended to evolve into an open standard plus implementation layer for agent-interaction-centric systems.

## License

MIT
