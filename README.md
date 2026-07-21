# MCPlex

> The MCP backplane that unifies your AI agentic tools into one discoverable server.

AI coding agents (Claude Code, Cursor, Codex) call `tools/list` on startup. MCPlex makes every tool you've built appear automatically. Zero context switching. Zero learning curve. Maximum adoption.

## Why MCPlex?

I shipped 8 agentic systems. Average adoption: 22%. Each required a new UI, a new URL, a new context switch.

MCPlex changes the distribution model: one MCP server, 20+ tools. Agents discover everything on their next startup. Engineers never leave their editor.

## Quick Start

```bash
# Install
pip install mcplex

# Configure
mcplex init  # creates config.yaml

# Start server
mcplex serve
```

Then connect your AI coding agent (Claude Code, Cursor, Codex) to `http://localhost:8000`.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   MCPlex                        │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Guardian │  │IncidentGP│  │  CI-Agent│  ... │
│  │  3 tools │  │ 3 tools  │  │ 2 tools  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │        YAML Config-Driven Router        │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │   Stateless HTTP Transport (MCP 2026)   │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Roadmap

- [x] MCP server skeleton (stdio transport, YAML config)
- [ ] IncidentGPT connector (3 tools)
- [ ] Guardian connector (3 tools)
- [ ] CI-Agent connector (2 tools)
- [ ] RAGoncall connector (2 tools)
- [ ] SprintSense connector (2 tools)
- [ ] LoopGuard connector (2 tools)
- [ ] TierForge connector (2 tools)
- [ ] DocPulse connector (2 tools)
- [ ] Platform core tools (5 tools)
- [ ] 20+ MCP tools total
- [ ] Streamable HTTP transport
- [ ] OAuth 2.0 authorization
- [ ] Unified audit logging

## License

MIT
