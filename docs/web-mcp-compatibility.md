# AgentBridge - Web MCP Compatibility

This document explains how AgentBridge fits alongside Web MCP-style agent integrations.

## Positioning

AgentBridge is an implementation layer for making existing systems easier for agents to use.
It focuses on:

- structured action discovery
- stable execution endpoints
- permission policies
- audit logging
- framework adapters

## Compatibility Surface

AgentBridge exposes:

- `GET /agent-registry`
- `POST /execute`
- `GET /health`
- `GET /audit/summary`
- `GET /audit/logs`

The registry is machine-readable and intended to be easy for agent runtimes to consume.

## Extensions

AgentBridge adds a few practical fields beyond plain action discovery:

- `permissions` for each action
- `policy` on execution requests
- `agent_id` for traceability
- audit endpoints for visibility

## Example Execution Request

```json
{
  "action": "get_order_status",
  "inputs": {
    "order_id": "ORD001"
  },
  "agent_id": "agent-001",
  "policy": "customer_service_bot"
}
```

## Why This Layer Exists

Many production systems still expose data and workflows in ways that are friendly to human users but awkward for agents. AgentBridge provides a clearer application-facing interface without requiring a full rewrite.
