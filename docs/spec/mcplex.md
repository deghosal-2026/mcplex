# MCPlex — Technical Specification

## Architecture

```
┌───────────────────────────────────────────────┐
│               AI Coding Agent                  │
│         (Claude Code / Cursor / Codex)         │
└──────────────────┬────────────────────────────┘
                   │ MCP stdio / HTTP
┌──────────────────▼────────────────────────────┐
│                  MCPlex                        │
│                                                │
│  ┌──────────────┐    ┌──────────────────────┐ │
│  │  YAML Config │───▶│   Tool Registry      │ │
│  │  (connectors) │    │  (name → handler)    │ │
│  └──────────────┘    └──────────┬───────────┘ │
│                                 │              │
│  ┌──────────────────────────────▼───────────┐ │
│  │         MCP Transport Layer              │ │
│  │  tools/list → tool definitions           │ │
│  │  tools/call → dispatch to handler        │ │
│  └──────────────────────────────────────────┘ │
│                                 │              │
│  ┌──────────────────────────────▼───────────┐ │
│  │         Connector Handlers               │ │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │Guardian │ │Incident  │ │  CI      │  │ │
│  │  │ handler │ │GPT handle│ │Agent hdl│  │ │
│  │  └─────────┘ └──────────┘ └──────────┘  │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

## Transport Layer

**Phase 1 (PoC):** stdio transport — agent spawns MCPlex as a subprocess, communicates over stdin/stdout using MCP JSON-RPC messages. Zero networking, zero auth. Simplest possible integration.

**Phase 2:** Streamable HTTP (MCP 2026-07-28 spec) — supports multiple concurrent agents, OAuth, remote access.

## Tool Registration

Tools are defined in YAML. Each connector has a YAML block and a Python handler module.

### Config Shape

```yaml
connectors:
  - name: incidentgpt
    tools:
      - name: incident_query_active
        description: "Query currently active incidents. Returns ongoing incidents with severity, service, duration, and responder."
        parameters:
          service:
            type: string
            description: "Filter by service name (optional)"
          severity:
            type: string
            description: "Filter by severity level: sev1, sev2, sev3 (optional)"
        returns:
          type: object
          properties:
            incidents:
              type: array
        permission: read

      - name: incident_query_history
        description: "Query historical incidents with optional filters."
        parameters:
          service:
            type: string
            description: "Filter by service name"
          days:
            type: integer
            description: "Number of days to look back"
        returns:
          type: object
        permission: read
```

### Handler Registration

Each connector registers a Python async function per tool:

```python
# mcplex/connectors/incidentgpt.py
async def handle_incident_query_active(args: dict) -> str:
    # returns JSON string of results
    ...
```

The registry maps YAML tool names → handler functions at startup.

## Connector Design

### Pattern

Every connector follows the same pattern:

1. **YAML definition** in `config.yaml` — tool name, description, parameters, returns, permission
2. **Handler function** — async function that takes `dict` args, returns `str` (JSON)
3. **Mock data** for PoC — static sample data so the demo works without real backends

### IncidentGPT Connector — Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `incident_query_active` | service (opt), severity (opt) | List of active incidents |
| `incident_query_history` | service, days | List of historical incidents |
| `incident_get_timeline` | incident_id | Full incident timeline with events |

### Mock Data

PoC uses static sample data simulating 2-3 active incidents and ~10 historical incidents across 3 services (payment-service, auth-service, api-gateway). Realistic but fake — enough to demo the full flow.

## Implementation Plan (PoC)

### Step 1: Project skeleton
- `pyproject.toml` with mcp SDK dependency
- `mcplex/main.py` — CLI entry point (`mcplex serve`)
- `mcplex/server.py` — MCP stdio server
- `mcplex/config.py` — YAML config loader
- `mcplex/registry.py` — tool name → handler mapping

### Step 2: IncidentGPT connector
- `mcplex/connectors/__init__.py`
- `mcplex/connectors/incidentgpt.py` — handler functions + mock data
- Register handlers in server startup

### Step 3: Demo
- `config.yaml.example` — complete config for IncidentGPT
- Run `mcplex serve` with Claude Code
- Verify: "check for active incidents" → discovers + calls tool

## CLI Interface

```
mcplex serve [--config config.yaml]
```

- Reads config, loads connectors, starts MCP stdio server
- Prints "MCPlex ready" on startup
- Logs tool calls to stdout

## Error Handling

- Unknown tool name → return structured error string
- Connector timeout (5s default) → return timeout error for that tool only
- Config parse error → exit with clear message on startup
- Handler exception → return error string with traceback

## Testing

- **Unit:** test config parsing, registry, each handler with mock args
- **Integration:** run `mcplex serve`, connect with a test script that calls tools/list and tools/call
- **Demo:** open Claude Code, type prompts manually

## Future (Post-PoC)

| Feature | When |
|---------|------|
| Streamable HTTP transport | Phase 2 |
| OAuth 2.0 / OIDC auth | Phase 2 |
| Unified audit logging | Phase 2 |
| Tool call rate limiting | Phase 2 |
| GitHub Action for auto-deploy | Phase 2 |
| PyPI publish | When 3+ connectors shipped |
