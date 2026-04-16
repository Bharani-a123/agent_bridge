"""
AgentBridge — CRM Example

Shows how a CRM system (like Salesforce or HubSpot style)
would use AgentBridge to become agent-ready.

An AI agent using this registry can:
- Look up contacts and companies
- Create and update leads
- Log activities
- Search the pipeline
"""

import sys
sys.path.insert(0, '..')

from agentbridge import AgentBridge
from agentbridge.permissions import PermissionPolicy, PermissionLevel

bridge = AgentBridge(
    system_name="CRM System",
    system_description="Customer relationship management — contacts, leads, deals, and activities",
    port=8091
)

# Different agents get different access levels
bridge.permissions.add_policy(PermissionPolicy(
    name="sales_bot",
    allowed_actions=["get_contact", "search_contacts", "list_deals", "get_deal"],
    max_permission_level=PermissionLevel.READ_ONLY
))

bridge.permissions.add_policy(PermissionPolicy(
    name="sales_agent",
    denied_actions=["delete_contact"],
    max_permission_level=PermissionLevel.WRITE
))


# ─── Contact Actions ──────────────────────────────────────────────────────────

@bridge.action(
    name="get_contact",
    description="Get a contact's full profile by their ID",
    permissions=["read_only"],
    tags=["contacts"]
)
def get_contact(contact_id: str):
    contacts = {
        "C001": {
            "id": "C001", "name": "Priya Sharma", "email": "priya@techcorp.com",
            "company": "TechCorp", "title": "CTO", "phone": "+91-98765-43210",
            "status": "active", "created_at": "2026-01-15"
        },
        "C002": {
            "id": "C002", "name": "James Miller", "email": "james@startup.io",
            "company": "StartupIO", "title": "CEO", "phone": "+1-555-0192",
            "status": "active", "created_at": "2026-02-20"
        }
    }
    if contact_id not in contacts:
        return {"error": f"Contact '{contact_id}' not found"}
    return contacts[contact_id]


@bridge.action(
    name="search_contacts",
    description="Search contacts by name, company, or email",
    permissions=["read_only"],
    tags=["contacts"]
)
def search_contacts(query: str, limit: int = 10):
    all_contacts = [
        {"id": "C001", "name": "Priya Sharma", "company": "TechCorp", "email": "priya@techcorp.com"},
        {"id": "C002", "name": "James Miller", "company": "StartupIO", "email": "james@startup.io"},
        {"id": "C003", "name": "Aisha Khan", "company": "DataFlow", "email": "aisha@dataflow.ai"},
    ]
    q = query.lower()
    results = [
        c for c in all_contacts
        if q in c["name"].lower() or q in c["company"].lower() or q in c["email"].lower()
    ]
    return {"results": results[:limit], "total": len(results), "query": query}


@bridge.action(
    name="create_contact",
    description="Create a new contact in the CRM",
    permissions=["write"],
    tags=["contacts"]
)
def create_contact(name: str, email: str, company: str, title: str = ""):
    return {
        "created": True,
        "contact": {
            "id": "C_NEW_001",
            "name": name,
            "email": email,
            "company": company,
            "title": title,
            "status": "active"
        }
    }


@bridge.action(
    name="update_contact",
    description="Update an existing contact's details",
    permissions=["write"],
    tags=["contacts"]
)
def update_contact(contact_id: str, field: str, value: str):
    allowed_fields = ["name", "email", "company", "title", "phone", "status"]
    if field not in allowed_fields:
        return {"error": f"Cannot update field '{field}'. Allowed: {allowed_fields}"}
    return {
        "updated": True,
        "contact_id": contact_id,
        "field": field,
        "new_value": value
    }


@bridge.action(
    name="delete_contact",
    description="Permanently delete a contact — requires human approval",
    permissions=["write", "requires_approval"],
    tags=["contacts"]
)
def delete_contact(contact_id: str, reason: str):
    return {"deleted": True, "contact_id": contact_id, "reason": reason}


# ─── Deal / Pipeline Actions ──────────────────────────────────────────────────

@bridge.action(
    name="list_deals",
    description="List all deals in the pipeline with their stage and value",
    permissions=["read_only"],
    tags=["deals"]
)
def list_deals(stage: str = "all", min_value: float = 0):
    deals = [
        {"id": "D001", "name": "TechCorp Enterprise", "stage": "proposal", "value": 50000, "contact_id": "C001"},
        {"id": "D002", "name": "StartupIO Starter", "stage": "negotiation", "value": 5000, "contact_id": "C002"},
        {"id": "D003", "name": "DataFlow Pro", "stage": "closed_won", "value": 25000, "contact_id": "C003"},
        {"id": "D004", "name": "MegaCorp Deal", "stage": "prospecting", "value": 150000, "contact_id": "C001"},
    ]
    if stage != "all":
        deals = [d for d in deals if d["stage"] == stage]
    deals = [d for d in deals if d["value"] >= min_value]
    total_value = sum(d["value"] for d in deals)
    return {"deals": deals, "total": len(deals), "total_value": total_value}


@bridge.action(
    name="get_deal",
    description="Get full details of a specific deal by ID",
    permissions=["read_only"],
    tags=["deals"]
)
def get_deal(deal_id: str):
    deals = {
        "D001": {
            "id": "D001", "name": "TechCorp Enterprise", "stage": "proposal",
            "value": 50000, "contact_id": "C001", "probability": 60,
            "expected_close": "2026-05-30", "notes": "Decision maker is CTO"
        }
    }
    if deal_id not in deals:
        return {"error": f"Deal '{deal_id}' not found"}
    return deals[deal_id]


@bridge.action(
    name="update_deal_stage",
    description="Move a deal to a new stage in the pipeline",
    permissions=["write"],
    tags=["deals"]
)
def update_deal_stage(deal_id: str, new_stage: str):
    valid_stages = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
    if new_stage not in valid_stages:
        return {"error": f"Invalid stage. Must be one of: {valid_stages}"}
    return {
        "updated": True,
        "deal_id": deal_id,
        "new_stage": new_stage
    }


# ─── Activity Actions ─────────────────────────────────────────────────────────

@bridge.action(
    name="log_activity",
    description="Log a sales activity — call, email, meeting, or note",
    permissions=["write"],
    tags=["activities"]
)
def log_activity(contact_id: str, activity_type: str, summary: str):
    valid_types = ["call", "email", "meeting", "note", "demo"]
    if activity_type not in valid_types:
        return {"error": f"Invalid activity type. Must be one of: {valid_types}"}
    return {
        "logged": True,
        "activity_id": "ACT_NEW_001",
        "contact_id": contact_id,
        "type": activity_type,
        "summary": summary
    }


@bridge.action(
    name="get_contact_activities",
    description="Get all logged activities for a specific contact",
    permissions=["read_only"],
    tags=["activities"]
)
def get_contact_activities(contact_id: str, limit: int = 20):
    activities = [
        {"id": "ACT001", "type": "call", "summary": "Intro call, interested in enterprise plan", "date": "2026-04-01"},
        {"id": "ACT002", "type": "email", "summary": "Sent pricing proposal", "date": "2026-04-03"},
        {"id": "ACT003", "type": "meeting", "summary": "Product demo completed, positive feedback", "date": "2026-04-08"},
    ]
    return {
        "contact_id": contact_id,
        "activities": activities[:limit],
        "total": len(activities)
    }


if __name__ == "__main__":
    bridge.serve()