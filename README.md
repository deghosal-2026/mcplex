# MCPlex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](.github/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-2025--06--18-purple)](docs/spec/mcplex.md)

> A stateless HTTP proxy that exposes any REST API as an MCP tool — no SDK, no wrapper library, no per-connector code.

MCPlex sits between AI coding agents (Claude Code, Cursor, Codex) and your
backend REST APIs.  Agents discover tools via the standard MCP `tools/list`
handshake and call them via `tools/call`.  MCPlex translates those calls
into HTTP requests to your backend.

The key idea: **connectors are YAML, not Python.**  Adding a new tool means
adding a few lines of config — method, URL path, parameter mapping.  The
generic HTTP proxy handler does the rest.

## What It's Meant to Do

Engineering teams build internal AI tools — incident responders, CI
diagnosers, policy checkers, DORA metric dashboards.  Each tool ships
with its own UI or CLI.  Adoption is low because engineers won't learn
N different interfaces.

MCPlex changes the distribution model: one MCP server, all tools.
Agents discover everything on startup.  Engineers never leave their
editor.

The repo includes 4 public connectors ([ai-code-guardian](https://github.com/deghosal-2026/ai-code-guardian),
[ci-doctor](https://github.com/deghosal-2026/ci-doctor),
[sprint-intelligence](https://github.com/deghosal-2026/sprint-intelligence),
[ai-incident-commander](https://github.com/deghosal-2026/ai-incident-commander))
as a concrete demonstration — 9 tools across 4 systems, all exposed
through a single `/mcp` endpoint.

## What It Is Not

- **Not an AI framework.**  MCPlex contains zero LLM calls, zero prompts,
  zero model dependencies.  It is a pure HTTP proxy.
- **Not an MCP SDK.**  MCPlex implements the MCP wire protocol directly.
  Backend tools never import an MCP library or add an MCP dependency.
- **Not a replacement for backend APIs.**  MCPlex does not transform data
  or add business logic.  It proxies calls to your existing REST endpoints.

## Architecture

```
                    config.yaml
                         │
              ┌──────────▼──────────┐
              │  Tool Registry      │
              │  name → route       │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  HTTP Proxy Handler │
              │  (generic — reads   │
              │   method, path,     │
              │   param_mapping     │
              │   from config)      │
              └────┬────┬────┬──────┘
                   │    │    │
             ┌─────▼┐ ┌▼───┐┌▼────┐
             │ API A│ │API B││API C│
             └──────┘ └────┘└─────┘
```

1. On startup, MCPlex reads `config.yaml` and builds a tool registry.
2. Each `type: http` connector generates an async proxy handler.
3. An agent connects and calls `tools/list` — MCPlex returns the catalog.
4. The agent calls `tools/call` — MCPlex maps MCP parameters to HTTP
   parameters and makes the request.
5. The backend response is returned as an MCP tool result.

Two transport modes, auto-detected by the `Accept` header:

| Accept header | Response format |
|---------------|-----------------|
| `application/json` | JSON-RPC over HTTP POST |
| `text/event-stream` | Server-Sent Events (Streamable HTTP) |

## Quick Start

```bash
pip install mcplex-backplane

# Copy and edit environment (for docker-compose)
cp .env.example .env

# Start with default config
mcplex serve --config config.yaml
```

Connect Claude Code: `claude --mcp http://localhost:8000/mcp`

## Included Connectors

4 MIT-licensed public repos, wired as MCP tools via thin API adapters
(see [Integration Guide](docs/integration/README.md) for the pattern):

| Connector | Repo | Tools |
|-----------|------|-------|
| guardian | [ai-code-guardian](https://github.com/deghosal-2026/ai-code-guardian) | `guardian_check_policy`, `guardian_get_coverage` |
| ci-agent | [ci-doctor](https://github.com/deghosal-2026/ci-doctor) | `ci_diagnose_failure`, `ci_get_pipeline_history` |
| sprintsense | [sprint-intelligence](https://github.com/deghosal-2026/sprint-intelligence) | `dora_get_metrics`, `dora_get_trend` |
| incident-cmdr | [ai-incident-commander](https://github.com/deghosal-2026/ai-incident-commander) | `incident_query_active`, `incident_query_history`, `incident_get_timeline` |

**Total: 9 MCP tools** across 4 AI systems (3 real repos + 1 test-bench mock).

## Docs

| Doc | Description |
|-----|-------------|
| [Integration Guide](docs/integration/README.md) | How to connect repos via MCP API adapters |
| [Specification](docs/spec/mcplex.md) | Architecture, transport, connector design |
| [PRD](docs/prd/mcplex.md) | Product requirements and user stories |
| [Sprint Plan (WBS)](docs/wbs/mcplex.md) | Work breakdown and epics |
| [Config Reference](docs/config-reference.md) | YAML schema for connectors |
| [E2E Test Plan & Results](tests/e2e/README.md) | Test plan, 9/9 results, 15 screenshots |
| [Code Review](docs/review.md) | Internal code review |

## Roadmap

**Shipped (v0.3.0)**
- Generic HTTP proxy connector (YAML-driven)
- Streamable HTTP + SSE auto-detect
- 4 public repo integrations
- Docker compose deployment
- 41 unit tests, 9 E2E tests passing

**Next**
- OSS readiness: issue templates, CODE_OF_CONDUCT, SECURITY.md
- GitHub Actions CI
- Contributing guide
- Claude Code demo recording

**Future (v1.0.0)**
- OAuth 2.0 / OIDC authorization
- Write tool approval flow
- Unified audit logging
- PyPI publish
- Rate limiting and config hot-reload

## License

MIT
