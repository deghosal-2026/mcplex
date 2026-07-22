"""
Unit tests for the MCP transport layer.

Uses Starlette's TestClient against a fully-wired app with a single
test tool.  Covers all MCP methods, SSE framing, error handling,
and the /health endpoint.
"""

import json

import pytest
from starlette.testclient import TestClient

from mcplex.config import Config, ConnectorType, ToolDef, ConnectorDef
from mcplex.server import create_app


@pytest.fixture
def client():
    """TestClient wired with one native tool (``ping``)."""
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                type=ConnectorType.http,
                base_url="http://localhost:8000",
                tools=[
                    ToolDef(
                        name="ping",
                        description="Ping tool",
                        parameters={},
                        returns={"type": "object"},
                    )
                ],
            )
        ]
    )
    app = create_app(config)
    return TestClient(app)


def test_health(client):
    """GET /health returns 'ok'."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.text == "ok"


def test_tools_list(client):
    """POST /mcp with ``tools/list`` returns the tool catalog."""
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert len(data["result"]["tools"]) == 1
    assert data["result"]["tools"][0]["name"] == "ping"


def test_tools_call_unknown(client):
    """Calling a tool with no handler returns a JSON error message."""
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "nonexistent", "arguments": {}},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data["result"]["content"][0]["text"]


def test_tools_call_success(client):
    """Calling a registered tool invokes its handler and returns the result."""

    async def ping_handler(args):
        return json.dumps({"pong": True})

    client.app.state.registry.register_handler("ping", ping_handler)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "ping", "arguments": {}},
    })
    assert resp.status_code == 200
    data = resp.json()
    text = data["result"]["content"][0]["text"]
    assert json.loads(text)["pong"] is True


def test_unknown_method(client):
    """An unrecognised method returns a JSON-RPC method-not-found error."""
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 4,
        "method": "unknown_method",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32601


def test_initialize(client):
    """``initialize`` returns protocol version and server capabilities."""
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0.1.0"},
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "protocolVersion" in data["result"]
    assert "capabilities" in data["result"]
    assert "serverInfo" in data["result"]
    assert data["result"]["serverInfo"]["name"] == "mcplex"
    assert data["result"]["capabilities"]["tools"]["listChanged"] is False


def test_initialized_notification(client):
    """``initialized`` is a notification — returns an empty JSON object."""
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "initialized",
    })
    assert resp.status_code == 200
    # The notification response is an empty object
    assert resp.json() == {}


def test_malformed_json_body(client):
    """A non-JSON body returns a parse error with status 400."""
    resp = client.post("/mcp", content=b"not json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32700


def test_sse_framing(client):
    """When Accept includes text/event-stream, response uses SSE framing."""
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Accept": "text/event-stream"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert ": heartbeat" in body
    assert "event: message\ndata: " in body
    assert body.endswith("\n\n")


def test_sse_framing_case_insensitive(client):
    """Accept header matching is case-insensitive."""
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Accept": "TEXT/EVENT-STREAM"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")


def test_sse_returns_json_when_no_sse_header(client):
    """Without text/event-stream Accept header, response is ordinary JSON."""
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"


def test_tools_call_error_has_isError_flag(client):
    """A failed tool call includes isError: true on the content block."""
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "nonexistent", "arguments": {}},
    })
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]
    assert content["isError"] is True
    assert "error" in content["text"]


def test_tools_call_success_no_isError(client):
    """A successful tool call does not set isError."""
    async def ping_handler(args):
        return json.dumps({"pong": True})

    client.app.state.registry.register_handler("ping", ping_handler)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "ping", "arguments": {}},
    })
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]
    assert "isError" not in content


def test_json_rpc_batch_request(client):
    """A JSON-RPC 2.0 batch array returns an array of responses."""
    resp = client.post("/mcp", json=[
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0.1"}}},
    ])
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["result"]["tools"] is not None
    assert data[1]["result"]["serverInfo"]["name"] == "mcplex"


def test_non_dict_json_body_returns_error(client):
    """A non-object/non-array JSON body returns -32600 Invalid Request."""
    resp = client.post("/mcp", json="bare string",
                       headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == -32600


def test_initialized_notification_sse(client):
    """initialized with Accept: text/event-stream returns an SSE frame, not JSON."""
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "initialized"},
        headers={"Accept": "text/event-stream"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert ": heartbeat" in resp.text
    assert "event: message" in resp.text
