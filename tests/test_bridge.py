import sys
import json
import pytest
sys.path.insert(0, '..')

from agentbridge import AgentBridge
from agentbridge.permissions import PermissionPolicy, PermissionLevel


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_bridge():
    """Create a fresh bridge with sample actions for each test."""
    bridge = AgentBridge(
        system_name="Test System",
        system_description="For testing only"
    )

    @bridge.action(
        name="get_order",
        description="Get order by ID",
        permissions=["read_only"],
        tags=["orders"]
    )
    def get_order(order_id: str):
        return {"order_id": order_id, "status": "shipped"}

    @bridge.action(
        name="update_order",
        description="Update an order",
        permissions=["write"],
        tags=["orders"]
    )
    def update_order(order_id: str, status: str):
        return {"updated": True, "order_id": order_id, "status": status}

    @bridge.action(
        name="delete_order",
        description="Delete an order — requires approval",
        permissions=["write", "requires_approval"],
        tags=["orders"]
    )
    def delete_order(order_id: str):
        return {"deleted": True}

    @bridge.action(
        name="get_secret",
        description="Restricted action",
        permissions=["restricted"]
    )
    def get_secret():
        return {"secret": "top_secret"}

    return bridge


# ─── Registry Tests ───────────────────────────────────────────────────────────

class TestRegistry:

    def test_registry_has_correct_structure(self):
        bridge = make_bridge()
        registry = bridge.get_registry()
        assert "agentbridge_version" in registry
        assert "web_mcp_compatible" in registry
        assert registry["web_mcp_compatible"] is True
        assert "actions" in registry
        assert "system" in registry

    def test_registry_lists_all_actions(self):
        bridge = make_bridge()
        registry = bridge.get_registry()
        action_names = [a["name"] for a in registry["actions"]]
        assert "get_order" in action_names
        assert "update_order" in action_names
        assert "delete_order" in action_names
        assert "get_secret" in action_names

    def test_registry_action_has_inputs(self):
        bridge = make_bridge()
        registry = bridge.get_registry()
        get_order = next(a for a in registry["actions"] if a["name"] == "get_order")
        assert "order_id" in get_order["inputs"]
        assert get_order["inputs"]["order_id"]["required"] is True

    def test_registry_action_has_permissions(self):
        bridge = make_bridge()
        registry = bridge.get_registry()
        get_order = next(a for a in registry["actions"] if a["name"] == "get_order")
        assert "read_only" in get_order["permissions"]

    def test_duplicate_action_raises_error(self):
        bridge = make_bridge()
        with pytest.raises(ValueError, match="already registered"):
            @bridge.action(name="get_order", description="duplicate", permissions=["read_only"])
            def get_order_duplicate(order_id: str):
                return {}

    def test_invalid_permission_raises_error(self):
        bridge = AgentBridge()
        with pytest.raises(ValueError, match="Invalid permission"):
            @bridge.action(name="bad_action", description="test", permissions=["superadmin"])
            def bad_action():
                return {}


# ─── Execution Tests ──────────────────────────────────────────────────────────

class TestExecution:

    def test_execute_read_only_action(self):
        bridge = make_bridge()
        result = bridge.execute("get_order", {"order_id": "ORD123"})
        assert result["success"] is True
        assert result["result"]["order_id"] == "ORD123"

    def test_execute_write_action(self):
        bridge = make_bridge()
        result = bridge.execute("update_order", {"order_id": "ORD123", "status": "delivered"})
        assert result["success"] is True
        assert result["result"]["updated"] is True

    def test_execute_requires_approval_is_blocked(self):
        bridge = make_bridge()
        result = bridge.execute("delete_order", {"order_id": "ORD123"})
        assert result["success"] is False
        assert result.get("requires_approval") is True

    def test_execute_restricted_action_is_blocked(self):
        bridge = make_bridge()
        result = bridge.execute("get_secret", {})
        assert result["success"] is False
        assert "restricted" in result["error"].lower()

    def test_execute_unknown_action(self):
        bridge = make_bridge()
        result = bridge.execute("nonexistent_action", {})
        assert result["success"] is False
        assert "not found" in result["error"].lower()
        assert "available_actions" in result

    def test_execute_with_wrong_inputs(self):
        bridge = make_bridge()
        result = bridge.execute("get_order", {})  # missing order_id
        assert result["success"] is False
        assert "Invalid inputs" in result["error"]


# ─── Permission Tests ─────────────────────────────────────────────────────────

class TestPermissions:

    def test_readonly_policy_blocks_write(self):
        bridge = make_bridge()
        bridge.permissions.add_policy(PermissionPolicy(
            name="readonly_agent",
            max_permission_level=PermissionLevel.READ_ONLY
        ))
        result = bridge.execute("update_order", {"order_id": "ORD1", "status": "done"}, policy_name="readonly_agent")
        assert result["success"] is False

    def test_readonly_policy_allows_read(self):
        bridge = make_bridge()
        bridge.permissions.add_policy(PermissionPolicy(
            name="readonly_agent",
            max_permission_level=PermissionLevel.READ_ONLY
        ))
        result = bridge.execute("get_order", {"order_id": "ORD1"}, policy_name="readonly_agent")
        assert result["success"] is True

    def test_denied_actions_are_blocked(self):
        bridge = make_bridge()
        bridge.permissions.add_policy(PermissionPolicy(
            name="limited_agent",
            denied_actions=["update_order"],
            max_permission_level=PermissionLevel.WRITE
        ))
        result = bridge.execute("update_order", {"order_id": "ORD1", "status": "done"}, policy_name="limited_agent")
        assert result["success"] is False

    def test_allowed_actions_list_works(self):
        bridge = make_bridge()
        bridge.permissions.add_policy(PermissionPolicy(
            name="scoped_agent",
            allowed_actions=["get_order"],
            max_permission_level=PermissionLevel.WRITE
        ))
        result = bridge.execute("update_order", {"order_id": "ORD1", "status": "done"}, policy_name="scoped_agent")
        assert result["success"] is False

        result2 = bridge.execute("get_order", {"order_id": "ORD1"}, policy_name="scoped_agent")
        assert result2["success"] is True


# ─── Audit Tests ──────────────────────────────────────────────────────────────

class TestAudit:

    def test_audit_logs_successful_action(self):
        bridge = make_bridge()
        bridge.execute("get_order", {"order_id": "ORD1"}, agent_id="agent-001")
        logs = bridge.audit.get_logs()
        assert len(logs) == 1
        assert logs[0]["action_name"] == "get_order"
        assert logs[0]["success"] is True
        assert logs[0]["agent_id"] == "agent-001"

    def test_audit_logs_failed_action(self):
        bridge = make_bridge()
        bridge.execute("get_secret", {})
        logs = bridge.audit.get_logs()
        assert len(logs) == 1
        assert logs[0]["success"] is False

    def test_audit_summary_is_correct(self):
        bridge = make_bridge()
        bridge.execute("get_order", {"order_id": "ORD1"})
        bridge.execute("get_order", {"order_id": "ORD2"})
        bridge.execute("get_secret", {})
        summary = bridge.audit.get_summary()
        assert summary["total_actions"] == 3
        assert summary["total_success"] == 2
        assert summary["total_failure"] == 1

    def test_audit_filter_by_action(self):
        bridge = make_bridge()
        bridge.execute("get_order", {"order_id": "ORD1"})
        bridge.execute("update_order", {"order_id": "ORD1", "status": "done"})
        logs = bridge.audit.get_logs(action_name="get_order")
        assert len(logs) == 1
        assert logs[0]["action_name"] == "get_order"

    def test_audit_disabled(self):
        bridge = AgentBridge(enable_audit=False)
        assert bridge.audit is None


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])