import json
import pytest
from starlette.testclient import TestClient

from mcplex.config import Config, ToolDef, ConnectorDef
from mcplex.registry import ToolRegistry
from mcplex.server import create_app


@pytest.fixture
def client():
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                tools=[
                    ToolDef(
                        name="ping",
                        description="Ping tool",
                        parameters={},
                        returns={"type": "object"},
                        permission="read",
                    )
                ],
            )
        ]
    )
    app = create_app(config)
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.text == "ok"


def test_tools_list(client):
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
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "nonexistent", "arguments": {}},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data["result"]["content"][0]["text"]


def test_unknown_method(client):
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "unknown_method",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32601
