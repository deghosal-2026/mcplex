# Deployment Guide

## Quick Start (Development)

```bash
pip install mcplex-backplane

# Run with test-bench mock (no sibling repos needed)
python tests/test_bench.py &
mcplex serve --config config.yaml
```

## Docker Compose (Full Stack)

Requires 3 sibling repos cloned alongside mcplex:

```bash
git clone https://github.com/deghosal-2026/mcplex
cd mcplex
git clone https://github.com/deghosal-2026/ai-code-guardian ../ai-code-guardian
git clone https://github.com/deghosal-2026/ci-doctor ../ci-doctor
git clone https://github.com/deghosal-2026/sprint-intelligence ../sprint-intelligence

cp .env.example .env
docker compose up
```

MCPlex exposes port 8080 → mapped to container port 8000.

Connect Claude Code:
```bash
claude --mcp http://localhost:8080/mcp
```

## Production Deployment

MCPlex v0.3.0 is a proof-of-concept — not production-hardened. For evaluation or light internal use:

### Behind nginx

```nginx
server {
    listen 443 ssl;
    server_name mcplex.internal;

    location /mcp {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;
        proxy_buffering off;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### Environment Variables

| Variable | Used In | Description |
|---|---|---|
| `MCPLEX_AUTH_TOKEN` | `config.yaml` `headers` | Bearer token injected via `${MCPLEX_AUTH_TOKEN}` |
| `GITHUB_TOKEN` | docker-compose, ci-doctor | GitHub API token for CI diagnosis |

### Config Hot-Reload

Send `SIGHUP` to reload `config.yaml` without restarting:

```bash
kill -HUP $(pgrep -f "mcplex serve")
```

Invalid config on reload keeps the current config running — no downtime.

## Security Considerations

- **No auth layer**: MCPlex itself has no authentication. Protect it behind a reverse proxy (nginx/Caddy) with your org's auth (OAuth2 proxy, mTLS, VPN).
- **No write gating**: All tools execute immediately. Do not expose destructive backends through MCPlex without backend-level auth.
- **Secrets in config**: Use `${ENV_VAR}` interpolation for headers containing tokens. Never commit literal secrets to `config.yaml`.
- **Identity propagation**: Client identity from `initialize.params.clientInfo` is forwarded to backends as `X-MCP-Client-Name` and `X-MCP-Client-Version` headers.

## Health Check

```bash
curl http://localhost:8000/health
# → "ok"
```
