# Changelog

## v0.4.0

### Production Hardening
- Schema/argument validation — type checking, required fields, enum, min/max, unknown param rejection (#49)
- Per-agent rate limiting to protect backends from flooding (#29)
- Structured audit logging: session_id, user_id, response_size_bytes, backend_url, http_status (#23)

### Proxy Engine
- Shared httpx.AsyncClient per process for connection pooling instead of per-call (#62)
- Client identity forwarded as X-MCP-Client-Name / X-MCP-Client-Version headers to backends (#27)
- Non-JSON responses (HTML/text) gracefully wrapped instead of erroring (#30)
- SSE keepalive heartbeat frame (#45)
- httpx follow_redirects enabled for 3xx responses (#63)

### Fixes
- Docker Compose health checks on test-bench for correct startup ordering (#33)
- Incident mock dates relative to datetime.now() — no time-bomb (#59)
- Production Dockerfile switches from editable install to regular install (#61)
- MCP protocol version aligned to 2025-06-18 (#74)
- mcplex/__main__.py + __version__ added (#73)
- Correct handler types in test_registry.py (#72)
- Static CI badge replaced with live GitHub Actions badge (#65)
- CODE_OF_CONDUCT enforcement email completed (#69)
- Notification Accept: text/event-stream returns SSE, not JSON (#76)
- pytest config (asyncio_mode, testpaths) added (#77)
- CI matrix now tests Python 3.11 and 3.12 (#75)
- E2E screenshot path corrected, dead code removed (#66, #67)
- README connector naming aligned with config (#71)

### Docs
- Architecture doc, deployment guide, troubleshooting guide added (#48, #47)
- Config reference updated with full HTTP connector schema (#51)
- WBS completion statuses corrected (#64)

### Tests
- 75 total tests (+31): HTTP proxy (13), integration (7), rate limiter (5), validation (6)
- 9/9 Playwright E2E tests passing across all 4 backends
