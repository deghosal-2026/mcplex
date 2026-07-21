"""
Generic HTTP proxy connector.

Takes a ``(base_url, HttpToolConfig)`` pair and returns an async handler
that proxies MCP tool calls to a backend REST API.  No connector-specific
Python code is needed — everything is driven by the YAML config.

GET requests pass parameters as query arguments; POST requests pass them
as a JSON body.  If ``param_mapping`` is provided, only mapped fields
are forwarded (safe default).  Without a mapping, all arguments are sent
which can leak unexpected fields to the backend.
"""

import json
import logging

import httpx

from mcplex.config import HttpToolConfig

logger = logging.getLogger(__name__)

BACKEND_TIMEOUT_SECONDS = 5.0


def make_proxy_handler(base_url: str, http_config: HttpToolConfig):
    """Return an async handler that proxies to *base_url* + *http_config.path*.

    The returned handler accepts ``args: dict`` (the MCP tool arguments)
    and returns a JSON string.
    """
    async def handler(args: dict) -> str:
        # Construct the full URL, normalising slashes
        base = base_url.rstrip("/")
        path = http_config.path.lstrip("/")
        url = f"{base}/{path}"

        headers = http_config.headers or {}

        # Map MCP argument names → backend API parameter names
        mapping = http_config.param_mapping
        if mapping:
            mapped = {api_key: args[mcp_key]
                      for mcp_key, api_key in mapping.items()
                      if mcp_key in args}
        else:
            # No mapping defined — forward everything (intentional passthrough)
            mapped = dict(args)

        timeout = httpx.Timeout(BACKEND_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if http_config.method.upper() == "GET":
                    resp = await client.get(url, params=mapped, headers=headers)
                elif http_config.method.upper() == "POST":
                    resp = await client.post(url, json=mapped, headers=headers)
                else:
                    return json.dumps({"error": f"Unsupported HTTP method: {http_config.method}"})
            except httpx.TimeoutException:
                logger.warning("Backend timeout for %s (%.1fs)", url, BACKEND_TIMEOUT_SECONDS)
                return json.dumps({"error": f"Backend timed out after {BACKEND_TIMEOUT_SECONDS}s"})
            except httpx.RequestError as e:
                logger.warning("Backend request failed for %s: %s", url, e)
                return json.dumps({"error": f"Backend unreachable: {e}"})

            if resp.status_code >= 400:
                # Attempt to extract a meaningful error body
                snippet = resp.text[:200]
                return json.dumps({
                    "error": f"Backend returned {resp.status_code}",
                    "detail": snippet,
                })

            # Verify the backend returned valid JSON; if not, wrap it
            try:
                json.loads(resp.text)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Backend returned non-JSON for %s: %.100s", url, resp.text)
                return json.dumps({
                    "error": "Backend returned non-JSON response",
                    "detail": resp.text[:200],
                })

            return resp.text

    return handler
