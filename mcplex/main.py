import argparse
import uvicorn

from mcplex.server import create_app


def cli():
    parser = argparse.ArgumentParser(prog="mcplex")
    parser.add_argument("serve", help="Start the MCPlex server")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    args = parser.parse_args()

    if args.serve != "serve":
        parser.print_help()
        return

    app = create_app(args.config)
    print(f"MCPlex starting on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
