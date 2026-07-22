# MCPlex — Technical Specification

## Architecture

```
┌────────────────────────────────────────────┐
│           Claude Code / Cursor             │
│         (discovers tools via MCP)          │
└────────────────────┬───────────────────────┘
                     │ tools/list → 9 tools
                     │ tools/call → dispatch
┌────────────────────▼───────────────────────┐
│              MCPlex Server                  │
│                                            │
│  ┌──────────────┐  ┌────────────────────┐ │
│  │  YAML Config │─▶│   Tool Registry    │ │
│  │  (connectors)│  │  name → handler    │ │
│  └──────────────┘  └────────┬───────────┘ │
│                             │              │
│  ┌──────────────────────────▼───────────┐ │
│  │      HTTP Proxy Handler              │ │
│  │  (generic — proxies to backend API)  │ │
│  │                                       │ │
│  │  ┌──────────────────────────────┐    │ │
│  │  │  Mock Connector (OSS demo)  │    │ │
│  │  │  IncidentGPT static data    │    │ │
│  │  └──────────────────────────────┘    │ │
│  └──────────────────────────────────────┘ │
└────┬──────────┬──────────┬──────────┬──────┘
     │          │          │          │
┌────▼──┐ ┌────▼──┐ ┌────▼──┐ ┌────▼─────┐
│Guardian│ │CI-Dr. │ │Sprint │ │Incident  │
│ :8001  │ │:8002  │ │:8003  │ │Commander │
└────────┘ └───────┘ └───────┘ │ :8004    │
                               └──────────┘
```

## Transport Layer

MCPlex ships HTTP-only, per the MCP Streamable HTTP spec (`2025-06-18`+). No stdio, no deprecated HTTP+SSE (`2024-11-05`) transport.

Two response modes, auto-detected by the client's `Accept` header on the single `/mcp` endpoint:

| `Accept` header | Response format | Use case |
|----------------|----------------|----------|
| `application/json` (default) | JSON-RPC over HTTP POST | Direct API calls, curl, scripts |
| `text/event-stream` | Server-Sent Events (SSE) | MCP Inspector, Streamable HTTP clients |

**JSON-RPC mode:** Client POSTs a JSON-RPC body to `/mcp`, server responds with `Content-Type: application/json`.

**SSE mode (Streamable HTTP):** Client POSTs with `Accept: text/event-stream`. Server responds with SSE events:
```
event: message
data: {"jsonrpc": "2.0", "id": 1, "result": {...}}

```

Both modes use the same `/mcp` endpoint and the same JSON-RPC message format — only the response framing differs. This is the current MCP transport spec; the old HTTP+SSE transport (`/sse` + `/message` endpoints, protocol `2024-11-05`) is deprecated and not implemented.

Used by the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) for visual debugging. E2E tested — see `tests/e2e/test_inspector_e2e.py`.

**Phase 2 (future):** OAuth, session management, long-running tool call streaming.

## Connector Architecture

MCPlex supports two connector types:

### 1. HTTP Proxy Connector (Generic, Ships in OSS)

The primary connector type. No Python code needed — everything is configured in YAML.

```yaml
connectors:
  - name: guardian
    type: http
    base_url: http://localhost:8001
    tools:
      - name: guardian_check_policy
        description: "Check a PR against AI code governance policy."
        http:
          method: POST
          path: /api/policy/check
          param_mapping:
            repo: repo
            pr_number: pr_number
        parameters:
          repo:
            type: string
            description: "Repository name"
        permission: read
```

**How it works:**
1. ToolRegistry reads `type: http` connectors from config
2. For each tool, it generates a handler function dynamically
3. When `tools/call` is invoked, the handler:
   - Maps MCP parameters → HTTP request params (via `param_mapping`)
   - Makes HTTP request to `base_url + path` with configured method
   - Returns response body as MCP tool result
   - On error (timeout, non-200, connection refused), returns structured error

**Config fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `type` | yes | Must be `"http"` |
| `base_url` | yes | Backend API base URL (e.g. `http://localhost:8001`) |
| `tools[].http.method` | no | HTTP method: GET (default) or POST |
| `tools[].http.path` | yes | URL path relative to base_url |
| `tools[].http.param_mapping` | no | Maps MCP param names → HTTP query/body param names |
| `tools[].http.headers` | no | Static headers to include (e.g. Authorization) |

### 2. Native Python Connectors (For Complex Logic)

For connectors that need transformation, aggregation, or fallback logic. Ships as Python modules in `mcplex/connectors/`.

Currently only the IncidentGPT mock connector uses this — it provides demo data so users can try MCPlex without running any backend.

### Error Handling

- HTTP proxy timeout: 5s (global constant; per-connector override planned)
- Non-200 response: return `{ "error": "backend returned {status}: {body}" }`
- Connection refused: return `{ "error": "{connector_name} is unavailable. Other tools are working." }`
- Per-connector isolation: one connector timeout doesn't block others

## Tool Registration

Tools are defined in YAML. The registry maps tool names to handler functions at startup.

### Config Shape

```yaml
connectors:
  - name: <connector_name>
    type: http | native
    base_url: <for http type>
    tools:
      - name: <tool_name>
        description: "Tool description for agent reasoning"
        http:  # only for type: http
          method: GET | POST
          path: /api/endpoint
          param_mapping:
            mcp_param: api_param
        parameters:
          param_name:
            type: string | integer | boolean
            description: "Parameter description"
        returns:
          type: object
        permission: read | write
```

## Reference Public Connectors (Ships in config.yaml.example)

| Connector | Backend | Tools |
|-----------|---------|-------|
| guardian | ai-code-guardian (:8001) | guardian_check_policy, guardian_get_coverage |
| ci-agent | ci-doctor (:8002) | ci_diagnose_failure, ci_get_pipeline_history |
| sprintsense | sprint-intelligence (:8003) | dora_get_metrics, dora_get_trend |
| incident-commander | ai-incident-commander (:8004) | incident_query_active, incident_query_history, incident_get_timeline |

## CLI Interface

```
mcplex serve [--config config.yaml]
```

- Reads config, creates HTTP proxy handlers, starts Starlette server
- Prints "MCPlex ready" on startup with tool count
- Logs every tool call to stdout

## Testing

- **Unit:** `tests/test_config.py`, `tests/test_registry.py`, `tests/test_incidentgpt.py`, `tests/test_transport.py` — config parsing, registry, handlers, transport
- **Integration:** run `mcplex serve` with test config, call `tools/list` + `tools/call` via curl
- **E2E:** `tests/e2e/test_inspector_e2e.py` — launches MCP Inspector, connects via Streamable HTTP, tests all 9 tools through the UI, captures screenshots to `tests/e2e/screenshots/`

## Future (Post-PoC)

| Feature | When |
|---------|------|
| OAuth 2.0 / OIDC auth | Phase 2 |
| Unified audit logging | Phase 2 |
| Tool call rate limiting | Phase 2 |
| Configuration hot-reload | Phase 2 |
| PyPI publish | v1.0.0 |
