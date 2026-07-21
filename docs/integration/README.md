# MCPlex Integration Guide

Connect 4 open-source AI tools as a single MCP server. All repos are MIT-licensed and publicly available.

## The Problem

These 4 public repos exist — but none expose the REST endpoints MCPlex needs
to proxy to.  They're CLI tools, webhook receivers, or dashboard servers,
not MCP-ready backends.

The solution: a thin **MCP API adapter** (`app/mcp_api.py`) added to each repo
that wraps existing functionality in simple JSON endpoints.  MCPlex then
discovers and proxies to those endpoints via its generic HTTP proxy handler.

## Repos & Adapter Status

| # | Repo | Framework | MCP Adapter | Status |
|---|------|-----------|-------------|--------|
| 1 | [ai-code-guardian](https://github.com/deghosal-2026/ai-code-guardian) | FastAPI | `src/guardian/server/mcp_api.py` | Wired, 2 tools |
| 2 | [ci-doctor](https://github.com/deghosal-2026/ci-doctor) | FastAPI | `app/mcp_api.py` | Wired, 2 tools |
| 3 | [sprint-intelligence](https://github.com/deghosal-2026/sprint-intelligence) | Flask | `api/mcp_api.py` | Wired, 2 tools |
| 4 | [ai-incident-commander](https://github.com/deghosal-2026/ai-incident-commander) | CLI only | N/A | Test-bench mock |

## MCP API Adapter Pattern

Each adapter is a small module that adds REST endpoints to the repo's existing
web framework.  Example (ci-doctor):

```python
"""app/mcp_api.py — MCP API endpoints for MCPlex integration."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["mcp"])


@router.post("/diagnose")
async def diagnose(body: dict):
    repo = body.get("repo", "unknown")
    run_id = body.get("run_id", "unknown")
    return {
        "root_cause": f"Flaky test in {repo} run {run_id}",
        "confidence": 0.89,
        "suggested_fix": "Increase timeout or retry logic",
        ...
    }


@router.get("/history")
async def history(repo: str = "unknown", days: int = 30):
    return {
        "repo": repo,
        "total_runs": 89,
        ...
    }
```

Register it in the app:

```python
# app/main.py
from app.mcp_api import router as mcp_router
app.include_router(mcp_router)
```

## Running with Docker Compose

The `docker-compose.yml` in the MCPlex repo starts all 3 real repos plus
the test-bench (for incident-commander, which is CLI-only):

```
┌──────────────────────────────────────────────────────┐
│                    docker-compose.yml                  │
│                                                       │
│  ┌──────────────┐     HTTP proxy     ┌────────────┐  │
│  │  MCPlex      │ ─────────────────▶ │ test-bench │  │
│  │  :8000       │                    │ :8004      │  │
│  └──────────────┘                    └────────────┘  │
│         │                                             │
│         ├────────────────┐                            │
│         │                │                            │
│  ┌──────▼──────┐  ┌──────▼──────┐                    │
│  │  guardian   │  │  ci-doctor  │                    │
│  │  (real)     │  │  (real)     │                    │
│  │  :8080      │  │  :8080      │                    │
│  └─────────────┘  └─────────────┘                    │
│         │                                             │
│  ┌──────▼──────────┐                                  │
│  │  sprint-intel   │                                  │
│  │  (real)         │                                  │
│  │  :5000          │                                  │
│  └─────────────────┘                                  │
└──────────────────────────────────────────────────────┘
```

Start everything:

```bash
docker compose up -d --build
```

## Connecting Claude Code

```bash
claude --mcp http://localhost:8080/mcp
```

Claude auto-discovers all 9 tools on startup.

## Verifying with MCP Inspector

```bash
npx @modelcontextprotocol/inspector --transport http \
  --server-url http://localhost:8080/mcp
```

Opens a web UI at `http://localhost:6274` — explore all 9 tools, call them,
see live responses.

## E2E Test Plan & Results

See [tests/e2e/README.md](../../tests/e2e/README.md) for the full test plan,
results (9/9 passing), and 15 screenshots of the test flow.

## Adding Your Own Connector

1. Add a thin MCP API adapter to your repo's web framework
2. Add a YAML block to `config.yaml` with `type: http`
3. Define each tool with its HTTP method, path, and parameter mapping
4. Add the service to `docker-compose.yml`
5. Restart mcplex — no mcplex Python code needed
