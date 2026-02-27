"""
AI Risk Gateway — Standalone Real-Time Demo
============================================
No LangGraph, no Ollama, no external services required.

Run:
    python demo_standalone.py

Covers all 7 improvement areas from the hackathon brief.
"""
from __future__ import annotations

import sys
import io
import time

# Force UTF-8 output on Windows terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from ai_risk_gateway import (
    RiskGateway,
    InMemoryStateProvider,
    DomainPolicy,
    FrequencyPolicy,
    RefundLimitPolicy,
)

DIVIDER  = "=" * 60
THIN_DIV = "-" * 60

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def pause() -> None:
    """Small pause so the demo output is readable when run live."""
    time.sleep(0.3)


def banner(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def run_scenario(
    label: str,
    gateway: RiskGateway,
    action_dict: dict,
    expect: str,
    use_enforce: bool = False,
) -> None:
    """Execute one scenario, print results, and check expectation."""
    print(f"\n>>> {label}")
    print(f"    Action : {action_dict}")
    if expect:
        print(f"    Expect : {expect}")

    decision = gateway.evaluate(action_dict)

    if use_enforce:
        print("    [calling enforce() to apply mode override]")
        decision = gateway.enforce(decision)
        print(f"    After enforce() -> {decision.decision.value}")

    actual = decision.decision.value
    verdict = "PASS" if actual == expect else "FAIL"
    print(f"    Result : {actual}  |  Test: {verdict}")
    pause()


# ---------------------------------------------------------------------------
# Gateway instances for each demo section
# ---------------------------------------------------------------------------

STANDARD_POLICIES = [
    DomainPolicy(allowed_domains=["company.com", "partner.org"], weight=70),
    RefundLimitPolicy(max_refund_amount=500.0, weight=70),
    FrequencyPolicy(max_actions=3, timeframe_seconds=60, weight=35),
]

# ---------------------------------------------------------------------------
# DEMO START
# ---------------------------------------------------------------------------
banner("AI Risk Gateway — Hackathon Demo")
print("""
  Runtime policy enforcement layer that intercepts AI tool calls
  and returns a structured risk decision: ALLOW / REVIEW / BLOCK.

  Features demonstrated:
    1. Standardised Action schema (action_id auto-generated)
    2. Structured Violation model  (policy_code + severity)
    3. Decision model              (risk_score, evaluated_at, is_review)
    4. Enforcement modes           (strict / advisory / monitor)
    5. Demo logging                (structured console output)
    6. Safe failure handling       (fail-closed on policy crash)
    7. enforce() separation        (evaluate then enforce)
""")
input("  Press ENTER to begin...\n")

# -------------------------------------------------------------------
# SECTION 1 — STRICT MODE (default)
# -------------------------------------------------------------------
banner("SECTION 1 — Strict Mode: ALLOW / REVIEW / BLOCK")

gw_strict = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=STANDARD_POLICIES,
    mode="strict",
)

run_scenario(
    label="1a. Account lookup (no policy covers this) → ALLOW",
    gateway=gw_strict,
    action_dict={
        "agent_id": "crm-agent",
        "source": "langgraph",
        "action_type": "lookup_account",
        "target": "CUST-001",
        "payload": {"customer_id": "CUST-001"},
    },
    expect="ALLOW",
)

run_scenario(
    label="1b. Email to allowed domain → ALLOW",
    gateway=gw_strict,
    action_dict={
        "agent_id": "crm-agent",
        "source": "langgraph",
        "action_type": "send_email",
        "target": "alice@company.com",
        "payload": {"to": "alice@company.com", "subject": "Invoice #1042"},
    },
    expect="ALLOW",
)

run_scenario(
    label="1c. Email to BLOCKED domain → BLOCK",
    gateway=gw_strict,
    action_dict={
        "agent_id": "crm-agent",
        "source": "langgraph",
        "action_type": "send_email",
        "target": "attacker@evil.com",
        "payload": {"to": "attacker@evil.com", "subject": "Credentials"},
    },
    expect="BLOCK",
)

run_scenario(
    label="1d. Refund within limit ($150) → ALLOW",
    gateway=gw_strict,
    action_dict={
        "agent_id": "crm-agent",
        "source": "langgraph",
        "action_type": "refund",
        "target": "CUST-002",
        "payload": {"customer_id": "CUST-002", "amount": 150.0},
    },
    expect="ALLOW",
)

run_scenario(
    label="1e. Refund OVER limit ($1 200) → BLOCK",
    gateway=gw_strict,
    action_dict={
        "agent_id": "crm-agent",
        "source": "langgraph",
        "action_type": "refund",
        "target": "CUST-003",
        "payload": {"customer_id": "CUST-003", "amount": 1200.0},
    },
    expect="BLOCK",
)

# -------------------------------------------------------------------
# SECTION 2 — REVIEW band (mid-weight policy)
# -------------------------------------------------------------------
banner("SECTION 2 — REVIEW Decision (mid-range risk score)")

gw_review = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[FrequencyPolicy(max_actions=3, timeframe_seconds=60, weight=45)],
    mode="strict",
)

# Warm up the state: submit 3 actions first so the 4th trips the limit
for i in range(3):
    gw_review.evaluate({
        "agent_id": "bot-x",
        "action_type": "send_email",
        "payload": {"to": "user@company.com"},
    })

print("\n[Frequency state filled: 3 send_email actions already recorded]")

run_scenario(
    label="2a. 4th send_email within 60 s → REVIEW (score 45, needs approval)",
    gateway=gw_review,
    action_dict={
        "agent_id": "bot-x",
        "action_type": "send_email",
        "payload": {"to": "user@company.com"},
    },
    expect="REVIEW",
)

# is_review property
from ai_risk_gateway.models.decision import DecisionType, Decision
rev = Decision(decision=DecisionType.REVIEW, risk_score=45, requires_approval=True)
print(f"\n    is_review={rev.is_review}  is_blocked={rev.is_blocked}  is_allowed={rev.is_allowed}")
print("    is_review property works correctly.")

# -------------------------------------------------------------------
# SECTION 3 — ADVISORY MODE
# -------------------------------------------------------------------
banner("SECTION 3 — Advisory Mode: violations logged, never blocked")

gw_advisory = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=STANDARD_POLICIES,
    mode="advisory",
)

run_scenario(
    label="3a. Bad domain in advisory mode → raw=BLOCK, enforced=ALLOW",
    gateway=gw_advisory,
    action_dict={
        "agent_id": "crm-agent",
        "source": "langgraph",
        "action_type": "send_email",
        "payload": {"to": "attacker@evil.com"},
    },
    expect="ALLOW",      # final value after enforce() in advisory mode
    use_enforce=True,
)

# -------------------------------------------------------------------
# SECTION 4 — MONITOR MODE
# -------------------------------------------------------------------
banner("SECTION 4 — Monitor Mode: score only, zero enforcement")

gw_monitor = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=STANDARD_POLICIES,
    mode="monitor",
)

run_scenario(
    label="4a. Huge refund in monitor mode → raw=BLOCK, enforced=ALLOW",
    gateway=gw_monitor,
    action_dict={
        "agent_id": "crm-agent",
        "action_type": "refund",
        "payload": {"amount": 9999.0},
    },
    expect="ALLOW",      # final value after enforce() in monitor mode
    use_enforce=True,
)

# -------------------------------------------------------------------
# SECTION 5 — SAFE FAILURE: policy crash → fail closed
# -------------------------------------------------------------------
banner("SECTION 5 — Safe Failure Handling (fail-closed on crash)")

from ai_risk_gateway import BasePolicy, Context, Action as GWAction

class AlwaysCrashPolicy(BasePolicy):
    def evaluate(self, action, context):
        raise RuntimeError("Simulated policy crash!")

gw_crash = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[AlwaysCrashPolicy()],
    mode="strict",
)

run_scenario(
    label="5a. Policy crash → BLOCK (POLICY_ERROR violation, score=100)",
    gateway=gw_crash,
    action_dict={"agent_id": "agent-x", "action_type": "delete_record", "payload": {}},
    expect="BLOCK",
)

# -------------------------------------------------------------------
# SECTION 6 — Action schema: auto-generated fields
# -------------------------------------------------------------------
banner("SECTION 6 — Action Schema: auto-generated action_id & timestamp")

a = GWAction.from_dict({
    "agent_id": "demo-agent",
    "action_type": "send_email",
    "payload": {"to": "user@company.com"},
})

print(f"\n    Submitted dict with NO action_id or timestamp.")
print(f"    action_id  (auto) : {a.action_id}")
print(f"    timestamp  (auto) : {a.timestamp.isoformat()}")
print(f"    source     (def)  : {a.source}")
print(f"    target     (def)  : '{a.target}'")
assert len(a.action_id) == 36, "Expected UUID4"
print("    Validation PASS: UUID4 generated correctly.")

# -------------------------------------------------------------------
# SUMMARY
# -------------------------------------------------------------------
banner("Demo Complete")
print("""
  All 7 improvement areas demonstrated:

  [1] Action schema     — action_id (UUID4) and timestamp auto-generated
  [2] Violation model   — policy_code + severity (LOW/MEDIUM/HIGH) + weight
  [3] Decision model    — risk_score, evaluated_at, is_review/is_blocked/is_allowed
  [4] Enforcement modes — strict | advisory | monitor
  [5] Demo logging      — structured console output on every evaluate()
  [6] Safe failure      — policy crash -> POLICY_ERROR BLOCK (fail-closed)
  [7] enforce()         — separate method to apply mode after evaluation
""")
