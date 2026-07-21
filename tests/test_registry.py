import json
import pytest

from mcplex.config import Config, ToolDef, ConnectorDef
from mcplex.registry import ToolRegistry


@pytest.fixture
def registry():
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                tools=[
                    ToolDef(
                        name="test_tool",
                        description="A test tool",
                        parameters={"input": {"type": "string"}},
                        returns={"type": "object"},
                        permission="read",
                    )
                ],
            )
        ]
    )
    return ToolRegistry(config)


def test_list_tools(registry):
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert "inputSchema" in tools[0]


@pytest.mark.asyncio
async def test_call_tool_unknown(registry):
    result = await registry.call_tool("nonexistent", {})
    assert "error" in result


@pytest.mark.asyncio
async def test_call_tool_registered(registry):
    async def handler(args):
        return json.dumps({"result": "ok"})

    registry.register_handler("test_tool", handler)
    result = await registry.call_tool("test_tool", {})
    data = json.loads(result)
    assert data["result"] == "ok"


@pytest.mark.asyncio
async def test_call_tool_handler_exception(registry):
    async def handler(args):
        raise ValueError("handler failed")

    registry.register_handler("test_tool", handler)
    result = await registry.call_tool("test_tool", {})
    assert "error" in result


def test_list_tools_empty_config():
    config = Config(connectors=[])
    reg = ToolRegistry(config)
    assert reg.list_tools() == []
