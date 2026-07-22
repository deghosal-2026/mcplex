# MCPlex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.4.0-blue)](https://github.com/deghosal-2026/mcplex/releases)
[![CI](https://github.com/deghosal-2026/mcplex/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-2025--06--18-purple)](docs/spec/mcplex.md)

> Early proof-of-concept: a YAML-configured MCP proxy that maps simple JSON REST endpoints (GET + query params, POST + JSON body) into MCP tools. Not production-hardened — see [Roadmap](#roadmap).

MCPlex sits between AI coding agents (Claude Code, Cursor, Codex) and your
backend REST APIs.  Agents discover tools via the standard MCP `tools/list`
handshake and call them via `tools/call`.  MCPlex translates those calls
into HTTP requests to your backend.  Zero LLM logic, zero model dependencies,
~400 lines of Python.

## What It's Meant to Do

Most engineering teams have a graveyard of internal tools built before AI
coding agents existed — CLIs, dashboards, webhook receivers, internal REST APIs.
These tools work.  They have users, auth, governance, and business logic baked in.
What they don't have is an interface that AI agents can call.

MCPlex gives those tools a 2nd life.  You don't rewrite them.  You add a thin
REST adapter if they don't already expose JSON (about 40 lines), point MCPlex at
it with a YAML connector, and now any MCP-compatible agent can call them.
The tool keeps its auth, its logic, its governance.  MCPlex is just the new
front door.

The key idea: **connectors are YAML, not Python** (for the 80% case where the
backend already speaks JSON REST).  Adding a new HTTP tool means adding a few
lines of config — method, URL path, parameter mapping.  The generic HTTP proxy
handler does the rest.

The repo includes a 4-connector demo config as an illustration of the pattern —
3 connectors proxy to real sibling repos; the 4th runs on mock data via a
native Python connector for backends without an HTTP server.

## Current Limitations (v0.4.0)

| What works | What's planned |
|---|---|
| `GET` with query params + `POST` with JSON body | `PUT` / `DELETE` support |
| Flat `param_mapping` (MCP arg → HTTP param) | Path-param templating (`/api/{id}`) |
| JSON + non-JSON response handling (HTML/text wrapped) | |
| Static header injection with `${ENV_VAR}` interpolation | OAuth 2.0 / OIDC |
| SSE heartbeat keepalive | Progress streaming, session continuity |
| Identity propagation (X-MCP-Client-Name / Version headers) | |
| Schema/argument validation (type, required, enum, min/max) | |
| Rate limiting per-tool/per-agent | |
| Structured audit logging (session_id, user_id, backend_url, etc.) | |
| Connection pooling (shared httpx.AsyncClient) | |
| 75 unit + integration tests | Write-tool approval flow |
| | Config hot-reload |

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

1. On startup, MCPlex reads `config.yaml`, interpolates `${ENV_VAR}` patterns,
   and builds a tool registry.
2. Each `type: http` connector generates an async proxy handler.
3. An agent connects and calls `tools/list` — MCPlex returns the catalog.
4. The agent calls `tools/call` — MCPlex validates arguments against the
   declared JSON Schema, maps MCP parameters to HTTP parameters, and makes
   the request.
5. The backend response is returned as an MCP tool result, with `isError`
   set when the tool fails.

Two transport modes, auto-detected by the `Accept` header:

| Accept header | Response format |
|---------------|-----------------|
| `application/json` | JSON-RPC over HTTP POST |
| `text/event-stream` | Server-Sent Events (one-shot framing) |

## What Is In This Repo

- MCPlex proxy server (Starlette, JSON-RPC, SSE transport)
- YAML config system (Pydantic models, env-var interpolation, config validation)
- Generic HTTP proxy handler (GET/POST with param mapping)
- Native Python connector fallback (`incidentgpt.py`) for backends without an HTTP server
- Test bench (mock server simulating all 4 backends)
- 50 unit tests, CI (lint, typecheck, test)

## What Is NOT In This Repo (Sibling Repos)

The 4 demo connectors proxy to sibling repos.  These must be cloned alongside
mcplex for the full Docker Compose stack (see `docker-compose.yml`):

| Connector | Sibling Repo | Status |
|-----------|-------------|--------|
| guardian | [ai-code-guardian](https://github.com/deghosal-2026/ai-code-guardian) | Real backend with MCP API adapter |
| ci-agent | [ci-doctor](https://github.com/deghosal-2026/ci-doctor) | Real backend with MCP API adapter |
| sprintsense | [sprint-intelligence](https://github.com/deghosal-2026/sprint-intelligence) | Real backend with MCP API adapter |
| incident-commander | [ai-incident-commander](https://github.com/deghosal-2026/ai-incident-commander) | CLI-only; uses test-bench mock via `incidentgpt.py` native connector |

**Total: 9 MCP tools** across 4 demo connectors (3 real repos + 1 test-bench mock).

To try it without cloning sibling repos, run the test bench: `python tests/test_bench.py`.

## Quick Start

```bash
pip install mcplex-backplane

# Try with the test-bench mock (no sibling repos needed)
python tests/test_bench.py &
mcplex serve --config config.yaml

# Or use docker-compose for the full stack
cp .env.example .env
docker compose up
```

Connect Claude Code: `claude --mcp http://localhost:8000/mcp`

## Included Connectors

The demo `config.yaml` includes 4 connectors — 3 proxy to real sibling repos,
1 runs on the test-bench mock:

| Connector | Repo | Tools |
|-----------|------|-------|
| guardian | [ai-code-guardian](https://github.com/deghosal-2026/ai-code-guardian) | `guardian_check_policy`, `guardian_get_coverage` |
| ci-agent | [ci-doctor](https://github.com/deghosal-2026/ci-doctor) | `ci_diagnose_failure`, `ci_get_pipeline_history` |
| sprintsense | [sprint-intelligence](https://github.com/deghosal-2026/sprint-intelligence) | `dora_get_metrics`, `dora_get_trend` |
| incident-commander | [ai-incident-commander](https://github.com/deghosal-2026/ai-incident-commander) | `incident_query_active`, `incident_query_history`, `incident_get_timeline` |

## Docs

| Doc | Description |
|-----|-------------|
| [Architecture](docs/architecture.md) | System design, data flow, design decisions |
| [Deployment Guide](docs/deployment.md) | Production deployment, nginx config, security |
| [Troubleshooting](docs/troubleshooting.md) | Common errors and resolution steps |
| [Integration Guide](docs/integration/README.md) | How to connect repos via MCP API adapters |
| [Specification](docs/spec/mcplex.md) | Architecture, transport, connector design |
| [PRD](docs/prd/mcplex.md) | Product requirements and user stories |
| [Sprint Plan (WBS)](docs/wbs/mcplex.md) | Work breakdown and epics |
| [Config Reference](docs/config-reference.md) | YAML schema for connectors |
| [E2E Test Plan & Results](tests/e2e/README.md) | Test plan, 9/9 results, 15 screenshots |
| [Code Review](docs/review.md) | Internal code review |

## Roadmap

**Shipped (v0.3.0)**
- Generic HTTP proxy connector (YAML-driven, GET/POST)
- JSON-RPC + one-shot SSE framing (auto-detect by Accept header)
- Config validation (required `base_url`, env-var interpolation)
- `isError` flag on failed tool calls (MCP spec compliance)
- JSON-RPC batch request handling
- 4-connector demo config
- OSS readiness: CI, issue templates, CODE_OF_CONDUCT, SECURITY.md, CONTRIBUTING.md
- 50 unit tests, Docker Compose deployment

**Shipped (v0.4.0)**
- Identity propagation (X-MCP-Client-Name / Version headers)
- Structured audit logging (session_id, user_id, backend_url, http_status)
- Per-tool / per-agent rate limiting
- Schema/argument validation (type, required, enum, min/max)
- Non-JSON response handling (HTML/text wrapped)
- SSE heartbeat keepalive
- Connection pooling (shared httpx.AsyncClient)
- 75 tests (unit + integration), self-contained mock-based integration tests
- PyPI publish as `mcplex-backplane`
- See [CHANGELOG.md](CHANGELOG.md) for full details

**Future (v1.0.0)**
- Write‑tool approval flow
- Config hot‑reload
- Path‑param templating (`/api/{id}`)
- PUT/DELETE support
- SSE progress streaming and session continuity
- OAuth 2.0 / OIDC

## License

MIT
