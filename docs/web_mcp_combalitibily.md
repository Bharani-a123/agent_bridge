# AgentBridge — Web MCP Compatibility

This document explains how AgentBridge relates to Google's Web MCP standard
and how the two work together.

---

## What is Web MCP?

Web MCP (Model Context Protocol for the Web) is an open standard released by Google
that defines how AI agents should interact with web services and software systems.

It specifies:
- How agents discover what a system can do
- How agents make requests to systems
- How systems respond to agent requests

---

## How AgentBridge Relates to Web MCP

AgentBridge does **not** compete with Web MCP. It builds on top of it.

```
[ AI Agent ]
     ↓  speaks Web MCP
[ Web MCP Protocol Layer ]
     ↓  implemented by
[ AgentBridge ]              ← We are here
     ↓  wraps
[ Your Existing System ]
```

Web MCP defines the standard. AgentBridge is the implementation layer
that makes the standard work in the real world — especially for systems
that were never designed for agents.

---

## What AgentBridge Adds on Top of Web MCP

Web MCP defines the protocol. AgentBridge adds the enterprise features
that production systems require:

| Feature | Web MCP | AgentBridge |
|---|---|---|
| Structured action discovery | ✅ | ✅ |
| Input/output schemas | ✅ | ✅ |
| Standardized execution | ✅ | ✅ |
| Permission policies per agent | ❌ | ✅ |
| Human-in-the-loop approval | ❌ | ✅ |
| Restricted actions | ❌ | ✅ |
| Full audit logging | ❌ | ✅ |
| Framework adapters (FastAPI/Flask/Django) | ❌ | ✅ |
| Zero-rebuild wrapping of existing systems | ❌ | ✅ |

---

## The `/agent-registry` Endpoint

AgentBridge's primary output — the `/agent-registry` endpoint — is designed
to be fully Web MCP compatible.

A Web MCP compatible agent can point at any AgentBridge-powered system
and immediately understand:

- What actions are available
- What inputs each action requires
- What each action returns
- What permissions are needed

### Example Registry Response

```json
{
  "agentbridge_version": "0.1.0",
  "spec_version": "web-mcp-1.0",
  "web_mcp_compatible": true,
  "generated_at": "2026-04-16T00:00:00Z",
  "system": {
    "name": "E-Commerce Backend",
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
      "tags": ["orders"],
      "examples": []
    }
  ],
  "meta": {
    "total_actions": 1,
    "permission_levels": ["read_only", "write", "requires_approval", "restricted"]
  }
}
```

---

## The `/execute` Endpoint

The `/execute` endpoint follows Web MCP's action invocation pattern
with AgentBridge extensions for agent identity and policy:

### Request

```json
{
  "action": "get_order_status",
  "inputs": {
    "order_id": "ORD001"
  },
  "agent_id": "my-agent-001",
  "policy": "customer_service_bot"
}
```

The `agent_id` and `policy` fields are AgentBridge extensions.
They are optional — a plain Web MCP agent can call this endpoint
without them and it will work using the default permission policy.

### Success Response

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

### Requires Approval Response

```json
{
  "success": false,
  "requires_approval": true,
  "message": "Action 'cancel_order' requires human approval before execution",
  "pending_inputs": {
    "order_id": "ORD001",
    "reason": "customer request"
  }
}
```

---

## How a Web MCP Agent Uses AgentBridge

1. Agent discovers the system at `GET /agent-registry`
2. Agent reads the list of available actions and their schemas
3. Agent decides which action to call based on the task
4. Agent calls `POST /execute` with action name and inputs
5. AgentBridge checks permissions, executes, returns structured result
6. AgentBridge logs the action to the audit trail

---

## Migration Path

If you currently have systems built directly on Web MCP,
AgentBridge is fully compatible. You can:

- Run AgentBridge alongside existing Web MCP implementations
- Gradually migrate legacy systems behind the AgentBridge layer
- Use AgentBridge's permission and audit features even on Web MCP native systems

---

## Staying Up to Date

As the Web MCP standard evolves, AgentBridge will update its compatibility layer.
The `spec_version` field in the registry output reflects which version of Web MCP
the current output is compatible with.

Current compatibility: `web-mcp-1.0`

---

## Questions?

Open an issue on GitHub or join the discussion in the AgentBridge community.