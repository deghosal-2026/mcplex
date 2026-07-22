# MCPlex Architecture

## Overview

MCPlex is a stateless HTTP proxy that implements the [MCP (Model Context Protocol)](https://spec.modelcontextprotocol.io/) wire protocol (JSON-RPC over HTTP + SSE). It sits between AI coding agents and backend REST APIs, translating MCP's `tools/list` / `tools/call` handshake into HTTP requests.

## Component Diagram

```
 AI Agent (Claude Code, Cursor, Codex)
        │
        │  JSON-RPC over HTTP POST
        ▼
 ┌─────────────────────────────────┐
 │         MCPlex Server            │
 │  (Starlette ASGI, port 8000)     │
 │                                  │
 │  ┌─────────────────────────────┐ │
 │  │   Transport Layer           │ │
 │  │   - JSON-RPC parsing        │ │
 │  │   - SSE framing             │ │
 │  │   - Batch request handling  │ │
 │  │   - Identity extraction     │ │
 │  └──────────┬──────────────────┘ │
 │             │                     │
 │  ┌──────────▼──────────────────┐ │
 │  │   Tool Registry             │ │
 │  │   - Tool metadata (YAML)    │ │
 │  │   - Handler routing         │ │
 │  │   - Orphan detection        │ │
 │  └──────────┬──────────────────┘ │
 │             │                     │
 │  ┌──────────▼──────────────────┐ │
 │  │   HTTP Proxy Handler        │ │
 │  │   - Arg validation          │ │
 │  │   - Param mapping           │ │
 │  │   - GET/POST proxying       │ │
 │  │   - Error handling          │ │
 │  └──────────┬──────────────────┘ │
 │             │                     │
 │  ┌──────────▼──────────────────┐ │
 │  │   Rate Limiter              │ │
 │  │   - Sliding window          │ │
 │  │   - Per-tool limits         │ │
 │  └─────────────────────────────┘ │
 └─────────────┬───────────────────┘
               │  HTTP (GET/POST + JSON)
               ▼
 ┌─────────────────────────────────┐
 │     Backend REST APIs            │
 │  (guardian, ci-doctor, etc.)     │
 └─────────────────────────────────┘
```

## Data Flow: `tools/call`

1. Agent sends `POST /mcp` with a JSON-RPC `tools/call` request.
2. Transport parses the body, validates structure (non-dict → `-32600`, batch → array dispatch).
3. Request dispatches to `tools/call` handler.
4. Rate limiter checks the tool's call count; rejects with `isError` if over limit.
5. Tool name is looked up in the registry; returns `isError` if unknown.
6. Handler validates arguments against declared JSON Schema.
7. MCP argument names are mapped to HTTP parameter names via `param_mapping`.
8. HTTP request is made (GET with query params, POST with JSON body).
9. Response is wrapped in an MCP `CallToolResult` with `isError` if the tool failed.
10. Audit event is logged with timestamp, tool name, client info, latency.

## Key Design Decisions

### No MCP SDK — Raw JSON-RPC

MCPlex implements the MCP wire protocol directly. The protocol is JSON-RPC 2.0 over HTTP — `initialize`, `tools/list`, `tools/call`, and `initialized`. No SDK dependency, no abstraction layer. This keeps the proxy ~400 lines of production code.

### YAML-Driven Connectors

The 80% case is a simple GET/POST proxy to a JSON REST endpoint. These are configured entirely in YAML — no Python code per connector. The remaining 20% (CLI-only backends, chained calls) use native Python connectors (`incidentgpt.py`) registered explicitly in code.

### One-Shot SSE Framing

SSE transport is auto-detected by the `Accept: text/event-stream` header. The implementation is one-shot per request — no session continuity, no keepalive, no progress streaming. This is a deliberate simplification for v0.3.0.

### Config Validation at Load Time

Pydantic validates all config at startup. `type: http` with missing `base_url` is rejected. Environment variables (`${VAR}` / `${VAR:-default}`) are interpolated. Invalid config prevents startup, not silent failure.

## Transport Modes

| Accept Header | Response | Session Model |
|---|---|---|
| `application/json` | JSON-RPC 200 | Stateless |
| `text/event-stream` | SSE `event: message` | One-shot |

## Version

The server reports its version dynamically from `importlib.metadata` on every `initialize` response. The MCP protocol version is `2025-06-18`.
