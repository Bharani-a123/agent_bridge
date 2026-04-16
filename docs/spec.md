# AgentBridge Spec

AgentBridge defines a small, machine-readable interface for exposing application actions to AI agents.

## Core Concepts

- `system`: metadata about the wrapped application
- `actions`: the list of callable operations exposed to agents
- `permissions`: execution requirements for each action
- `inputs` and `outputs`: structured action schemas

## Required Endpoints

- `GET /agent-registry`: returns the action registry
- `POST /execute`: executes an action by name
- `GET /health`: returns service health

## Registry Shape

The registry response includes:

- `agentbridge_version`
- `spec_version`
- `web_mcp_compatible`
- `generated_at`
- `system`
- `actions`
- `meta`

## Action Shape

Each action includes:

- `name`
- `description`
- `inputs`
- `outputs`
- `permissions`
- `examples`
- `tags`

## Permission Levels

- `read_only`
- `write`
- `requires_approval`
- `restricted`

## Execution Request

`POST /execute` accepts:

```json
{
  "action": "get_order_status",
  "inputs": {
    "order_id": "ORD001"
  },
  "agent_id": "agent-123",
  "policy": "readonly_agent"
}
```

`agent_id` and `policy` are optional but recommended for auditing and scoped access.
