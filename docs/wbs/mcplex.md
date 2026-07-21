# MCPlex — Work Breakdown Structure

## Milestones

| MS | Version | Definition | Target |
|----|---------|------------|--------|
| M0 | v0.0.1 | Project scaffold: pyproject.toml, README, MIT, .gitignore | Week 3 (Jul 20) |
| M1 | v0.1.0 | PoC: HTTP server + IncidentGPT connector (3 tools) + demo with Claude Code | Week 3 (Jul 26) |
| M2 | v0.2.0 | **HTTP Proxy connector** + 2 public repo integrations (ai-code-guardian, ci-doctor) | Week 4 (Aug 2) |
| M3 | v0.3.0 | All 4 public repo integrations + docker-compose + demo | Week 5 (Aug 9) |
| M4 | v1.0.0 | Production: Streamable HTTP, OAuth, audit logging, PyPI | Week 6+ |

---

## Sprint 1 — PoC (Week 3, Jul 20-26)

> **Milestone M1:** HTTP server + 1 connector (IncidentGPT, 3 tools). Demo with Claude Code.

### Epic 1: Project Foundation [M0]

| WBS | Issue | Title | Status |
|-----|-------|-------|--------|
| 1.1 | #1 | pyproject.toml, package structure, CLI entry point | [x] |
| 1.2 | #2 | YAML config loader with Pydantic validation | [x] |
| 1.3 | #3 | Tool registry: name → handler mapping, tools/list, tools/call | [x] |
| 1.4 | #4 | HTTP transport: Starlette server, /mcp endpoint, JSON-RPC | [x] |

### Epic 2: IncidentGPT Connector (Mock)

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 2.1 | #5 | Mock data — active incidents (2-3 across 3 services, realistic fields) | 1hr | [x] |
| 2.2 | #6 | Mock data — historical incidents (~10, 30-day range, diverse severities) | 1hr | [x] |
| 2.3 | #7 | Handler: incident_query_active — params (service, severity), filter + return | 1hr | [x] |
| 2.4 | #8 | Handler: incident_query_history — params (service, days), filter + return | 1hr | [x] |
| 2.5 | #9 | Handler: incident_get_timeline — params (incident_id), lookup + return events | 1hr | [x] |
| 2.6 | #10 | Example config.yaml for IncidentGPT | 0.5hr | [x] |
| 2.7 | #11 | Wire connector registration in server startup (import handlers, connect to registry) | 0.5hr | [x] |

### Epic 3: Testing + Demo

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 3.1 | — | Unit tests: config parsing, registry, error handling | 1hr | [x] |
| 3.2 | — | Unit tests: handlers (each tool + edge cases: empty results, missing params) | 1hr | [x] |
| 3.3 | — | Integration test: server startup → tools/list → tools/call (no auth, raw MCP) | 2hr | [x] |
| 3.4 | #11 | Demo: run mcplex serve, connect Claude Code, verify auto-discovery + tool calls | 1hr | |

### Epic 4: OSS Readiness

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 4.1 | #16 | Issue templates — bug report + feature request in `.github/ISSUE_TEMPLATE/` | 0.5hr | |
| 4.2 | #17 | Pull request template — `.github/PULL_REQUEST_TEMPLATE.md` | 0.5hr | |
| 4.3 | #18 | CODE_OF_CONDUCT.md (Contributor Covenant) | 0.5hr | |
| 4.4 | #19 | SECURITY.md — how to report vulnerabilities | 0.5hr | |
| 4.5 | #20 | GitHub Actions CI — lint (ruff), typecheck (pyright/mypy), unit tests on PR | 1hr | |

### Epic 5: Documentation

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 5.1 | #12 | README: what, why, quick start, architecture diagram, Claude Code setup | 1hr | [x] |
| 5.2 | #21 | Config reference: all YAML fields with examples | 1hr | [x] |
| 5.3 | #13 | Contributing guide: setup, test, submit PR | 0.5hr | |

**Sprint 1 total:** ~12.5 hours

---

## Sprint 2 — HTTP Proxy + Test Bench (Week 4, Jul 27 - Aug 2)

> **Milestone M2:** HTTP Proxy connector ships in OSS. Test bench simulates all 4 backends. 9 tools proxied and tested.

### Epic 6: HTTP Proxy Connector (Generic, Ships in OSS)

The core architectural shift. Instead of one Python file per connector, a generic HTTP proxy handler reads config and makes HTTP calls to any backend. Adding a new connector becomes a YAML change only.

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 6.1 | — | HTTP proxy handler — generic async fn that takes tool config + args, makes HTTP request | 1hr | [x] |
| 6.2 | — | Config schema for `type: http` connectors — base_url, method, path, param mapping, headers | 1hr | [x] |
| 6.3 | — | ToolRegistry: dynamic handler creation from `type: http` config entries | 1hr | [x] |
| 6.4 | — | Error handling — timeout (5s), non-200, connection refused → structured MCP error | 0.5hr | [x] |
| 6.5 | — | Auth support — static bearer token, header injection (for internal API keys) | 0.5hr | |
| 6.6 | — | Unit tests: HTTP proxy handler mocking responses, error conditions | 1hr | [x] |

### Epic 7: Test Bench — Mock All 4 Backend APIs

Docker topology for the test bench setup (Sprint 2):

```
┌────────────────────────────────────────────────────┐
│                  docker-compose.yml                 │
│                                                    │
│  ┌──────────────┐     HTTP proxy    ┌────────────┐ │
│  │  MCPlex      │ ────────────────▶ │ test-bench │ │
│  │  :8000       │                   │ :8001-8004 │ │
│  └──────────────┘                   └────────────┘ │
│         │                              │           │
│         │                              ├─ :8001 guardian (mock)
│         │                              ├─ :8002 ci-doctor (mock)
│         │                              ├─ :8003 sprint-intel (mock)
│         │                              └─ :8004 incident-cmdr (mock)
│         ▼
│  tools/list → 9 tools
│  tools/call  → proxied to backend
└────────────────────────────────────────────────────┘
```

After wiring 3 real repos (Sprint 3), the topology evolves to:

```
┌─────────────────────────────────────────────────────┐
│                   docker-compose.yml                  │
│                                                      │
│  ┌──────────────┐     HTTP proxy     ┌────────────┐  │
│  │  MCPlex      │ ─────────────────▶ │ test-bench │  │
│  │  :8000       │                    │ :8004      │  │
│  └──────────────┘                    └────────────┘  │
│         │                                            │
│         ├────────────────┐                           │
│         │                │                           │
│  ┌──────▼──────┐  ┌──────▼──────┐                    │
│  │  guardian   │  │  ci-doctor  │                    │
│  │  (real)     │  │  (real)     │                    │
│  │  :8080      │  │  :8080      │                    │
│  └─────────────┘  └─────────────┘                    │
│         │                                            │
│  ┌──────▼──────────┐                                 │
│  │  sprint-intel   │                                 │
│  │  (real)         │                                 │
│  │  :5000          │                                 │
│  └─────────────────┘                                 │
│         ▼                                             │
│  tools/list → 9 tools (6 from real repos)            │
└─────────────────────────────────────────────────────┘
```

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 7.1 | — | Mock ai-code-guardian: `/api/stats`, `/api/policy/check` endpoints | 0.5hr | [x] |
| 7.2 | — | Mock ci-doctor: `/api/diagnose`, `/api/history` endpoints | 0.5hr | [x] |
| 7.3 | — | Mock sprint-intelligence: `/api/dora/metrics`, `/api/dora/trend` endpoints | 0.5hr | [x] |
| 7.4 | — | Mock ai-incident-commander: `/api/incidents/*` endpoints | 0.5hr | [x] |
| 7.5 | — | config.yaml: all 4 connectors via `type: http` pointing to test bench | 0.5hr | [x] |
| 7.6 | — | docker-compose.yml: test-bench + mcplex, port 8080 | 1hr | [x] |

### Epic 8: E2E Test + Screenshots

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 8.1 | — | Playwright E2E test: launch Inspector, connect, call all 9 tools | 2hr | [x] |
| 8.2 | — | Capture 15 screenshots of full test flow | 1hr | [x] |
| 8.3 | — | E2E test plan & results doc in `tests/e2e/README.md` | 0.5hr | [x] |
| 8.4 | — | Update spec + user guide with test paths | 0.5hr | [x] |

**Sprint 2 total:** ~9.5 hours

---

## Sprint 3 — All 4 Real Repos + Docker Compose (Week 5, Aug 3-9)

> **Milestone M3:** 4 public repos connected with real APIs. docker-compose.yml. Full demo with Claude Code.

### Epic 9: ai-code-guardian Integration (Public Repo)

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 9.1 | — | Add MCP API adapter (`src/guardian/server/mcp_api.py`) to ai-code-guardian | 1hr | [x] |
| 9.2 | — | Swap config.yaml guardian entry from test-bench to real `base_url` | 0.5hr | [x] |
| 9.3 | — | Verify with Claude Code: guardian_check_policy, guardian_get_coverage both work | 1hr | |

### Epic 10: ci-doctor Integration (Public Repo)

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 10.1 | — | Add MCP API adapter (`app/mcp_api.py`) to ci-doctor | 1hr | [x] |
| 10.2 | — | Swap config.yaml ci-agent entry from test-bench to real `base_url` | 0.5hr | [x] |
| 10.3 | — | Verify with Claude Code: ci_diagnose_failure, ci_get_pipeline_history both work | 1hr | |

### Epic 11: sprint-intelligence Integration (Public Repo)

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 11.1 | — | Add MCP API adapter (`api/mcp_api.py`) to sprint-intelligence | 1hr | [x] |
| 11.2 | — | Swap config.yaml sprintsense entry from test-bench to real `base_url` | 0.5hr | [x] |
| 11.3 | — | Verify with Claude Code: dora_get_metrics, dora_get_trend both work | 1hr | |

### Epic 12: ai-incident-commander Integration (Public Repo)

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 12.1 | — | Evaluate ai-incident-commander for server capability | 0.5hr | [x] |
| 12.2 | — | Confirm CLI-only — no REST API possible without new framework | 0.5hr | [x] |
| 12.3 | — | Document: ai-incident-commander remains on test-bench mock | 0.5hr | [x] |

### Epic 13: Docker Compose (Real Repos) + Demo

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 13.1 | — | docker-compose.yml — 3 real services + test-bench + mcplex | 2hr | [x] |
| 13.2 | — | Full E2E test: all 9 tools via MCP Inspector | 1hr | [x] |
| 13.3 | — | README update: real repo quick start | 0.5hr | [x] |
| 13.4 | — | Screenshots captured for both test-bench and e2e | 1hr | [x] |

### Epic 14: Integration Doc

| WBS | Issue | Title | Est. | Status |
|-----|-------|-------|------|--------|
| 14.1 | — | docs/integration/README.md — how to connect each repo via MCP API adapters | 1hr | [x] |

**Sprint 3 total:** ~12.5 hours

---

## Sprint 4 — Production Hardening (Week 6+)

> **Milestone M4:** v1.0.0 — auth, audit, PyPI.

| WBS | Title | Est. | Status |
|-----|-------|------|--------|
| 13 | Streamable HTTP transport (SSE auto-detect on Accept header) | 4hr | [x] |
| 14 | Graceful degradation: per-connector timeout + error isolation + JSON validation | 2hr | [x] |
| 15 | OAuth 2.0 + OIDC authorization (read-by-default, write-on-approval) | 4hr | |
| 16 | Write tool MCP interrupt approval flow | 3hr | |
| 17 | Unified audit logging: all tool calls logged with agent identity, params, latency | 3hr | |
| 18 | PyPI publish: setup.py/sdist, GitHub Action release workflow | 2hr | |
| 19 | Rate limiting per tool/per agent | 2hr | |
| 20 | Configuration hot-reload (no restart needed for new connectors) | 2hr | |

**Sprint 4 total:** ~22 hours
