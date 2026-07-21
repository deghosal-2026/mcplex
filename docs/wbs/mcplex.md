# MCPlex — Work Breakdown Structure

## Milestones

| MS | Version | Definition | Target |
|----|---------|------------|--------|
| M0 | v0.0.1 | Project scaffold: pyproject.toml, README, MIT, .gitignore | Week 3 (Jul 20) |
| M1 | v0.1.0 | PoC: HTTP server + IncidentGPT connector (3 tools) + demo with Claude Code | Week 3 (Jul 26) |
| M2 | v0.2.0 | 3 connectors: IncidentGPT + Guardian + CI-Agent (8 tools total) | Week 4 (Aug 2) |
| M3 | v0.3.0 | All 8 connectors + platform core (20+ tools) | Week 5 (Aug 9) |
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

### Epic 2: IncidentGPT Connector

| WBS | Issue | Title | Est. |
|-----|-------|-------|------|
| 2.1 | #5 | Mock data — active incidents (2-3 across 3 services, realistic fields) | 1hr |
| 2.2 | #6 | Mock data — historical incidents (~10, 30-day range, diverse severities) | 1hr |
| 2.3 | #7 | Handler: incident_query_active — params (service, severity), filter + return | 1hr |
| 2.4 | #8 | Handler: incident_query_history — params (service, days), filter + return | 1hr |
| 2.5 | #9 | Handler: incident_get_timeline — params (incident_id), lookup + return events | 1hr |
| 2.6 | #10 | Example config.yaml for IncidentGPT | 0.5hr |
| 2.7 | #11 | Wire connector registration in server startup (import handlers, connect to registry) | 0.5hr |

### Epic 3: Testing + Demo

| WBS | Issue | Title | Est. |
|-----|-------|-------|------|
| 3.1 | #12 | Unit tests: config parsing, registry, error handling | 1hr |
| 3.2 | #13 | Unit tests: IncidentGPT handlers (each tool + edge cases: empty results, missing params) | 1hr |
| 3.3 | #14 | Integration test: server startup → tools/list → tools/call (no auth, raw MCP) | 2hr |
| 3.4 | #15 | Demo: run mcplex serve, connect Claude Code, verify auto-discovery + tool calls | 1hr |

### Epic 4: Documentation

| WBS | Issue | Title | Est. |
|-----|-------|-------|------|
| 4.1 | #16 | README: what, why, quick start, architecture diagram, Claude Code setup | 1hr |
| 4.2 | #17 | Config reference: all YAML fields with examples | 1hr |
| 4.3 | #18 | Contributing guide: setup, test, submit PR | 0.5hr |

**Sprint 1 total:** ~12.5 hours

---

## Sprint 2 — 3 Connectors (Week 4, Jul 27 - Aug 2)

> **Milestone M2:** 8 total tools across IncidentGPT + Guardian + CI-Agent.

### Epic 5: Guardian Connector (#01)

| WBS | Issue | Title | Est. |
|-----|-------|-------|------|
| 5.1 | #19 | Mock governance data (policies, coverage scores per repo) | 1hr |
| 5.2 | #20 | Handler: guardian_check_policy — params (repo, pr_number), returns pass/fail per rule | 1hr |
| 5.3 | #21 | Handler: guardian_get_coverage — params (repo), returns coverage_pct, trend | 1hr |
| 5.4 | #22 | Handler: guardian_override_policy — write tool, requires approval | 1hr |

### Epic 6: CI-Agent Connector (#04)

| WBS | Issue | Title | Est. |
|-----|-------|-------|------|
| 6.1 | #23 | Mock CI data (pipeline failures, history, failure patterns per repo) | 1hr |
| 6.2 | #24 | Handler: ci_diagnose_failure — params (repo, run_id), root cause + similar failures | 1hr |
| 6.3 | #25 | Handler: ci_get_pipeline_history — params (repo, days), pass_rate, patterns | 1hr |

**Sprint 2 total:** ~7 hours

---

## Sprint 3 — All 8 Connectors (Week 5, Aug 3-9)

> **Milestone M3:** 20+ tools across all 8 connectors + platform core.

| WBS | Epic | Connector | Issues | Tools | Est. |
|-----|------|-----------|--------|-------|------|
| 7 | Epic 7 | RAGoncall (#02) | #26-#27 | rag_search, rag_get_document | 3hr |
| 8 | Epic 8 | SprintSense (#03) | #28-#29 | dora_get_metrics, dora_get_trend | 3hr |
| 9 | Epic 9 | LoopGuard (#58) | #30-#31 | loopguard_get_escalations, loopguard_get_cost | 3hr |
| 10 | Epic 10 | TierForge (#59) | #32-#33 | tierforge_get_cost, tierforge_get_usage | 3hr |
| 11 | Epic 11 | DocPulse (#06) | #34-#35 | docpulse_get_health, docpulse_flag_stale | 3hr |
| 12 | Epic 12 | Platform core | #36-#40 | deploy_trigger, deploy_get_status, policy_check, dashboard_query, catalog_get_service | 5hr |

**Sprint 3 total:** ~20 hours

---

## Sprint 4 — Production Hardening (Week 6+)

> **Milestone M4:** v1.0.0 — auth, audit, Streamable HTTP, PyPI.

| WBS | Issue | Title | Est. |
|-----|-------|-------|------|
| 13 | #41 | Streamable HTTP transport (MCP 2026-07-28 spec) | 4hr |
| 14 | #42 | OAuth 2.0 + OIDC authorization (read-by-default, write-on-approval) | 4hr |
| 15 | #43 | Write tool MCP interrupt approval flow | 3hr |
| 16 | #44 | Unified audit logging: all tool calls logged with agent identity, params, latency | 3hr |
| 17 | #45 | Graceful degradation: per-connector timeout + error isolation | 2hr |
| 18 | #46 | PyPI publish: setup.py/sdist, GitHub Action release workflow | 2hr |
| 19 | #47 | Rate limiting per tool/per agent | 2hr |
| 20 | #48 | Configuration hot-reload (no restart needed for new connectors) | 2hr |

**Sprint 4 total:** ~22 hours
