# Contributing to MCPlex

Thank you for considering contributing. MCPlex is a small project and
every contribution helps.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/deghosal-2026/mcplex
cd mcplex

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run linter
ruff check mcplex/ tests/
```

## Project Structure

```
mcplex/
  config.py          Pydantic models for YAML config
  registry.py        Tool name → handler mapping
  server.py          Starlette app factory
  transport.py       MCP JSON-RPC + SSE handlers
  connectors/
    __init__.py      Registration of all connector types
    http_proxy.py    Generic HTTP proxy handler
    incidentgpt.py   Native incident-commander mock
tests/
  test_config.py
  test_registry.py
  test_transport.py
  test_incidentgpt.py
  test_bench.py      Mock backend server (4 APIs)
  e2e/               E2E tests with MCP Inspector
```

## Making Changes

1. Create a branch: `git checkout -b my-feature`
2. Make your changes
3. Add or update tests
4. Run `ruff check mcplex/ tests/` — no new warnings
5. Run `python -m pytest tests/ -v` — all tests pass
6. Update documentation if needed
7. Open a pull request

## Code Style

All contributions must follow these coding standards:

- **Python:** [PEP 8](https://peps.python.org/pep-0008/) via Ruff with the ruleset in [`pyproject.toml`](pyproject.toml).
- **JSON:** Use `json.dumps()` for constructing JSON strings, never f-string JSON.
- **Documentation:** Add module-level docstrings to new files. Every function should have a docstring explaining what it does.
- **Async:** Follow existing async/await patterns.
- **Type safety:** Type hints required on all public functions.
- **Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`).
- Tests use pytest with `@pytest.mark.asyncio` for async tests

## Testing Policy

- **Every new feature must include tests.** Major functionality added to the codebase must be accompanied by automated tests in the test suite.
- **Coverage targets:** Aim for ≥80% line coverage on new code. Pull requests that reduce overall coverage below the fail_under threshold will be flagged.
- **Test types:** Prefer unit tests for business logic, integration tests for API routes.
- **Running tests:** `pytest` — ensure all tests pass before opening a PR.
- **Test data:** Use fixtures and factories rather than production data. Never commit real credentials or tokens.

## Questions?

Open a GitHub Discussion or issue. We're happy to help.
