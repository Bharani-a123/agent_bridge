"""
AgentBridge Server

Standalone HTTP server that serves the AgentBridge registry,
execute endpoint, and audit endpoints.

This is extracted from bridge.py so it can be used independently
or replaced with a custom server implementation.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bridge import AgentBridge


class AgentBridgeServer:
    """
    Standalone HTTP server for AgentBridge.

    Exposes:
        GET  /agent-registry        — Web MCP compatible action registry
        POST /execute               — Execute an action by name
        GET  /audit/summary         — Audit summary
        GET  /audit/logs            — Detailed audit logs
        GET  /health                — Health check

    Usage:
        server = AgentBridgeServer(bridge, host="0.0.0.0", port=8090)
        server.start()
    """

    def __init__(self, bridge: "AgentBridge", host: str = "0.0.0.0", port: int = 8090):
        self.bridge = bridge
        self.host = host
        self.port = port
        self._server = None

    def start(self, show_banner: bool = True):
        """Start the server — blocks until Ctrl+C."""
        if show_banner:
            self._print_banner()

        bridge_ref = self.bridge

        class Handler(BaseHTTPRequestHandler):

            def do_GET(self):
                if self.path == "/agent-registry":
                    self._json(bridge_ref.get_registry())

                elif self.path == "/health":
                    self._json({
                        "status": "ok",
                        "agentbridge": True,
                        "total_actions": len(bridge_ref.registry.all_actions())
                    })

                elif self.path == "/audit/summary":
                    if bridge_ref.audit:
                        self._json(bridge_ref.audit.get_summary())
                    else:
                        self._json({"error": "Audit logging is disabled"}, 404)

                elif self.path.startswith("/audit/logs"):
                    if bridge_ref.audit:
                        self._json({"logs": bridge_ref.audit.get_logs()})
                    else:
                        self._json({"error": "Audit logging is disabled"}, 404)

                else:
                    self._json({
                        "error": "Endpoint not found",
                        "available_endpoints": [
                            "GET  /agent-registry",
                            "POST /execute",
                            "GET  /audit/summary",
                            "GET  /audit/logs",
                            "GET  /health"
                        ]
                    }, 404)

            def do_POST(self):
                if self.path == "/execute":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)
                    try:
                        payload = json.loads(body)
                        result = bridge_ref.execute(
                            action_name=payload.get("action"),
                            inputs=payload.get("inputs", {}),
                            agent_id=payload.get("agent_id"),
                            policy_name=payload.get("policy")
                        )
                        self._json(result)
                    except json.JSONDecodeError:
                        self._json({"error": "Request body must be valid JSON"}, 400)
                    except Exception as e:
                        self._json({"error": str(e)}, 500)
                else:
                    self._json({"error": "Not found. Use POST /execute"}, 404)

            def do_OPTIONS(self):
                """Support CORS preflight requests."""
                self.send_response(200)
                self._cors_headers()
                self.end_headers()

            def _json(self, data: dict, status: int = 200):
                body = json.dumps(data, indent=2).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._cors_headers()
                self.end_headers()
                self.wfile.write(body)

            def _cors_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

            def log_message(self, format, *args):
                print(f"[AgentBridge] {self.address_string()} {format % args}")

        self._server = HTTPServer((self.host, self.port), Handler)
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            print("\n[AgentBridge] Server stopped.")
            self._server.server_close()

    def stop(self):
        """Stop the server programmatically."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            print("[AgentBridge] Server stopped.")

    def _print_banner(self):
        base = f"http://{self.host}:{self.port}"
        print(f"""
╔══════════════════════════════════════════════════╗
║           AgentBridge Server Running             ║
╠══════════════════════════════════════════════════╣
║  Registry  →  GET  {base}/agent-registry
║  Execute   →  POST {base}/execute
║  Audit     →  GET  {base}/audit/summary
║  Health    →  GET  {base}/health
╠══════════════════════════════════════════════════╣
║  Press Ctrl+C to stop                            ║
╚══════════════════════════════════════════════════╝
""")