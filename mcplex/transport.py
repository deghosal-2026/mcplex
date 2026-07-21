from starlette.requests import Request
from starlette.responses import JSONResponse

from mcplex.registry import ToolRegistry


async def handle_mcp_message(request: Request, registry: ToolRegistry):
    body = await request.json()
    method = body.get("method")
    msg_id = body.get("id")

    if method == "tools/list":
        tools = registry.list_tools()
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": tools},
        })

    if method == "tools/call":
        params = body.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        result = await registry.call_tool(name, arguments)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": result}],
            },
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    })
