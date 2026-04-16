"""
Tests for AgentBridge Registry functionality.
"""
import sys
sys.path.insert(0, '..')

import pytest
from agentbridge.registry import Registry
from agentbridge.action import ActionDefinition


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_action(name="test_action", description="A test action", permissions=None):
    def dummy_func(param: str):
        return {}
    return ActionDefinition(
        name=name,
        description=description,
        permissions=permissions or ["read_only"],
        func=dummy_func,
        inputs={"param": {"type": "str", "required": True}},
        outputs={},
        examples=[],
        tags=["test"]
    )


# ── Registry Tests ────────────────────────────────────────────────────────────

class TestRegistry:

    def test_empty_registry(self):
        reg = Registry()
        assert reg.all_actions() == []

    def test_register_action(self):
        reg = Registry()
        action = make_action()
        reg.register(action)
        assert len(reg.all_actions()) == 1

    def test_register_multiple_actions(self):
        reg = Registry()
        reg.register(make_action("action_1"))
        reg.register(make_action("action_2"))
        reg.register(make_action("action_3"))
        assert len(reg.all_actions()) == 3

    def test_duplicate_action_raises(self):
        reg = Registry()
        reg.register(make_action("same_name"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(make_action("same_name"))

    def test_get_existing_action(self):
        reg = Registry()
        reg.register(make_action("find_me"))
        found = reg.get_action("find_me")
        assert found is not None
        assert found.name == "find_me"

    def test_get_nonexistent_action_returns_none(self):
        reg = Registry()
        assert reg.get_action("ghost") is None


# ── Registry Output Tests ─────────────────────────────────────────────────────

class TestRegistryOutput:

    def test_to_dict_structure(self):
        reg = Registry(system_name="Test", system_description="Testing")
        reg.register(make_action())
        d = reg.to_dict()

        assert "agentbridge_version" in d
        assert "web_mcp_compatible" in d
        assert "system" in d
        assert "actions" in d
        assert "meta" in d

    def test_to_dict_system_info(self):
        reg = Registry(system_name="My System", system_description="My Desc", version="3.0.0")
        d = reg.to_dict()
        assert d["system"]["name"] == "My System"
        assert d["system"]["description"] == "My Desc"
        assert d["system"]["version"] == "3.0.0"

    def test_to_dict_action_count(self):
        reg = Registry()
        reg.register(make_action("a1"))
        reg.register(make_action("a2"))
        d = reg.to_dict()
        assert d["meta"]["total_actions"] == 2
        assert len(d["actions"]) == 2

    def test_to_dict_action_structure(self):
        reg = Registry()
        reg.register(make_action("check_this", "Check this action", ["read_only"]))
        d = reg.to_dict()
        action = d["actions"][0]
        assert action["name"] == "check_this"
        assert action["description"] == "Check this action"
        assert "read_only" in action["permissions"]
        assert "inputs" in action
        assert "outputs" in action
        assert "tags" in action
        assert "examples" in action

    def test_web_mcp_compatible_is_true(self):
        reg = Registry()
        assert reg.to_dict()["web_mcp_compatible"] is True

    def test_generated_at_present(self):
        reg = Registry()
        assert "generated_at" in reg.to_dict()

    def test_permission_levels_in_meta(self):
        reg = Registry()
        d = reg.to_dict()
        perms = d["meta"]["permission_levels"]
        assert "read_only" in perms
        assert "write" in perms
        assert "requires_approval" in perms
        assert "restricted" in perms

    def test_output_is_json_serializable(self):
        import json
        reg = Registry(system_name="Test")
        reg.register(make_action())
        # Should not raise
        json.dumps(reg.to_dict())

    def test_summary_contains_action_names(self):
        reg = Registry(system_name="Summary Test")
        reg.register(make_action("visible_action"))
        summary = reg.summary()
        assert "visible_action" in summary
        assert "Summary Test" in summary


# ── Action Definition Tests ───────────────────────────────────────────────────

class TestActionDefinition:

    def test_action_to_dict(self):
        action = make_action("my_action", "Does something", ["read_only"])
        d = action.to_dict()
        assert d["name"] == "my_action"
        assert d["description"] == "Does something"
        assert "read_only" in d["permissions"]

    def test_action_has_inputs(self):
        action = make_action()
        d = action.to_dict()
        assert "inputs" in d
        assert "param" in d["inputs"]

    def test_action_has_tags(self):
        def dummy(x: str): return {}
        action = ActionDefinition(
            name="tagged",
            description="Has tags",
            permissions=["read_only"],
            func=dummy,
            inputs={},
            outputs={},
            examples=[],
            tags=["crm", "contacts"]
        )
        d = action.to_dict()
        assert "crm" in d["tags"]
        assert "contacts" in d["tags"]

    def test_action_has_examples(self):
        def dummy(x: str): return {}
        action = ActionDefinition(
            name="with_examples",
            description="Has examples",
            permissions=["read_only"],
            func=dummy,
            inputs={},
            outputs={},
            examples=[{"description": "Example 1", "inputs": {"x": "test"}}],
            tags=[]
        )
        d = action.to_dict()
        assert len(d["examples"]) == 1
        assert d["examples"][0]["description"] == "Example 1"


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])