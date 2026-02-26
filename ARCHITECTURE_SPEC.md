You are building a production-grade Python library called "ai_risk_gateway".

Goal:
Create a runtime policy enforcement layer for AI agents that evaluates actions before execution and returns structured risk decisions.

This is NOT a web app.
This is NOT a FastAPI project.
This is a pure Python library.

Follow clean architecture principles.

-------------------------------------------------------
PROJECT STRUCTURE
-------------------------------------------------------

ai_risk_gateway/
│
├── __init__.py
├── gateway.py
│
├── models/
│   ├── action.py
│   ├── context.py
│   ├── violation.py
│   └── decision.py
│
├── engines/
│   ├── policy_engine.py
│   ├── risk_scorer.py
│   └── decision_engine.py
│
├── policies/
│   ├── base.py
│   ├── email/
│   │   ├── domain_policy.py
│   │   └── frequency_policy.py
│   └── financial/
│       └── refund_limit_policy.py
│
├── providers/
│   ├── base_state_provider.py
│   └── in_memory_provider.py
│
├── registry.py
├── constants.py
└── exceptions.py

-------------------------------------------------------
CORE REQUIREMENTS
-------------------------------------------------------

1. RiskGateway class (gateway.py)
   - Accepts:
        - state_provider
        - list of policy objects
        - optional config
   - Public method:
        evaluate(action_dict: dict) -> Decision
   - Orchestrates:
        - Action model validation
        - Context building
        - Policy execution
        - Risk scoring
        - Decision evaluation

2. Models:
   - Action: represents agent action request
   - Context: enriched runtime context
   - Violation: policy violation with message + weight
   - Decision:
        - decision (ALLOW | REVIEW | BLOCK)
        - risk_score (int)
        - violations (list)
        - requires_approval (bool)
        - helper properties: is_allowed, is_blocked

3. Policy System:
   - BasePolicy (abstract class)
        method: evaluate(action, context) -> Optional[Violation]
   - Policies must be modular and independently pluggable.
   - Example policies:
        - DomainPolicy (email domain restriction)
        - FrequencyPolicy (action rate limit)
        - RefundLimitPolicy (financial cap)

4. Risk Scoring:
   - Aggregates violation weights.
   - Returns total integer score.

5. Decision Engine:
   - Uses thresholds from constants.py
   - Default:
        - 0–30 ALLOW
        - 31–60 REVIEW
        - 61+ BLOCK

6. State Provider:
   - BaseStateProvider (abstract)
        methods:
            get_action_count(agent_id, action_type, timeframe)
            record_action(action)
   - InMemoryStateProvider:
        simple dictionary-based implementation.

7. Deterministic:
   - No randomness.
   - No ML.
   - No external services.
   - No database dependency.

-------------------------------------------------------
CODING RULES
-------------------------------------------------------

- Use type hints everywhere.
- Use dataclasses where appropriate.
- Follow SOLID principles.
- Keep engines independent.
- Avoid circular imports.
- Do not hardcode business values inside engines.
- Keep policies lightweight and configurable.
- Write docstrings for all public classes and methods.

-------------------------------------------------------
OUTPUT REQUIREMENTS
-------------------------------------------------------

Generate complete implementation for:

- All models
- All engines
- BasePolicy abstraction
- Example policies
- State provider system
- RiskGateway orchestrator
- Constants and exceptions

Ensure:
- The package can be imported.
- A basic usage example works.
- Code is clean and production-ready.

-------------------------------------------------------
END OF SPEC
-------------------------------------------------------