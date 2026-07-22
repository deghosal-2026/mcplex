"""
Unit tests for the HTTP proxy connector handler.

Covers GET/POST proxying, parameter mapping, header injection,
timeouts, error handling, non-JSON responses, and arg validation.
Uses httpx.MockTransport for in-process mock backends.
"""

import json

import httpx
import pytest

from mcplex.config import HttpToolConfig
from mcplex.connectors.http_proxy import make_proxy_handler, validate_args


def _json_backend(request: httpx.Request) -> httpx.Response:
    if request.method == "GET":
        return httpx.Response(200, json={"echo": dict(request.url.params)})
    body = json.loads(request.content) if request.content else {}
    return httpx.Response(200, json={"echo": body})


def _error_backend(request: httpx.Request) -> httpx.Response:
    return httpx.Response(500, json={"error": "internal"})


def _html_backend(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content="<html>dash</html>",
                          headers={"content-type": "text/html"})


def _make_handler(backend_fn, config, parameters=None):
    """Create a proxy handler with a mock transport backend."""
    transport = httpx.MockTransport(backend_fn)
    client = httpx.AsyncClient(transport=transport, follow_redirects=True)
    return make_proxy_handler("http://mock", config, parameters, shared_client=client), client


# ── Arg validation tests (#49) ──────────────────────────────────

def test_validate_args_type_mismatch():
    is_valid, msg = validate_args({"count": "abc"}, {"count": {"type": "integer"}})
    assert not is_valid
    assert "expected integer" in msg


def test_validate_args_required_missing():
    is_valid, msg = validate_args({}, {"name": {"type": "string", "required": True}})
    assert not is_valid
    assert "required" in msg


def test_validate_args_unknown_param():
    is_valid, msg = validate_args({"a": 1, "b": 2}, {"a": {"type": "integer"}})
    assert not is_valid
    assert "unknown" in msg


def test_validate_args_enum():
    is_valid, msg = validate_args({"sev": "sev9"}, {"sev": {"type": "string", "enum": ["sev1", "sev2", "sev3"]}})
    assert not is_valid
    assert "enum" in msg


def test_validate_args_minimum():
    is_valid, msg = validate_args({"n": -1}, {"n": {"type": "integer", "minimum": 0}})
    assert not is_valid
    assert "minimum" in msg


def test_validate_args_valid():
    is_valid, msg = validate_args(
        {"name": "test", "count": 5},
        {"name": {"type": "string"}, "count": {"type": "integer"}},
    )
    assert is_valid
    assert msg == ""


# ── Proxy handler tests with mock backend (#24) ──────────────────

@pytest.mark.asyncio
async def test_proxy_get_returns_json():
    config = HttpToolConfig(method="GET", path="/api/test", param_mapping={"name": "name"})
    handler, client = _make_handler(_json_backend, config)
    result = await handler({"name": "hello"})
    parsed = json.loads(result)
    assert parsed["echo"]["name"] == "hello"
    await client.aclose()


@pytest.mark.asyncio
async def test_proxy_post_returns_json():
    config = HttpToolConfig(method="POST", path="/api/submit", param_mapping={"data": "data"})
    handler, client = _make_handler(_json_backend, config)
    result = await handler({"data": "payload"})
    parsed = json.loads(result)
    assert parsed["echo"]["data"] == "payload"
    await client.aclose()


@pytest.mark.asyncio
async def test_proxy_error_status():
    config = HttpToolConfig(method="GET", path="/fail")
    handler, client = _make_handler(_error_backend, config)
    result = await handler({})
    parsed = json.loads(result)
    assert "error" in parsed
    assert "500" in parsed["error"]
    await client.aclose()


@pytest.mark.asyncio
async def test_proxy_html_wrapped():
    config = HttpToolConfig(method="GET", path="/dashboard")
    handler, client = _make_handler(_html_backend, config)
    result = await handler({})
    parsed = json.loads(result)
    assert "html" in parsed
    await client.aclose()


@pytest.mark.asyncio
async def test_proxy_validation_error():
    config = HttpToolConfig(method="GET", path="/api/test", param_mapping={"count": "count"})
    handler, client = _make_handler(_json_backend, config,
                                     parameters={"count": {"type": "integer"}})
    result = await handler({"count": "not-int"})
    parsed = json.loads(result)
    assert "error" in parsed
    assert "Invalid arguments" in parsed["error"]
    await client.aclose()


@pytest.mark.asyncio
async def test_proxy_unsupported_method():
    config = HttpToolConfig(method="PUT", path="/test")
    handler, client = _make_handler(_json_backend, config)
    result = await handler({})
    parsed = json.loads(result)
    assert "Unsupported HTTP method" in parsed["error"]
    await client.aclose()


@pytest.mark.asyncio
async def test_proxy_header_injection():
    config = HttpToolConfig(method="GET", path="/test", headers={"X-Key": "val"})
    handler, client = _make_handler(_json_backend, config)
    result = await handler({})
    parsed = json.loads(result)
    assert "echo" in parsed
    await client.aclose()
