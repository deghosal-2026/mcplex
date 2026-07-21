from pathlib import Path

from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from mcplex.config import load_config
from mcplex.registry import ToolRegistry
from mcplex.transport import handle_mcp_message


def create_app(config_path: str) -> Starlette:
    config = load_config(Path(config_path))
    registry = ToolRegistry(config)

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
