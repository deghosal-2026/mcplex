# MCPlex Config Reference

## File Location

Default: `config.yaml` in the working directory.  Override with `--config`.

## Root Structure

```yaml
connectors:
  - name: <string>
    type: http                  # required
    base_url: <string>          # required — backend API root URL
    tools:
      - name: <string>          # MCP tool name
        description: <string>   # agent-optimized description
        parameters: <object>    # JSON Schema for tool parameters
        returns: <object>       # JSON Schema for return value (informational)
        http:
          method: <string>      # GET (default) or POST
          path: <string>        # URL path relative to base_url
          param_mapping: <dict> # MCP arg name → HTTP param name (optional)
          headers: <dict>       # static headers with ${ENV_VAR} interpolation
```

## Fields

| Field | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `connectors` | yes | array | | List of connector definitions |
| `connectors[].name` | yes | string | | Connector/module name |
| `connectors[].type` | yes | string | `"http"` | Connector type — currently only `"http"` |
| `connectors[].base_url` | yes | string | | Backend API root URL (e.g. `http://localhost:8001`) |
| `connectors[].tools` | yes | array | | List of MCP tool definitions |
| `tools[].name` | yes | string | | MCP tool name. Convention: `{system}_{action}` |
| `tools[].description` | yes | string | | Agent-optimized description. Tells the agent when to use this tool and what it returns |
| `tools[].parameters` | yes | object | | JSON Schema for tool parameters |
| `tools[].returns` | yes | object | | JSON Schema for the return value (informational) |
| `tools[].http.method` | no | string | `"GET"` | HTTP method: `GET` or `POST` |
| `tools[].http.path` | yes | string | | URL path relative to `base_url` (e.g. `/api/diagnose`) |
| `tools[].http.param_mapping` | no | object | `{}` | Maps MCP argument names → backend HTTP parameter names |
| `tools[].http.headers` | no | object | `{}` | Static headers injected on every request. Supports `${ENV_VAR}` interpolation |

## Environment Variable Interpolation

String values (especially `headers`) support `${VAR}` and `${VAR:-default}` patterns:

```yaml
http:
  headers:
    Authorization: "Bearer ${MCPLEX_AUTH_TOKEN}"
```

## Tool Naming Convention

```
{system}_{action}
```

Examples: `incident_query_active`, `guardian_check_policy`, `ci_diagnose_failure`

## Tool Description Best Practices

A good description tells the agent:
1. **When to use it** — "Query active incidents"
2. **What it returns** — "Returns severity, service, duration, responder"
3. **Why it's useful** — implicit in the above

Compare:
- ❌ `"Check policy"` — agents ignore this
- ✅ `"Check a pull request against AI code governance policy — returns pass/fail per rule with evidence"` — agents use this correctly

## Parameters

Uses JSON Schema types: `string`, `integer`, `number`, `boolean`, `array`, `object`.

Each parameter:
```yaml
parameters:
  service:
    type: string
    description: "Filter by service name (optional)"
  days:
    type: integer
    description: "Number of days to look back"
```

Mark optional parameters with "(optional)" in the description.
