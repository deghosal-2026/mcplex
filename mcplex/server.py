"""
MCPlex HTTP server — Starlette application factory.

Creates the ASGI app with two routes:

  * ``/mcp`` — the MCP JSON-RPC endpoint (POST only)
  * ``/health`` — returns "ok" for health checks
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from mcplex.config import Config, load_config
from mcplex.connectors import register_all
from mcplex.registry import ToolRegistry
from mcplex.transport import handle_mcp_message

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: Starlette):
    logger.info("MCPlex starting up")
    yield
    logger.info("MCPlex shutting down — connections closed")


def create_app(config: Config) -> Starlette:
    """Build a fully-wired Starlette app from a parsed Config.

    Loads tool definitions into the registry, registers connector
    handlers, and wires the HTTP routes.
    """
    registry = ToolRegistry(config)
    register_all(registry, config)
    registry.check_orphans()

    async def mcp_endpoint(request):
        return await handle_mcp_message(request, registry)

    async def health_endpoint(request):
        return PlainTextResponse("ok")

    routes = [
        Route("/mcp", endpoint=mcp_endpoint, methods=["POST"]),
        Route("/health", endpoint=health_endpoint),
    ]

    app = Starlette(debug=False, routes=routes, lifespan=lifespan)
    app.state.registry = registry
    logger.info("MCPlex ready: %d tools registered", len(registry.list_tools()))
    return app


def create_app_from_path(config_path: str) -> Starlette:
    """Convenience — load config from a file path then build the app."""
    path = Path(config_path)
    config = load_config(path)
    return create_app(config)
