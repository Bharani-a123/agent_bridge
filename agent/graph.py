"""LangGraph graph wiring the LLM agent with the ai_risk_gateway.

Graph topology
--------------
                    ┌──────────┐
              ┌────▶│  agent   │────▶ END  (no tool calls)
              │     └────┬─────┘
              │          │ (tool calls detected by tools_condition)
              │          ▼
              │     ┌────────────┐
              │     │ risk_check │  ←─ evaluates every tool call
              │     └────┬───────┘
              │          │
              │    ┌─────┴──────┐
        BLOCK │    │            │ ALLOW / REVIEW
              │    ▼            ▼
              └──agent      ┌──────┐
               (block msg)  │tools │──┐
                            └──────┘  │ (execute approved tools)
                                      │
                                      └──▶ agent (loop)
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from ai_risk_gateway import (
    DomainPolicy,
    FrequencyPolicy,
    InMemoryStateProvider,
    RefundLimitPolicy,
    RiskGateway,
)

from .state import AgentState
from .tools import issue_refund, lookup_account, send_email

# ---------------------------------------------------------------------------
# Tools registry
# ---------------------------------------------------------------------------
TOOLS = [send_email, issue_refund, lookup_account]

# Maps LangChain tool name → gateway action_type
TOOL_TO_ACTION: dict[str, str] = {
    "send_email": "send_email",
    "issue_refund": "refund",
    "lookup_account": "lookup_account",
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are a helpful customer-support AI assistant. "
        "You have access to tools for sending emails, issuing refunds, "
        "and looking up account details. "
        "Always use the most appropriate tool when the user requests an action. "
        "If a tool is blocked by the security gateway, acknowledge it "
        "and clearly explain to the user why the action was denied."
    )
)


# ---------------------------------------------------------------------------
# Factory: build a compiled graph with its own isolated gateway instance
# ---------------------------------------------------------------------------
def build_graph(model: str = "llama3.1:8b"):
    """Build and return a compiled LangGraph agent with risk gateway.

    A fresh InMemoryStateProvider is created so each compiled graph
    starts with no prior action history.

    Args:
        model: Ollama model name to use for the LLM node.

    Returns:
        Compiled LangGraph StateGraph.
    """
    llm = ChatOllama(model=model).bind_tools(TOOLS)

    state_provider = InMemoryStateProvider()
    gateway = RiskGateway(
        state_provider=state_provider,
        policies=[
            # weight=70 → any violation produces BLOCK (score 70 ≥ 61)
            DomainPolicy(
                allowed_domains=["company.com", "partner.org"],
                weight=70,
            ),
            # weight=35 → violation produces REVIEW (31–60)
            FrequencyPolicy(max_actions=3, timeframe_seconds=60, weight=35),
            # weight=70 → over-limit refund produces BLOCK
            RefundLimitPolicy(max_refund_amount=500.0, weight=70),
        ],
    )

    # -----------------------------------------------------------------------
    # Node: agent
    # -----------------------------------------------------------------------
    def agent_node(state: AgentState) -> dict[str, Any]:
        """Invoke the LLM with the current conversation history."""
        messages = [SYSTEM_PROMPT] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # -----------------------------------------------------------------------
    # Node: risk_check
    # -----------------------------------------------------------------------
    def risk_check_node(state: AgentState) -> dict[str, Any]:
        """Evaluate every pending tool call through the risk gateway.

        - ALLOW  → logged, tool call passes through to ToolNode.
        - REVIEW → logged with warning, tool call still executes.
        - BLOCK  → ToolMessage injected explaining the denial;
                   all other tool calls in the same batch are suspended
                   so the LLM can reconsider without partial execution.
        """
        last_msg = state["messages"][-1]
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {}

        block_messages: list[ToolMessage] = []
        risk_entries: list[dict[str, Any]] = []
        blocked_ids: set[str] = set()

        for call in last_msg.tool_calls:
            tool_name: str = call["name"]
            tool_args: dict = call["args"]
            call_id: str = call["id"]

            action_type = TOOL_TO_ACTION.get(tool_name, tool_name)
            decision = gateway.evaluate(
                {
                    "agent_id": "langgraph-agent",
                    "source": "langgraph",
                    "action_type": action_type,
                    "payload": tool_args,
                }
            )

            risk_entries.append(
                {
                    "tool": tool_name,
                    "args": tool_args,
                    "action_type": action_type,
                    "decision": decision.decision.value,
                    "risk_score": decision.risk_score,
                    "violations": [
                        {
                            "policy": v.policy_code,
                            "severity": v.severity,
                            "message": v.message,
                            "weight": v.weight,
                        }
                        for v in decision.violations
                    ],
                }
            )

            if decision.is_blocked:
                blocked_ids.add(call_id)
                reasons = "; ".join(v.message for v in decision.violations)
                block_messages.append(
                    ToolMessage(
                        content=(
                            f"[BLOCKED by Risk Gateway | score={decision.risk_score}] "
                            f"{reasons}"
                        ),
                        tool_call_id=call_id,
                    )
                )

        result: dict[str, Any] = {"risk_log": risk_entries}

        if blocked_ids:
            # Suspend all non-blocked calls in the same batch so the LLM
            # receives a complete set of ToolMessages and can respond.
            for call in last_msg.tool_calls:
                if call["id"] not in blocked_ids:
                    block_messages.append(
                        ToolMessage(
                            content=(
                                "[SUSPENDED] Execution halted: another tool in "
                                "this batch was blocked by the risk gateway."
                            ),
                            tool_call_id=call["id"],
                        )
                    )
            result["messages"] = block_messages

        return result

    # -----------------------------------------------------------------------
    # Routing after risk_check
    # -----------------------------------------------------------------------
    def after_risk_check(state: AgentState) -> Literal["tools", "agent"]:
        """If risk_check injected block/suspend messages go back to agent,
        otherwise forward to ToolNode for actual execution."""
        if isinstance(state["messages"][-1], ToolMessage):
            return "agent"
        return "tools"

    # -----------------------------------------------------------------------
    # Assemble graph
    # -----------------------------------------------------------------------
    g = StateGraph(AgentState)

    g.add_node("agent", agent_node)
    g.add_node("risk_check", risk_check_node)
    g.add_node("tools", ToolNode(TOOLS))

    g.add_edge(START, "agent")

    # agent → risk_check  (if tool calls present)  |  agent → END
    g.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "risk_check", END: END},
    )

    # risk_check → agent  (if blocked)  |  risk_check → tools  (if approved)
    g.add_conditional_edges(
        "risk_check",
        after_risk_check,
        {"agent": "agent", "tools": "tools"},
    )

    # tools → agent  (always loop back for follow-up response)
    g.add_edge("tools", "agent")

    return g.compile()
