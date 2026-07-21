from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from mcplex.config import load_config
from mcplex.connectors import register_all
from mcplex.registry import ToolRegistry
from mcplex.transport import handle_mcp_message


def create_app(config_or_path) -> Starlette:
    if isinstance(config_or_path, str):
        config = load_config(Path(config_or_path))
    else:
        config = config_or_path

    registry = ToolRegistry(config)
    register_all(registry)

    async def mcp_endpoint(request):
        return await handle_mcp_message(request, registry)

    routes = [
        Route("/mcp", endpoint=mcp_endpoint, methods=["POST"]),
        Route("/health", endpoint=lambda r: PlainTextResponse("ok")),
    ]

    return Starlette(
        debug=False,
        routes=routes,
    )
