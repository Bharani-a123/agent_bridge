# AgentBridge Quickstart Guide

Get your system agent-ready in under 5 minutes.

---

## Installation

```bash
pip install agentbridge
```

---

## Step 1 — Create a bridge

```python
from agentbridge import AgentBridge

bridge = AgentBridge(
    system_name="My System",
    system_description="What your system does"
)
```

---

## Step 2 — Register your actions

Wrap your existing functions with the `@bridge.action` decorator:

```python
@bridge.action(
    name="get_order_status",
    description="Get the current status of a customer order",
    permissions=["read_only"]
)
def get_order_status(order_id: str):
    # Your existing code — unchanged
    return {"status": "shipped", "delivery_date": "2026-04-15"}
```

That's it. AgentBridge automatically reads your type hints and builds the input schema.

---

## Step 3 — Start the server

```python
bridge.serve()
```

Your system is now agent-ready at:

| Endpoint | Method | What it does |
|---|---|---|
| `/agent-registry` | GET | Returns full Web MCP compatible action registry |
| `/execute` | POST | Executes an action by name |
| `/audit/summary` | GET | Returns audit summary of all agent actions |
| `/audit/logs` | GET | Returns detailed audit logs |
| `/health` | GET | Health check |

---

## Calling the registry

Any AI agent can now discover what your system can do:

```bash
curl http://localhost:8090/agent-registry
```

Response:
```json
{
  "agentbridge_version": "0.1.0",
  "web_mcp_compatible": true,
  "system": {
    "name": "My System"
  },
  "actions": [
    {
      "name": "get_order_status",
      "description": "Get the current status of a customer order",
      "inputs": {
        "order_id": { "type": "str", "required": true }
      },
      "permissions": ["read_only"]
    }
  ]
}
```

---

## Executing an action

```bash
curl -X POST http://localhost:8090/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "get_order_status", "inputs": {"order_id": "ORD001"}}'
```

Response:
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

---

## Permission levels

| Level | What it means |
|---|---|
| `read_only` | Agent can read data, cannot change anything |
| `write` | Agent can make changes |
| `requires_approval` | Agent must wait for human approval |
| `restricted` | Declared but blocked for all agents |

---

## Using with FastAPI

```python
from fastapi import FastAPI
from agentbridge import AgentBridge
from agentbridge.adapters import FastAPIAdapter

app = FastAPI()
bridge = AgentBridge(adapter=FastAPIAdapter(app))

@bridge.action(name="get_data", description="Get data", permissions=["read_only"])
def get_data(id: str):
    return {"id": id, "data": "..."}

# Start with: uvicorn myapp:app
```

---

## Using with Flask

```python
from flask import Flask
from agentbridge import AgentBridge
from agentbridge.adapters import FlaskAdapter

app = Flask(__name__)
bridge = AgentBridge(adapter=FlaskAdapter(app))

@bridge.action(name="get_data", description="Get data", permissions=["read_only"])
def get_data(id: str):
    return {"id": id, "data": "..."}

# Start with: flask run
```

---

## Permission policies

Control what different agents can and cannot do:

```python
from agentbridge.permissions import PermissionPolicy, PermissionLevel

# Read-only bot — can only read
bridge.permissions.add_policy(PermissionPolicy(
    name="customer_bot",
    max_permission_level=PermissionLevel.READ_ONLY
))

# Ops agent — can read and write, but not specific actions
bridge.permissions.add_policy(PermissionPolicy(
    name="ops_agent",
    denied_actions=["delete_customer"],
    max_permission_level=PermissionLevel.WRITE
))
```

Then agents pass their policy name when executing:

```json
{
  "action": "get_order_status",
  "inputs": {"order_id": "ORD001"},
  "agent_id": "my-agent-123",
  "policy": "customer_bot"
}
```

---

## Audit logs

Every action is automatically logged:

```bash
curl http://localhost:8090/audit/summary
```

```json
{
  "total_actions": 47,
  "total_success": 45,
  "total_failure": 2,
  "success_rate": 95.74,
  "action_breakdown": {
    "get_order_status": 30,
    "list_products": 17
  }
}
```

Export for compliance:

```python
bridge.audit.export_json("audit_report_2026_04.json")
```

---

## Next steps

- Read the [Open Spec](./spec.md) to understand the full registry format
- See [Web MCP Compatibility](./web-mcp-compatibility.md) for integration details
- Check the [examples/](../examples/) folder for real world usage
