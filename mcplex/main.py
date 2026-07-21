import argparse
import uvicorn

from mcplex.server import create_app


def cli():
    parser = argparse.ArgumentParser(prog="mcplex")
    sub = parser.add_subparsers(dest="command", required=True)

    serve_parser = sub.add_parser("serve", help="Start the MCPlex server")
    serve_parser.add_argument("--config", default="config.yaml", help="Path to config file")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port")

    args = parser.parse_args()

    app = create_app(args.config)
    print(f"MCPlex starting on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
