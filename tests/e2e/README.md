# E2E Test Plan & Results

## Test Plan

### Scope

Verify MCPlex routes all 9 tools from 4 backend repos through a single
`/mcp` endpoint (Streamable HTTP) and returns valid responses.

### Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                      docker-compose.yml                         │
│                                                                 │
│  ┌──────────────┐     Streamable HTTP     ┌──────────────────┐  │
│  │ MCP Inspector │ ◀────────────────────▶ │  MCPlex Server   │  │
│  │  local:6274   │                        │  container:8000  │  │
│  └──────────────┘                        └────────┬─────────┘  │
│                                                   │             │
│                    ┌──────────────────────────────┼─────────┐   │
│                    │                              │         │   │
│              ┌─────▼──────┐             ┌─────────▼──────┐  │   │
│              │  ci-doctor │             │  test-bench    │  │   │
│              │  (real)    │             │  (3 mocks)     │  │   │
│              │  :8080     │             │  :8001,3,4     │  │   │
│              └────────────┘             └────────────────┘  │   │
│                                                             │   │
└─────────────────────────────────────────────────────────────┘   │
                                                                  │
  Host machine (macOS) ───────────────────────────────────────────┘
```

### Setup

| Component | Port | Description |
|-----------|------|-------------|
| MCPlex | 8000 | HTTP proxy server (`/mcp` endpoint) |
| guardian | 8080 | Real public repo (ai-code-guardian + MCP API adapter) |
| ci-doctor | 8080 | Real public repo (ci-doctor + MCP API adapter) |
| sprint-intel | 5000 | Real public repo (sprint-intelligence + MCP API adapter) |
| test-bench | 8004 | Mock backend for incident-commander (CLI-only repo) |

3 of 4 backends are real public repos with thin MCP API adapters.
Only incident-commander uses the test-bench mock (it's a CLI-only tool
with no HTTP server).

### Test Flow

1. Launch MCPlex + ci-doctor + test-bench via `docker-compose up`
2. Launch MCP Inspector (localhost:6274)
3. Connect Inspector to `http://localhost:8080/mcp`
4. Click **List Tools** — verify 9 tools appear
5. Call each tool with sample args — verify response contains expected keys

### Tools Tested

| # | Tool | Backend | Type | Expected Keys |
|---|------|---------|------|---------------|
| 1 | `guardian_check_policy` | ai-code-guardian | **real repo** | `passed`, `rules` |
| 2 | `guardian_get_coverage` | ai-code-guardian | **real repo** | `repo`, `coverage_pct` |
| 3 | `ci_diagnose_failure` | ci-doctor | **real repo** | `root_cause`, `confidence` |
| 4 | `ci_get_pipeline_history` | ci-doctor | **real repo** | `total_runs`, `pass_rate` |
| 5 | `dora_get_metrics` | sprint-intelligence | **real repo** | `deploy_frequency`, `lead_time` |
| 6 | `dora_get_trend` | sprint-intelligence | **real repo** | `weekly` |
| 7 | `incident_query_active` | ai-incident-commander | test-bench | `incidents` |
| 8 | `incident_query_history` | ai-incident-commander | test-bench | `incidents` |
| 9 | `incident_get_timeline` | ai-incident-commander | test-bench | `events` |

### How to Run

```bash
# Start services
docker compose up -d

# Run E2E test (requires Playwright + Inspector installed)
python3 tests/e2e/test_inspector_e2e.py
```

---

## Results

- **Date**: 2026-07-20
- **Status**: ✅ **9/9 tool calls passed**
- **Total tests**: 9
- **Passed**: 9
- **Failed**: 0

### Detailed Results

| # | Tool | Backend | Type | Status | Response Summary |
|---|------|---------|------|--------|-----------------|
| 1 | `guardian_check_policy` | ai-code-guardian | **real** | ✅ pass | 3 rules (hallucinated-apis, missing-error-handling, hardcoded-secrets) all passing |
| 2 | `guardian_get_coverage` | ai-code-guardian | **real** | ✅ pass | 87% coverage, 124/142 PRs reviewed, +5% trend |
| 3 | `ci_diagnose_failure` | ci-doctor | **real** | ✅ pass | Root cause: "Flaky test in my-org/payment-service run 123" (89% confidence) |
| 4 | `ci_get_pipeline_history` | ci-doctor | **real** | ✅ pass | 89 total runs, 76% pass rate, 2 failure patterns |
| 5 | `dora_get_metrics` | sprint-intelligence | **real** | ✅ pass | Deploy freq: daily, lead time: 4.2h, MTTR: 25min |
| 6 | `dora_get_trend` | sprint-intelligence | **real** | ✅ pass | 3-week trend showing improving deploy frequency |
| 7 | `incident_query_active` | ai-incident-commander | mock | ✅ pass | Active sev2 incident on payment-service |
| 8 | `incident_query_history` | ai-incident-commander | mock | ✅ pass | Historical sev1 incident (connection pool exhaustion) |
| 9 | `incident_get_timeline` | ai-incident-commander | mock | ✅ pass | 2 events (detected, action) + correlated deploy |

### Screenshots

15 screenshots captured covering the full test flow (see `screenshots/`):

| File | Description |
|------|-------------|
| `01-landing.png` | MCP Inspector landing page |
| `02-transport-selected.png` | Streamable HTTP transport selected |
| `03-url-entered.png` | Server URL `http://localhost:8080/mcp` entered |
| `04-connected.png` | Connection established |
| `05-tools-listed.png` | All 9 tools visible after List Tools |
| `06-01-guardian_check_policy.png` | Tool call result (**real ai-code-guardian** repo) |
| `06-02-guardian_get_coverage.png` | Tool call result (**real ai-code-guardian** repo) |
| `06-03-ci_diagnose_failure.png` | Tool call result (**real ci-doctor** repo) |
| `06-04-ci_get_pipeline_history.png` | Tool call result (**real ci-doctor** repo) |
| `06-05-dora_get_metrics.png` | Tool call result (**real sprint-intelligence** repo) |
| `06-06-dora_get_trend.png` | Tool call result (**real sprint-intelligence** repo) |
| `06-07-incident_query_active.png` | Tool call result (test-bench mock — incident-commander is CLI-only) |
| `06-08-incident_query_history.png` | Tool call result (test-bench mock — incident-commander is CLI-only) |
| `06-09-incident_get_timeline.png` | Tool call result (test-bench mock — incident-commander is CLI-only) |
| `07-final-overview.png` | Final overview showing all test results |
