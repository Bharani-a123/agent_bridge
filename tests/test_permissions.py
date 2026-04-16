"""
Tests for AgentBridge Permission layer.
"""
import sys
sys.path.insert(0, '..')

import pytest
from agentbridge import AgentBridge
from agentbridge.permissions import PermissionManager, PermissionPolicy, PermissionLevel


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_bridge_with_actions():
    bridge = AgentBridge(system_name="Permission Test Bridge")

    @bridge.action(name="read_data", description="Read", permissions=["read_only"])
    def read_data(id: str):
        return {"data": id}

    @bridge.action(name="write_data", description="Write", permissions=["write"])
    def write_data(key: str, value: str):
        return {"written": True}

    @bridge.action(name="approve_action", description="Needs approval", permissions=["write", "requires_approval"])
    def approve_action(target: str):
        return {"done": True}

    @bridge.action(name="restricted_action", description="Restricted", permissions=["restricted"])
    def restricted_action():
        return {"data": "secret"}

    return bridge


# ── PermissionManager Tests ───────────────────────────────────────────────────

class TestPermissionManager:

    def test_default_policy_allows_read(self):
        manager = PermissionManager()
        result = manager.check("some_action", ["read_only"])
        assert result["allowed"] is True

    def test_default_policy_allows_write(self):
        manager = PermissionManager()
        result = manager.check("some_action", ["write"])
        assert result["allowed"] is True

    def test_restricted_always_blocked(self):
        manager = PermissionManager()
        result = manager.check("secret", ["restricted"])
        assert result["allowed"] is False
        assert "restricted" in result["reason"].lower()

    def test_requires_approval_blocked(self):
        manager = PermissionManager()
        result = manager.check("action", ["write", "requires_approval"])
        assert result["allowed"] is False
        assert result.get("requires_approval") is True

    def test_add_policy(self):
        manager = PermissionManager()
        policy = PermissionPolicy(name="my_policy", max_permission_level=PermissionLevel.READ_ONLY)
        manager.add_policy(policy)
        retrieved = manager.get_policy("my_policy")
        assert retrieved.name == "my_policy"

    def test_unknown_policy_uses_default(self):
        manager = PermissionManager()
        result = manager.check("action", ["read_only"], policy_name="nonexistent_policy")
        assert result["allowed"] is True  # default allows read

    def test_set_custom_default_policy(self):
        manager = PermissionManager()
        strict = PermissionPolicy(
            name="strict_default",
            allowed_actions=["get_data"],
            max_permission_level=PermissionLevel.READ_ONLY
        )
        manager.set_default_policy(strict)
        result = manager.check("some_other_action", ["read_only"])
        assert result["allowed"] is False


# ── PermissionPolicy Tests ────────────────────────────────────────────────────

class TestPermissionPolicy:

    def test_read_only_policy_blocks_write(self):
        policy = PermissionPolicy(name="ro", max_permission_level=PermissionLevel.READ_ONLY)
        assert policy.can_execute("any_action", ["write"]) is False

    def test_read_only_policy_allows_read(self):
        policy = PermissionPolicy(name="ro", max_permission_level=PermissionLevel.READ_ONLY)
        assert policy.can_execute("any_action", ["read_only"]) is True

    def test_write_policy_allows_write(self):
        policy = PermissionPolicy(name="rw", max_permission_level=PermissionLevel.WRITE)
        assert policy.can_execute("any_action", ["write"]) is True

    def test_denied_actions_blocks(self):
        policy = PermissionPolicy(
            name="limited",
            denied_actions=["dangerous_op"],
            max_permission_level=PermissionLevel.WRITE
        )
        assert policy.can_execute("dangerous_op", ["write"]) is False
        assert policy.can_execute("safe_op", ["write"]) is True

    def test_allowed_actions_whitelist(self):
        policy = PermissionPolicy(
            name="scoped",
            allowed_actions=["read_orders", "read_products"],
            max_permission_level=PermissionLevel.READ_ONLY
        )
        assert policy.can_execute("read_orders", ["read_only"]) is True
        assert policy.can_execute("read_products", ["read_only"]) is True
        assert policy.can_execute("read_customers", ["read_only"]) is False

    def test_restricted_always_blocked_by_policy(self):
        policy = PermissionPolicy(
            name="superadmin",
            max_permission_level=PermissionLevel.WRITE
        )
        assert policy.can_execute("secret", ["restricted"]) is False

    def test_empty_policy_allows_nothing_outside_level(self):
        policy = PermissionPolicy(
            name="read_only_agent",
            max_permission_level=PermissionLevel.READ_ONLY
        )
        assert policy.can_execute("action", ["read_only"]) is True
        assert policy.can_execute("action", ["write"]) is False


# ── Integration: Bridge + Permissions ─────────────────────────────────────────

class TestBridgePermissionIntegration:

    def test_no_policy_allows_read(self):
        bridge = make_bridge_with_actions()
        r = bridge.execute("read_data", {"id": "123"})
        assert r["success"] is True

    def test_no_policy_allows_write(self):
        bridge = make_bridge_with_actions()
        r = bridge.execute("write_data", {"key": "x", "value": "y"})
        assert r["success"] is True

    def test_no_policy_blocks_restricted(self):
        bridge = make_bridge_with_actions()
        r = bridge.execute("restricted_action", {})
        assert r["success"] is False

    def test_no_policy_blocks_requires_approval(self):
        bridge = make_bridge_with_actions()
        r = bridge.execute("approve_action", {"target": "x"})
        assert r["success"] is False
        assert r.get("requires_approval") is True

    def test_readonly_policy_blocks_write(self):
        bridge = make_bridge_with_actions()
        bridge.permissions.add_policy(PermissionPolicy(
            name="ro_agent",
            max_permission_level=PermissionLevel.READ_ONLY
        ))
        r = bridge.execute("write_data", {"key": "x", "value": "y"}, policy_name="ro_agent")
        assert r["success"] is False

    def test_readonly_policy_allows_read(self):
        bridge = make_bridge_with_actions()
        bridge.permissions.add_policy(PermissionPolicy(
            name="ro_agent",
            max_permission_level=PermissionLevel.READ_ONLY
        ))
        r = bridge.execute("read_data", {"id": "abc"}, policy_name="ro_agent")
        assert r["success"] is True

    def test_scoped_policy_whitelist(self):
        bridge = make_bridge_with_actions()
        bridge.permissions.add_policy(PermissionPolicy(
            name="scoped_agent",
            allowed_actions=["read_data"],
            max_permission_level=PermissionLevel.WRITE
        ))
        r1 = bridge.execute("read_data", {"id": "abc"}, policy_name="scoped_agent")
        r2 = bridge.execute("write_data", {"key": "x", "value": "y"}, policy_name="scoped_agent")
        assert r1["success"] is True
        assert r2["success"] is False

    def test_policy_check_result_has_policy_name(self):
        bridge = make_bridge_with_actions()
        bridge.permissions.add_policy(PermissionPolicy(
            name="named_policy",
            max_permission_level=PermissionLevel.READ_ONLY
        ))
        check = bridge.permissions.check("write_data", ["write"], policy_name="named_policy")
        assert check["policy"] == "named_policy"


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])