# MCPlex Config Reference

## File Location

Default: `config.yaml` in the working directory. Override with `--config`.

## Root Structure

```yaml
connectors:
  - name: <string>
    tools:
      - name: <string>
        description: <string>
        parameters: <object>
        returns: <object>
        permission: <"read" | "write">
```

## Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `connectors` | yes | array | List of connector definitions |
| `connectors[].name` | yes | string | Connector/module name. Must match the handler module in `mcplex/connectors/` |
| `connectors[].tools` | yes | array | List of MCP tool definitions |
| `connectors[].tools[].name` | yes | string | MCP tool name. Agents use this to call the tool. Convention: `{system}_{action}` |
| `connectors[].tools[].description` | yes | string | Agent-optimized description. Tells the agent when to use this tool and what it returns |
| `connectors[].tools[].parameters` | yes | object | JSON Schema for tool parameters. Each key is a parameter name |
| `connectors[].tools[].returns` | yes | object | JSON Schema for the return value (informational) |
| `connectors[].tools[].permission` | no | string | `"read"` (default) or `"write"`. Write tools require human approval |

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
