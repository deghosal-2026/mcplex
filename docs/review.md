# MCPlex Code Review

Review of mcplex core code, tests, and config. Comments only — no fixes applied.

---

## `mcplex/config.py`

- L17: `returns: dict = {}` — mutable default argument on a Pydantic field. Pydantic handles this safely, but it's a code-smell pattern that trips up linters and reviewers. Consider `returns: dict = Field(default_factory=dict)`.
- L24: `type: str = "native"` — no enum/validation. Any string is accepted. A typo like `type: htt` silently falls through `register_all` (L10 in `connectors/__init__.py` checks `== "http"`) and the connector's tools are silently dropped with no warning.
- L33-35: `load_config` has no error handling around file I/O or YAML parse. A missing file raises a raw `FileNotFoundError`; a bad YAML raises `yaml.YAMLError`. No structured error message telling the user which config file failed.

## `mcplex/registry.py`

- L7: `dict[str, callable]` — `callable` is the builtin, but the type annotation should be `Callable[..., Awaitable[str]]` for clarity and static analysis. As written, mypy/pyright will infer `callable` as the function type, not a callable type hint.
- L31: `return f'{{"error": "tool {name} not found"}}'` — manual JSON string construction. If `name` contains a double quote or backslash, the resulting JSON is malformed. Should use `json.dumps({"error": ...})`.
- L34: `return f'{{"error": "{e}"}}'` — same issue. Exception messages can contain quotes/newlines, producing invalid JSON.
- L7-10: The registry stores `ToolDef` objects from config but handlers are registered separately via `register_handler`. There's no validation that every tool has a handler registered — a misconfigured connector results in a "tool not found" error at call time rather than at startup.

## `mcplex/transport.py`

- L39: `"protocolVersion": "2025-06-18"` — hardcoded protocol version. The MCP spec version is dated and changes; this should be a constant or read from config. Also inconsistent with the WBS/spec docs which reference "MCP 2026-07-28 spec".
- L44-45: `method == "initialized"` returns a response with `result: {}`. Per MCP spec, the `initialized` notification is a notification (no `id`), so returning a response is technically incorrect — notifications should not get responses. The client may ignore it, but it's a protocol violation.
- L57: `body = await request.json()` — no try/except. A malformed JSON body raises an unhandled 500 error instead of a proper JSON-RPC error response (`code: -32700`, parse error).
- L67: `payload = f"event: message\ndata: {json.dumps(data)}\n\n"` — SSE payload is constructed correctly, but if `data` contains newlines in its values, `json.dumps` escapes them as `\n` (valid), so this is OK. However, the SSE `data:` field should split multi-line JSON across multiple `data:` lines per the SSE spec. `json.dumps` produces single-line output by default, so this works, but it's fragile.
- L60-63: Accept-header detection for SSE vs JSON is case-sensitive. `"text/Event-Stream"` would not match. HTTP headers are case-insensitive per RFC 7230.

## `mcplex/server.py`

- L13: `def create_app(config_or_path)` — accepts either a string path or a `Config` object. This dual-type parameter makes the API ambiguous and harder to test. Consider two separate entry points or always requiring a `Config` object.
- L14: `isinstance(config_or_path, str)` — if someone passes a `Path` object (which is not a `str`), it falls through to `ToolRegistry(config_or_path)` which would fail. The type hint is missing entirely.
- L24: `Route("/health", endpoint=lambda r: PlainTextResponse("ok"))` — inline lambda for a route. Works but not testable in isolation and slightly unusual for Starlette (typically a function).

## `mcplex/connectors/__init__.py`

- L1: `from mcplex.connectors import incidentgpt` — this import is at module level, meaning `incidentgpt` is always loaded even if no native connectors are configured. Since the project moved to HTTP-proxy-only, this native connector is dead code for OSS users.
- L6: `incidentgpt.register(registry)` — unconditionally registers the native IncidentGPT handlers. If config also defines an `incident-commander` connector with `incident_query_active` etc., the native handler overwrites the HTTP proxy handler (or vice versa, depending on order). There's a silent name collision with no warning.
- L13: `registry.register_handler(tool.name, handler)` — same collision risk. If two connectors define a tool with the same name, the last one wins silently.

## `mcplex/connectors/http_proxy.py`

- L8: URL construction via string concatenation. If `base_url` has a trailing path (e.g. `http://host/api`), it's preserved, which may or may not be intended. No support for path parameters (e.g. `/api/incidents/{incident_id}`).
- L11-15: `param_mapping` logic is odd. If `mcp_key in args`, it maps `api_key = args[mcp_key]`. If not, it does `args.get(mcp_key)` — which is always `None` since we just checked it's not in `args`. The else branch is dead code that always sets `None`.
- L17: `httpx.Timeout(10.0)` — hardcoded 10s timeout. The WBS mentions 5s. Should be configurable per-connector or per-tool.
- L20: `params = mapped_params if mapped_params else args` — if `param_mapping` is empty, ALL args are sent as query params (for GET) or body (for POST). This is a silent fallback that could leak unexpected fields to the backend.
- L29: `return f'{{"error": "backend returned {resp.status_code}: {resp.text[:200]}"}}'` — manual JSON string construction again. `resp.text` may contain quotes/newlines, producing invalid JSON.
- L30: `return resp.text` — returns the raw backend response text without validating it's JSON. If the backend returns HTML (e.g. a 404 page from a misconfigured proxy), the MCP client gets HTML stuffed into a `text` content field.

## `mcplex/connectors/incidentgpt.py`

- L1-121: This entire file is mock data for the PoC. It's still loaded unconditionally by `connectors/__init__.py` L1 and L6. For OSS release, this should be removed or made opt-in.
- L98: `days = args.get("days", 30)` — `days` comes from the MCP client as a string (the E2E test passes `"30"`), but `timedelta(days=days)` expects an int. If `days` is `"30"`, this raises `TypeError`. The test passes `"30"` as a string in the E2E test but the unit tests pass `7` as an int — inconsistent.

## `mcplex/main.py`

- L18: `app = create_app(args.config)` — no error handling. If the config file is missing, the user gets a traceback instead of a helpful message.
- L20: `uvicorn.run(app, ...)` — no graceful shutdown handling. The worker loop in `incidentgpt` (if active) would be killed without cleanup.

## `tests/test_config.py`

- L42-43: `import pytest` is inside the function body. Should be at module top.
- No test for `HttpToolConfig`, `ConnectorDef.type`, or `base_url` fields — the new HTTP proxy config schema is untested.
- No test for invalid config values (e.g. `type: invalid`, missing `path` in `http` config).

## `tests/test_registry.py`

- L7: `dict[str, callable]` type hint on `_handlers` — `callable` is not a valid type annotation in this context (should be `Callable`).
- No test for handler name collision (two handlers registered for the same tool name).
- No test for the HTTP proxy handler integration (registering a proxy handler and calling it).

## `tests/test_transport.py`

- No test for the `initialize` method response.
- No test for the `initialized` method.
- No test for SSE response framing (`Accept: text/event-stream`).
- No test for malformed JSON body (parse error handling).
- No test for the `tools/call` success path (only the unknown-tool error path is tested).

## `tests/test_incidentgpt.py`

- L67-69: `test_query_history_filters_by_days` — the assertion `all("2026-07" in i["date"] for i in data["incidents"])` is weak. It only checks the month string is present, not that the results are actually within the last 7 days. If the mock data had a 2026-07-01 date and `days=7` from a later date, this could pass incorrectly.
- Tests don't cover the `days` as string case that the E2E test exercises — type inconsistency is not caught.

## `tests/test_bench.py`

- L157: `incidents_timeline` returns 404 for missing incidents, but the other endpoints return empty arrays. Inconsistent error handling — the MCP proxy will get a 404 and return an error string, while other missing-data cases return `{"incidents": []}`.
- L170-183: Uses `multiprocessing.Process` with `daemon=True`. Daemon processes can be killed without cleanup when the parent exits. For a test bench this is fine, but uvicorn servers in daemon mode may not flush logs.
- No health endpoint on the test bench. The E2E test has no way to verify the test bench is ready before starting — it relies on `sleep` and retries.

## `tests/e2e/test_inspector_e2e.py`

- L7: Docstring still says "Screenshots → docs/user-guide/screenshots/" but `SCREENSHOT_DIR` (L29) is `tests/e2e/screenshots`. Stale comment.
- L29: `SCREENSHOT_DIR = Path(__file__).parent / "screenshots"` — correct, but the print on L7 is misleading.
- L57: `DANGEROUSLY_OMIT_AUTH=true` — hardcoded in the test. Fine for local E2E, but if this test ever runs in CI with a real Inspector, this is a security risk.
- L66-73: `launch_inspector` polls for 30 seconds. If the Inspector takes longer to start, the test proceeds with a dead process and fails confusingly.
- Test is not parameterized — all 9 tools are hardcoded in `TOOLS_TO_TEST`. Adding a tool requires editing the test.

## `config.yaml`

- Paths are inconsistent across connectors: guardian uses `/mcp/...`, ci-doctor uses `/api/...`, sprint-intel uses `/mcp/...`, incident-commander uses `/api/...`. This is because each repo's MCP adapter chose a different prefix. Not a bug, but confusing for someone reading the config.
- No `config.yaml.example` sync — `config.yaml.example` exists but may be out of date with the real `config.yaml`.

## `docker-compose.yml`

- L13-14: `GITHUB_TOKEN: "dummy-mcplex-demo"` — dummy token in plaintext. Fine for local demo, but this file is committed to the OSS repo. Should reference an env file or use `${GITHUB_TOKEN}` with a default.
- L6: `entrypoint: ["python", "-m", "guardian", "serve", "--port", "8080"]` — overrides the Dockerfile's ENTRYPOINT. The Dockerfile uses `ENTRYPOINT ["python", "-m", "guardian"]` without a `serve` subcommand, so this is necessary but fragile — if the CLI changes, this breaks.
- No healthcheck on any service. `depends_on: condition: service_started` only waits for the container to start, not for the app to be ready. MCPlex may try to connect to backends before they're accepting connections.

## `Dockerfile.bench`

- Not reviewed (not read). Should be checked for consistency with `Dockerfile`.

## General / Cross-cutting

- No logging anywhere in mcplex core (`config.py`, `registry.py`, `transport.py`, `http_proxy.py`). The WBS calls out "unified audit logging" as Sprint 4, but even basic `logging.info` for tool calls is absent. Debugging a failed proxy call requires reading the error string from the MCP response.
- No structured error type — errors are returned as JSON strings inside the `text` field of a content block. The MCP client has to parse the string to determine if it's an error. A proper error would use the JSON-RPC `error` field.
- `pyproject.toml` not reviewed in this pass — should check for dependency pinning and optional extras.
