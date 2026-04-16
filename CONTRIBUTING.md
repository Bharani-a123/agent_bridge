# Contributing to AgentBridge

AgentBridge is built by developers who felt this pain firsthand.
Every contribution matters — whether it's fixing a bug, adding a connector,
improving docs, or proposing a spec change.

---

## Getting Started

```bash
# Clone the repo
git clone https://github.com/agentbridge/agentbridge.git
cd agentbridge

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

---

## What to Work On

Check the GitHub Issues for open tasks. Good first issues are labeled `good-first-issue`.

High priority areas:
- New framework adapters (FastAPI, Flask, Django already exist — what's next?)
- Connector library for popular enterprise systems (Salesforce, SAP, HubSpot)
- Improved Web MCP compatibility
- Performance improvements for large registries
- Documentation improvements

---

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Write tests for your changes
4. Make sure all tests pass: `pytest tests/ -v`
5. Submit a pull request with a clear description

---

## Code Style

We use `black` for formatting and `ruff` for linting:

```bash
black agentbridge/
ruff check agentbridge/
```

---

## Spec Changes

Changes to the AgentBridge spec (docs/spec.md) require a GitHub issue first
for community discussion before implementation.

---

## License

By contributing, you agree your contributions will be licensed under the MIT License.