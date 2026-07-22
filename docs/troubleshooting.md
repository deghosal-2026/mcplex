# Troubleshooting

## Tools appear in `tools/list` but calls return "tool not found"

**Cause**: A tool has metadata in `config.yaml` but no handler registered.

**Check**: Look for startup warnings:
```
Tool 'guardian_check_policy' (connector: guardian) has no handler registered
```

**Fix**: Ensure the connector has `type: http` and a valid `base_url`. The proxy handler is only created for HTTP connectors with a non-empty `base_url`.

## Backend timeout after 5 seconds

**Cause**: The global proxy timeout is 5 seconds (`mcplex/connectors/http_proxy.py:BACKEND_TIMEOUT_SECONDS`).

**Workaround**: Increase the constant value. Per-connector configurable timeout is planned for v1.0.0.

## "Backend returned non-JSON response" error

**Cause**: The backend returned HTML, plain text, or a redirect response.

**Fix**: Ensure the backend's endpoint returns `Content-Type: application/json` with a valid JSON body. MCPlex v0.3.0 does not handle non-JSON responses or redirects (though `follow_redirects` is enabled for 3xx responses). Add a thin REST adapter to the backend if it only speaks HTML/CLI — see the [Integration Guide](integration/README.md).

## Config parse error: "Connector 'X' is type 'http' but has no base_url"

**Cause**: A connector has `type: http` but `base_url` is missing or empty.

**Fix**: Add `base_url: http://YOUR_BACKEND:PORT` to the connector definition.

## Config hot-reload not working

**Cause**: SIGHUP may not be available on your platform (Windows, some container runtimes).

**Check**: Look for the startup log `SIGHUP not available on this platform — hot-reload disabled`.

**Alternative**: Restart the server: `mcplex serve --config config.yaml`.

## Tools called too fast — rate limited

**Cause**: Rate limits are configured in `config.yaml` under the `rate_limits` section.

**Response**: The agent receives:
```json
{"error": "Rate limit exceeded for 'ci_diagnose_failure': 30 requests per 60s. Retry in 12s."}
```

**Fix**: Increase `max_requests` or `window_seconds` in the rate limit config, or remove the limit for the tool.

## Audit logs show no client identity

**Cause**: The MCP client did not send `clientInfo` in its `initialize` request, or the client connects via a JSON-RPC path that doesn't include the initialize handshake.

**Expected**: Audit logs include `"client": {"name": "claude-code", "version": "1.0"}` if the client sends `clientInfo`. If missing, it appears as `null`.

## "module 'mcplex' has no attribute '__version__'" on older install

**Cause**: The package was installed before `__version__` was added to `mcplex/__init__.py`.

**Fix**: Reinstall: `pip uninstall mcplex-backplane && pip install mcplex-backplane`.

## SSE connection drops mid-request

**Cause**: MCPlex SSE is one-shot per response. If a proxy or load balancer drops idle connections with a timeout less than the backend response time, the SSE response will be truncated.

**Workaround**: Increase proxy read timeout (e.g., `proxy_read_timeout 30s` in nginx). SSE heartbeat keepalive is enabled; progress streaming is planned for v1.0.0.
