from mcplex.config import Config, ToolDef


class ToolRegistry:
    def __init__(self, config: Config):
        self._tools: dict[str, ToolDef] = {}
        self._handlers: dict[str, callable] = {}
        for connector in config.connectors:
            for tool in connector.tools:
                self._tools[tool.name] = tool

    def register_handler(self, tool_name: str, handler: callable):
        self._handlers[tool_name] = handler

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": {
                    "type": "object",
                    "properties": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    async def call_tool(self, name: str, arguments: dict) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return f'{{"error": "tool {name} not found"}}'
        try:
            return await handler(arguments)
        except Exception as e:
            return f'{{"error": "{e}"}}'
