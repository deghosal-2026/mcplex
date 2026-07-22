"""
Unit tests for the ToolRegistry.

Covers listing, calling, unknown handlers, and exception handling.
"""

import json

import pytest

from mcplex.config import Config, ConnectorType, ToolDef, ConnectorDef
from mcplex.registry import ToolRegistry


@pytest.fixture
def registry():
    """A registry with a single HTTP tool (no handler)."""
    config = Config(
        connectors=[
            ConnectorDef(
                name="test",
                type=ConnectorType.http,
                base_url="http://localhost:8000",
                tools=[
                    ToolDef(
                        name="test_tool",
                        description="A test tool",
                        parameters={"input": {"type": "string"}},
                        returns={"type": "object"},
                    )
                ],
            )
        ]
    )
    return ToolRegistry(config)


def test_list_tools(registry):
    """list_tools returns metadata for every tool in config."""
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert "inputSchema" in tools[0]


@pytest.mark.asyncio
async def test_call_tool_unknown(registry):
    """Calling a tool with no handler returns a JSON error with is_error=True."""
    result, is_error = await registry.call_tool("nonexistent", {})
    data = json.loads(result)
    assert "error" in data
    assert is_error is True


@pytest.mark.asyncio
async def test_call_tool_registered(registry):
    """A registered handler is invoked with the provided arguments."""
    async def handler(args):
        return json.dumps({"result": "ok"})

    registry.register_handler("test_tool", handler)
    result, is_error = await registry.call_tool("test_tool", {})
    data = json.loads(result)
    assert data["result"] == "ok"
    assert is_error is False


@pytest.mark.asyncio
async def test_call_tool_handler_exception(registry):
    """An exception in a handler is caught and returned as a JSON error."""
    async def handler(args):
        raise ValueError("handler failed")

    registry.register_handler("test_tool", handler)
    result, is_error = await registry.call_tool("test_tool", {})
    data = json.loads(result)
    assert "error" in data
    assert is_error is True


def test_list_tools_empty_config():
    """An empty config produces an empty tool list."""
    config = Config(connectors=[])
    reg = ToolRegistry(config)
    assert reg.list_tools() == []


def test_registry_check_orphans_no_warning(registry, caplog):
    """check_orphans logs a warning for tools without handlers."""
    import logging

    async def _ok_handler(args):
        return json.dumps({"ok": True})

    registry.register_handler("test_tool", _ok_handler)
    with caplog.at_level(logging.WARNING):
        registry.check_orphans()
    assert "has no handler" not in caplog.text


def test_registry_check_orphans_with_orphan(registry, caplog):
    """A tool with no handler triggers a warning."""
    import logging
    with caplog.at_level(logging.WARNING):
        registry.check_orphans()
    assert "has no handler" in caplog.text


@pytest.mark.asyncio
async def test_handler_collision_last_wins(registry):
    """Registering two handlers for the same tool uses the last one."""
    async def first(args):
        return json.dumps({"from": "first"})
    async def second(args):
        return json.dumps({"from": "second"})
    registry.register_handler("test_tool", first)
    registry.register_handler("test_tool", second)
    result, is_error = await registry.call_tool("test_tool", {})
    data = json.loads(result)
    assert data["from"] == "second"
    assert is_error is False


def test_has_handler_true(registry):
    """has_handler returns True for a registered handler."""
    registry.register_handler("test_tool", lambda args: "")
    assert registry.has_handler("test_tool") is True


def test_has_handler_false(registry):
    """has_handler returns False for an unregistered tool name."""
    assert registry.has_handler("nonexistent") is False


@pytest.mark.asyncio
async def test_call_tool_handler_returns_error_json(registry):
    """A handler returning {"error": ...} JSON sets is_error=True."""
    async def handler(args):
        return json.dumps({"error": "backend failed"})

    registry.register_handler("test_tool", handler)
    result, is_error = await registry.call_tool("test_tool", {})
    data = json.loads(result)
    assert data["error"] == "backend failed"
    assert is_error is True
