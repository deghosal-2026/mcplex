"""
MCP transport layer — JSON-RPC over HTTP and SSE.

Handles the ``/mcp`` endpoint on ``POST``.  Auto-detects Streamable HTTP
(SSE) vs plain JSON-RPC by inspecting the ``Accept`` header (case-insensitive).
All tools/call responses go through the handler which returns JSON strings;
errors are returned via the JSON-RPC ``error`` field when appropriate.
"""

import json
import logging

from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse

from mcplex.registry import ToolRegistry

logger = logging.getLogger(__name__)

# MCP protocol version identifier sent in the initialize response.
# Bump when the client/server contract changes.
MCP_PROTOCOL_VERSION = "2025-06-18"


def _json_rpc_response(msg_id, result=None, error=None):
    """Build a JSON-RPC 2.0 response dict."""
    body = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        body["error"] = error
    else:
        body["result"] = result
    return body


async def _handle_tools_list(registry: ToolRegistry, msg_id):
    """Return the list of all registered tools."""
    tools = registry.list_tools()
    logger.info("tools/list → %d tools", len(tools))
    return _json_rpc_response(msg_id, result={"tools": tools})


async def _handle_tools_call(registry: ToolRegistry, body: dict, msg_id):
    """Execute a tool call and return its result."""
    params = body.get("params", {})
    name = params.get("name")
    arguments = params.get("arguments", {})
    logger.info("tools/call: %s args=%s", name, arguments)
    result_str = await registry.call_tool(name, arguments)
    return _json_rpc_response(msg_id, result={
        "content": [{"type": "text", "text": result_str}],
    })


async def _handle_request(body: dict, registry: ToolRegistry):
    """Dispatch a single JSON-RPC request to the appropriate handler."""
    method = body.get("method")
    msg_id = body.get("id")

    if method == "initialize":
        logger.info("Client initialize received")
        return _json_rpc_response(msg_id, result={
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "mcplex", "version": "0.1.0"},
        })

    # initialized is a notification — it has no id, so we return None
    # so the caller can skip sending a response.
    if method == "initialized":
        logger.info("Client initialized notification received")
        return None

    if method == "tools/list":
        return await _handle_tools_list(registry, msg_id)
    if method == "tools/call":
        return await _handle_tools_call(registry, body, msg_id)

    return _json_rpc_response(msg_id, error={
        "code": -32601, "message": f"Method not found: {method}",
    })


async def handle_mcp_message(request: Request, registry: ToolRegistry):
    """Main entry point for ``/mcp`` POST requests.

    Attempts to parse the JSON body and dispatch.  Returns a JSON-RPC
    error response on parse failure.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    response_body = await _handle_request(body, registry)

    # initialized is a notification — no response to send
    if response_body is None:
        return JSONResponse({})

    accept = request.headers.get("accept", "").lower()
    if "text/event-stream" in accept:
        return _sse_response(response_body)
    return JSONResponse(response_body)


def _sse_response(data: dict) -> StreamingResponse:
    """Wrap a single JSON-RPC response in an SSE ``event: message`` frame."""
    payload = f"event: message\ndata: {json.dumps(data)}\n\n"

    async def stream():
        yield payload

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
