# AI Risk Gateway

> **A production-grade Python library for runtime policy enforcement in AI agent systems.**

`ai_risk_gateway` is a pure Python library that acts as a **runtime safety layer** between AI agents and the actions they execute. It intercepts agent tool calls, evaluates them against a configurable set of policies, computes a risk score, and returns a structured decision — **ALLOW**, **REVIEW**, or **BLOCK** — before any action is performed.

> No ML. No external services. No database. Fully deterministic and production-ready.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🛡️ **Policy Engine** | Modular, independently pluggable policies for any action type |
| 📊 **Risk Scoring** | Aggregates policy violation weights into a total integer risk score |
| 🚦 **Decision Engine** | Configurable thresholds to ALLOW, REVIEW, or BLOCK actions |
| ⚙️ **Enforcement Modes** | `strict`, `advisory`, and `monitor` modes for flexible deployment |
| 🔒 **Safe Failure** | Fail-closed on policy crash (returns BLOCK with `POLICY_ERROR`) |
| 🧱 **Clean Architecture** | SOLID principles, type hints throughout, no circular imports |
| 🗄️ **State Provider** | Pluggable state backend; ships with an in-memory implementation |
| 🔌 **Extensible** | Write your own policies by subclassing `BasePolicy` in minutes |

---

## 📦 Project Structure

```
ai_risk_gateway/
│
├── __init__.py
├── gateway.py              # RiskGateway orchestrator
│
├── config/
│   └── settings.py         # GatewaySettings (thresholds, mode)
│
├── models/
│   ├── action.py           # Action model (agent request)
│   ├── context.py          # Context model (enriched runtime data)
│   ├── violation.py        # Violation model (policy breach record)
│   └── decision.py         # Decision model (ALLOW / REVIEW / BLOCK)
│
├── engines/
│   ├── policy_engine.py    # Runs all policies against an action
│   ├── risk_scorer.py      # Aggregates violation weights → score
│   └── decision_engine.py  # Maps score to a Decision
│
├── policies/
│   ├── base.py             # BasePolicy abstract class
│   ├── email/
│   │   ├── domain_policy.py      # Restrict emails by domain
│   │   └── frequency_policy.py   # Rate-limit agent actions
│   └── financial/
│       └── refund_limit_policy.py  # Cap refund amounts
│
├── providers/
│   ├── base_state_provider.py    # Abstract state interface
│   └── in_memory_provider.py     # Dictionary-based implementation
│
├── registry.py             # PolicyRegistry for named policy management
├── constants.py            # Default thresholds and policy weights
└── exceptions.py           # Custom exception hierarchy
```

---

## 🚀 Quick Start

### Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/Bharani-a123/ai_risk_gateway.git
cd ai_risk_gateway
pip install -e .
```

### Basic Usage

```python
from ai_risk_gateway import (
    RiskGateway,
    InMemoryStateProvider,
    DomainPolicy,
    FrequencyPolicy,
    RefundLimitPolicy,
)

# 1. Create a gateway with policies
gateway = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[
        DomainPolicy(allowed_domains=["company.com", "partner.org"]),
        FrequencyPolicy(max_actions=5, timeframe_seconds=60),
        RefundLimitPolicy(max_refund_amount=500.0),
    ],
)

# 2. Evaluate an agent action
decision = gateway.evaluate({
    "agent_id": "crm-agent",
    "action_type": "send_email",
    "payload": {"to": "user@company.com", "subject": "Invoice #1042"},
})

# 3. Act on the decision
if decision.is_allowed:
    print("✅ Action approved — proceed")
elif decision.is_review:
    print(f"⚠️  Requires human approval (score: {decision.risk_score})")
else:
    print(f"🚫 Action blocked (score: {decision.risk_score})")
    for v in decision.violations:
        print(f"   - {v}")
```

---

## 🔧 Core Concepts

### Decision Types

| Decision | Risk Score Range | Meaning |
|---|---|---|
| `ALLOW` | 0 – 30 | Action is safe to execute |
| `REVIEW` | 31 – 60 | Action requires human approval |
| `BLOCK` | 61+ | Action is rejected outright |

Thresholds are fully configurable via `GatewaySettings`.

### Decision Model

```python
@dataclass
class Decision:
    decision: DecisionType          # ALLOW | REVIEW | BLOCK
    risk_score: int                 # Aggregated violation weight
    violations: list[Violation]     # All triggered policy violations
    requires_approval: bool         # True when decision is REVIEW
    evaluated_at: datetime          # Timestamp of evaluation

    @property
    def is_allowed(self) -> bool: ...
    @property
    def is_review(self) -> bool: ...
    @property
    def is_blocked(self) -> bool: ...
```

### Enforcement Modes

| Mode | Behaviour |
|---|---|
| `strict` *(default)* | Decisions are applied as-is |
| `advisory` | Violations are logged; all actions ultimately ALLOW |
| `monitor` | Score only — no enforcement whatsoever |

```python
gateway = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[...],
    mode="advisory",   # or "strict" | "monitor"
)

# evaluate() returns the raw decision; enforce() applies the mode
decision = gateway.evaluate(action_dict)
final    = gateway.enforce(decision)   # applies mode override
```

---

## 🧩 Built-in Policies

### `DomainPolicy`
Restricts `send_email` actions to an allowlist of domains.

```python
DomainPolicy(allowed_domains=["company.com", "partner.org"], weight=70)
```

### `FrequencyPolicy`
Rate-limits an agent's actions within a rolling time window.

```python
FrequencyPolicy(max_actions=5, timeframe_seconds=60, weight=35)
```

### `RefundLimitPolicy`
Blocks `refund` actions that exceed a monetary cap.

```python
RefundLimitPolicy(max_refund_amount=500.0, weight=70)
```

---

## 🛠️ Writing a Custom Policy

Extend `BasePolicy` and implement the `evaluate` method:

```python
from ai_risk_gateway import BasePolicy, Action, Context, Violation

class HighValueTransferPolicy(BasePolicy):
    """Block transfers above a configurable limit."""

    name = "high_value_transfer"

    def __init__(self, max_amount: float, weight: int = 80) -> None:
        self.max_amount = max_amount
        self.weight = weight

    def evaluate(self, action: Action, context: Context) -> Violation | None:
        if action.action_type != "transfer":
            return None
        amount = action.payload.get("amount", 0)
        if amount > self.max_amount:
            return Violation(
                policy=self.name,
                message=f"Transfer ${amount} exceeds limit of ${self.max_amount}",
                weight=self.weight,
            )
        return None
```

Then plug it in:

```python
gateway = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[HighValueTransferPolicy(max_amount=10_000)],
)
```

---

## ⚙️ Configuration

### Via `GatewaySettings`

```python
from ai_risk_gateway import GatewaySettings, RiskGateway

settings = GatewaySettings(
    allow_max=25,    # score ≤ 25 → ALLOW
    review_max=55,   # 26–55 → REVIEW, 56+ → BLOCK
)

gateway = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[...],
    config=settings,
)
```

### Via plain dict

```python
gateway = RiskGateway(
    state_provider=InMemoryStateProvider(),
    policies=[...],
    config={"allow_max": 25, "review_max": 55},
)
```

### Default constants (`constants.py`)

| Constant | Value |
|---|---|
| `DEFAULT_ALLOW_MAX` | `30` |
| `DEFAULT_REVIEW_MAX` | `60` |
| `DEFAULT_FREQUENCY_TIMEFRAME_SECONDS` | `3600` |
| `DEFAULT_FREQUENCY_MAX_ACTIONS` | `5` |
| `DEFAULT_DOMAIN_POLICY_WEIGHT` | `40` |
| `DEFAULT_FREQUENCY_POLICY_WEIGHT` | `35` |
| `DEFAULT_REFUND_LIMIT_POLICY_WEIGHT` | `50` |

---

## 🗄️ State Providers

The `BaseStateProvider` interface allows you to plug in any storage backend:

```python
from ai_risk_gateway import BaseStateProvider

class RedisStateProvider(BaseStateProvider):
    def get_action_count(self, agent_id, action_type, timeframe_seconds): ...
    def record_action(self, action): ...
```

The built-in `InMemoryStateProvider` uses an in-process dictionary — ideal for testing, demos, and single-process deployments.

---

## 🎮 Running the Demo

A fully self-contained demo covers all 7 capability areas:

```bash
python demo_standalone.py
```

The demo walks through:

1. **Action schema** — `action_id` (UUID4) and `timestamp` auto-generated
2. **Violation model** — `policy_code`, severity (`LOW/MEDIUM/HIGH`), and weight
3. **Decision model** — `risk_score`, `evaluated_at`, helper properties
4. **Enforcement modes** — strict / advisory / monitor
5. **Demo logging** — structured console output on every `evaluate()`
6. **Safe failure** — policy crash → `POLICY_ERROR` BLOCK (fail-closed)
7. **`enforce()` separation** — evaluate then enforce independently

---

## 🏗️ Architecture

```
Agent Action Dict
       │
       ▼
  ┌─────────────┐
  │ RiskGateway │  gateway.evaluate(action_dict)
  └──────┬──────┘
         │
   ┌─────▼──────┐        ┌──────────────────┐
   │   Action   │◄───────│  Action.from_dict │
   └─────┬──────┘        └──────────────────┘
         │
   ┌─────▼──────┐
   │  Context   │  enriched with state_provider + config
   └─────┬──────┘
         │
   ┌─────▼──────────┐
   │  PolicyEngine  │  runs each BasePolicy → List[Violation]
   └─────┬──────────┘
         │
   ┌─────▼──────┐
   │ RiskScorer │  sum of violation weights → int score
   └─────┬──────┘
         │
   ┌─────▼──────────┐
   │ DecisionEngine │  score → ALLOW / REVIEW / BLOCK
   └─────┬──────────┘
         │
         ▼
      Decision
```

---

## 📋 Exception Hierarchy

```
RiskGatewayError
├── ActionValidationError   # Invalid action payload
└── PolicyEvaluationError   # Policy crash during evaluation
```

---

## 🔒 Design Principles

- **Deterministic** — no randomness, no ML, no external calls
- **Fail-closed** — a crashing policy produces a BLOCK, never a silent pass
- **SOLID** — engines are independent; policies are open for extension
- **Type-safe** — full type hints throughout; dataclasses for all models
- **Zero dependencies** — pure Python standard library only

---

## 📄 License

This project is currently unlicensed. See the repository for details.

---

*Built with ❤️ as a production-grade AI safety primitive.*