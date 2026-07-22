"""
Self-contained integration tests — full proxy chain without Docker.

Tests the complete flow: config → registry → transport → http_proxy → mock backend.
Uses httpx.MockTransport to simulate backend HTTP responses in-process.
"""

import json

import httpx
import pytest
from starlette.testclient import TestClient

from mcplex.config import Config, ConnectorType, ToolDef, ConnectorDef, HttpToolConfig
from mcplex.connectors.http_proxy import make_proxy_handler
from mcplex.context import client_identity
from mcplex.server import create_app


def _mock_backend(request: httpx.Request) -> httpx.Response:
    """Mock backend that echoes params for GET and body for POST."""
    if request.method == "GET":
        return httpx.Response(200, json={"echo": dict(request.url.params)})
    elif request.method == "POST":
        body = json.loads(request.content) if request.content else {}
        return httpx.Response(200, json={"echo": body})
    return httpx.Response(405, json={"error": "method not allowed"})


def _mock_error_backend(request: httpx.Request) -> httpx.Response:
    """Mock backend that always returns 500."""
    return httpx.Response(500, json={"error": "internal"})


def _mock_html_backend(request: httpx.Request) -> httpx.Response:
    """Mock backend that returns HTML instead of JSON."""
    return httpx.Response(200, content="<html>dashboard</html>",
                          headers={"content-type": "text/html"})


@pytest.fixture
def mock_client():
    """Create an httpx.AsyncClient with a mock transport."""
    transport = httpx.MockTransport(_mock_backend)
    return httpx.AsyncClient(transport=transport, follow_redirects=True)


@pytest.fixture
def app_with_mock():
    """Build a Starlette app with a mock-backed HTTP connector."""
    transport = httpx.MockTransport(_mock_backend)
    mock_client = httpx.AsyncClient(transport=transport, follow_redirects=True)
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                type=ConnectorType.http,
                base_url="http://mock-backend",
                tools=[
                    ToolDef(
                        name="test_get",
                        description="GET test tool",
                        parameters={"name": {"type": "string", "description": "A name"}},
                        http=HttpToolConfig(method="GET", path="/api/test",
                                            param_mapping={"name": "name"}),
                    ),
                    ToolDef(
                        name="test_post",
                        description="POST test tool",
                        parameters={"data": {"type": "string", "description": "Data"}},
                        http=HttpToolConfig(method="POST", path="/api/submit",
                                            param_mapping={"data": "data"}),
                    ),
                ],
            ),
        ],
    )
    app = create_app(config, http_client=mock_client)
    return app


def test_integration_tools_list(app_with_mock):
    """tools/list returns both registered tools."""
    client = TestClient(app_with_mock)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/list",
    })
    tools = resp.json()["result"]["tools"]
    assert len(tools) == 2
    assert {t["name"] for t in tools} == {"test_get", "test_post"}


def test_integration_get_success(app_with_mock):
    """GET tool call proxies to mock backend and returns echoed params."""
    client = TestClient(app_with_mock)
    client_identity.set({"name": "test-agent", "version": "1.0"})
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "test_get", "arguments": {"name": "hello"}},
    })
    data = resp.json()
    text = data["result"]["content"][0]["text"]
    parsed = json.loads(text)
    assert parsed["echo"]["name"] == "hello"
    assert "isError" not in data["result"]["content"][0]


def test_integration_post_success(app_with_mock):
    """POST tool call proxies to mock backend and returns echoed body."""
    client = TestClient(app_with_mock)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "test_post", "arguments": {"data": "payload"}},
    })
    data = resp.json()
    text = data["result"]["content"][0]["text"]
    parsed = json.loads(text)
    assert parsed["echo"]["data"] == "payload"


def test_integration_validation_error():
    """Invalid argument type returns -32602 JSON-RPC error."""
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                type=ConnectorType.http,
                base_url="http://mock-backend",
                tools=[
                    ToolDef(
                        name="typed_tool",
                        description="Typed tool",
                        parameters={"count": {"type": "integer", "description": "A count"}},
                        http=HttpToolConfig(method="GET", path="/api/test",
                                            param_mapping={"count": "count"}),
                    ),
                ],
            ),
        ],
    )
    app = create_app(config)
    client = TestClient(app)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "typed_tool", "arguments": {"count": "not-an-int"}},
    })
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32602


def test_integration_unknown_tool(app_with_mock):
    """Calling an unknown tool returns isError."""
    client = TestClient(app_with_mock)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "nonexistent", "arguments": {}},
    })
    data = resp.json()
    assert data["result"]["content"][0]["isError"] is True


@pytest.mark.asyncio
async def test_integration_html_response_wrapped():
    """Non-JSON HTML response is wrapped in {"html": ...}."""
    transport = httpx.MockTransport(_mock_html_backend)
    mock_client = httpx.AsyncClient(transport=transport, follow_redirects=True)

    handler = make_proxy_handler(
        "http://mock",
        HttpToolConfig(method="GET", path="/dashboard"),
        shared_client=mock_client,
    )

    result = await handler({})
    parsed = json.loads(result)
    assert "html" in parsed
    assert "dashboard" in parsed["html"]
    await mock_client.aclose()


def test_integration_initialize_and_list():
    """Full handshake: initialize → tools/list."""
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                type=ConnectorType.http,
                base_url="http://mock",
                tools=[
                    ToolDef(name="t1", description="Tool 1", parameters={},
                            http=HttpToolConfig(method="GET", path="/t1")),
                ],
            ),
        ],
    )
    app = create_app(config)
    client = TestClient(app)

    init_resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "test-client", "version": "1.0"}},
    })
    assert init_resp.json()["result"]["serverInfo"]["name"] == "mcplex"

    list_resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/list",
    })
    tools = list_resp.json()["result"]["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "t1"
