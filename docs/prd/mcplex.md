# MCPlex — Product Requirements Document

## User Personas

| Persona | Title | Goal | Pain Point |
|---------|-------|------|------------|
| **Alex** | Engineer (backend/platform) | Ship code fast. Knows tooling exists but won't learn N different UIs. Stays in editor. | "I know we have incident tools and policy checkers somewhere. I don't have time to learn 8 dashboards. I'll just do it manually." |
| **Jordan** | Platform Engineer | Build and maintain internal tools. Wants maximum adoption with minimum overhead. | "I shipped 5 agentic tools this quarter. Adoption is stuck at 20%. I can't keep sending Slack reminders about tools nobody uses." |
| **Sam** | Engineering Director | Ensure the org uses AI tools effectively. Wants data on what's being adopted and where value is delivered. | "We're spending engineering time building AI tools but I can't tell which ones are actually used. I need adoption metrics." |

## User Journeys

### Journey 1: Auto-Discovery + First Use (Alex)

**Trigger:** Alex opens Claude Code to debug a production incident.

| Step | Actor | Action | System Response | Emotion |
|------|-------|--------|-----------------|---------|
| 1 | Alex | Opens Claude Code in terminal | Claude Code connects to MCPlex on startup, calls `tools/list` | Neutral |
| 2 | Alex | Types: "check if there are any active incidents right now" | Agent discovers `incident_query_active`. Calls it. Returns: "2 active incidents: INC-2026-142 (sev2, payment-service, 45min) and INC-2026-148 (sev3, auth-service, 12min)" | Surprised — "it just worked" |
| 3 | Alex | Types: "what's the runbook for payment-service?" | Agent discovers `rag_search`. Returns top 3 runbooks with summaries | Delighted — never left editor |
| 4 | Alex | Types: "check the deploy history for payment-service" | Agent discovers `ci_get_pipeline_history`. Returns deployment frequency + last 3 deploy times | Delighted — "this saved me 5 minutes of clicking around" |

**Success criteria:**
- Alex discovers tools without any training or documentation
- Alex uses at least 3 different tools in their first session
- Alex returns to use tools again within the same week

**Adoption metric:** Tool return rate >60% (tried it → used it again)

### Journey 2: New Engineer Onboarding (Alex, week 1)

**Trigger:** Alex joins the team. Day 1: sets up dev environment.

| Step | Actor | Action | System Response | Emotion |
|------|-------|--------|-----------------|---------|
| 1 | Alex | Installs Claude Code + connects to MCPlex | `tools/list` returns 20+ tools across all systems | Overwhelmed → curious |
| 2 | Alex | Types: "what can you help me with?" | Agent reads all tool descriptions, summarizes: "I can check governance policies, query incidents, diagnose CI failures, search runbooks, check DORA metrics..." | "Wow, this is my entire platform in one place" |
| 3 | Alex | Types: "find the coding standards for Python services" | Agent calls `rag_search` with relevant query. Returns linked ADR | Productive on day 1 |
| 4 | Alex | Checks in their first PR | Agent calls `guardian_check_policy` automatically, flags AI-generated code for review | Protected without knowing the policy existed |

**Success criteria:**
- Alex uses MCPlex tools within the first hour of their first day
- Alex doesn't need onboarding docs about individual tools
- Alex's PR passes governance check without prior knowledge of the rules

**Adoption metric:** Time-to-first-tool-call <1 hour from setup

### Journey 3: Platform Engineer Adds a New Connector (Jordan)

**Trigger:** Jordan ships a new internal tool — Deployment Dashboard.

| Step | Actor | Action | System Response | Emotion |
|------|-------|--------|-----------------|---------|
| 1 | Jordan | Writes YAML config for `deploy_trigger`, `deploy_get_status`, `deploy_rollback` tools | MCPlex validates schema, registers tools | Confident |
| 2 | Jordan | Restarts MCPlex server | Server loads new config, all 3 tools available | Satisfied |
| 3 | Jordan | Opens Claude Code, types: "can I deploy payment-service to staging?" | Agent discovers `deploy_trigger`. Calls it. Returns: "Deploy #1423 started. Strategy: canary. Estimated: 4min." | "That was 15 minutes of YAML" |
| 4 | Jordan | Checks audit log | Logs show: which agent, which user, which tool, parameters, latency | Trustworthy |

**Success criteria:**
- Adding a new tool takes <30 minutes (write YAML, restart, verify)
- No MCP SDK code needed for basic tools
- YAML schema catches errors at load time, not runtime

**Adoption metric:** Time-to-add-tool <30 minutes (platform engineer)

### Journey 4: Graceful Degradation During Outage (Alex)

**Trigger:** IncidentGPT database is down for maintenance.

| Step | Actor | Action | System Response | Emotion |
|------|-------|--------|-----------------|---------|
| 1 | Alex | Types: "any active incidents?" | MCPlex calls IncidentGPT API → timeout. Returns: `error: "IncidentGPT is currently unavailable. Other tools (guardian, ci, rag, dora) are working."` | Frustrated → reassured |
| 2 | Alex | Types: "ok, check if our last deploy caused any CI failures" | Agent calls `ci_diagnose_failure` normally. Returns results. | Satisfied — other tools still work |

**Success criteria:**
- One system going down doesn't break other tools
- Error message tells the agent (and engineer) which subsystems are affected
- Agent adapts and uses available tools instead of failing entirely

**Adoption metric:** Zero "MCPlex is down" reports during single-system outages

### Journey 5: Write Tool with Human Approval (Alex → Sam)

**Trigger:** Alex needs to roll back a bad deploy.

| Step | Actor | Action | System Response | Emotion |
|------|-------|--------|-----------------|---------|
| 1 | Alex | Types: "roll back payment-service to the previous version" | Agent calls `deploy_rollback`. MCPlex returns: "This action requires approval. Type 'approve' to continue." | Patient |
| 2 | Sam | Reviews the request in Claude Code. Types: "approve" | MCPlex receives approval, executes rollback. Returns: "Rollback #1422 started. Estimated: 3min." | Safe — human in loop |
| 3 | Sam | Checks audit log later | Full trail: Alex requested → Sam approved → rollback executed. All tool calls logged across all sessions. | Auditable |

**Success criteria:**
- Write tools require explicit human approval
- Approval prompt clearly states what the action will do
- All actions are logged with agent identity, parameters, and approval chain

**Adoption metric:** Zero unauthorized write operations

## Permissions Model

| Level | Examples | Approval |
|-------|----------|----------|
| Read | `incident_query_active`, `guardian_check_policy`, `rag_search` | None |
| Write (sensitive) | `deploy_rollback`, `deploy_trigger`, `guardian_override_policy` | MCP interrupt (human approves in chat) |

## Transport

MCPlex auto-detects Streamable HTTP (SSE) when clients send `Accept: text/event-stream`. Use the MCP Inspector for visual debugging:

```bash
npx @modelcontextprotocol/inspector --transport http \
  --server-url http://localhost:8080/mcp
```

Opens a web UI at `http://localhost:6274` to explore tools, call them, and inspect responses.

## Success Metrics

| Metric | Target |
|--------|--------|
| Average tool adoption | >60% (baseline: 22% pre-MCPlex) |
| Tool calls | >1,000/month |
| Time-to-add-connector | <30 minutes |
| Time-to-first-tool-call (new hire) | <1 hour |
| System availability | 99.9% (individual connector outages don't affect others) |
