import json
import time
from typing import Any, Callable, Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from .action import action as action_decorator, ActionDefinition
from .registry import Registry
from .permissions import PermissionManager, PermissionPolicy, PermissionLevel
from .audit import AuditLogger


class AgentBridge:
    """
    The main AgentBridge class.

    Wraps your existing Python system and exposes a structured,
    Web MCP compatible Action Registry that any AI agent can read
    and interact with.

    Usage:
        bridge = AgentBridge(
            system_name="My E-Commerce System",
            system_description="Order management and customer service"
        )

        @bridge.action(
            name="get_order_status",
            description="Get the current status of a customer order",
            permissions=["read_only"]
        )
        def get_order_status(order_id: str):
            return {"status": "shipped"}

        bridge.serve()
    """

    def __init__(
        self,
        system_name: str = "AgentBridge System",
        system_description: str = "",
        version: str = "1.0.0",
        host: str = "0.0.0.0",
        port: int = 8090,
        adapter=None,
        enable_audit: bool = True
    ):
        self.host = host
        self.port = port
        self.adapter = adapter
        self.registry = Registry(
            system_name=system_name,
            system_description=system_description,
            version=version
        )
        self.permissions = PermissionManager()
        self.audit = AuditLogger() if enable_audit else None
        self._registered_funcs: Dict[str, Callable] = {}

        # Mount adapter if provided
        if adapter:
            adapter.mount(self)

    def action(
        self,
        name: str,
        description: str,
        permissions: Optional[List[str]] = None,
        schema: Optional[Any] = None,
        outputs: Optional[Dict] = None,
        examples: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Decorator to register a function as an agent-accessible action.

        Example:
            @bridge.action(
                name="get_order_status",
                description="Get order status by ID",
                permissions=["read_only"]
            )
            def get_order_status(order_id: str):
                return {"status": "shipped"}
        """
        decorator = action_decorator(
            name=name,
            description=description,
            permissions=permissions,
            schema=schema,
            outputs=outputs,
            examples=examples,
            tags=tags
        )

        def wrapper(func: Callable) -> Callable:
            decorated = decorator(func)
            self.registry.register(decorated._agentbridge_action)
            self._registered_funcs[name] = decorated
            return decorated

        return wrapper

    def execute(
        self,
        action_name: str,
        inputs: Dict[str, Any],
        agent_id: Optional[str] = None,
        policy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a registered action by name with given inputs.
        Applies permission checks and records audit log.
        """
        start_time = time.time()

        if action_name not in self._registered_funcs:
            result = {
                "success": False,
                "error": f"Action '{action_name}' not found in registry",
                "available_actions": list(self._registered_funcs.keys())
            }
            self._audit(action_name, inputs, result, False, agent_id, policy_name, start_time)
            return result

        action_def = self.registry.get_action(action_name)

        permission_check = self.permissions.check(
            action_name=action_name,
            action_permissions=action_def.permissions,
            policy_name=policy_name
        )

        if not permission_check["allowed"]:
            if permission_check.get("requires_approval"):
                result = {
                    "success": False,
                    "requires_approval": True,
                    "message": f"Action '{action_name}' requires human approval before execution",
                    "pending_inputs": inputs
                }
            else:
                result = {
                    "success": False,
                    "error": permission_check["reason"]
                }
            self._audit(action_name, inputs, result, False, agent_id, policy_name, start_time)
            return result

        try:
            func = self._registered_funcs[action_name]
            output = func(**inputs)
            result = {
                "success": True,
                "action": action_name,
                "result": output
            }
            self._audit(action_name, inputs, result, True, agent_id, policy_name, start_time)
            return result

        except TypeError as e:
            result = {
                "success": False,
                "error": f"Invalid inputs for action '{action_name}': {str(e)}"
            }
            self._audit(action_name, inputs, result, False, agent_id, policy_name, start_time, str(e))
            return result

        except Exception as e:
            result = {
                "success": False,
                "error": f"Action '{action_name}' failed: {str(e)}"
            }
            self._audit(action_name, inputs, result, False, agent_id, policy_name, start_time, str(e))
            return result

    def _audit(self, action_name, inputs, result, success, agent_id, policy_name, start_time, error=None):
        if self.audit:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self.audit.log(
                action_name=action_name,
                inputs=inputs,
                result=result,
                success=success,
                agent_id=agent_id,
                policy_name=policy_name,
                duration_ms=duration_ms,
                error=error
            )

    def get_registry(self) -> Dict[str, Any]:
        return self.registry.to_dict()

    def serve(self, show_summary: bool = True):
        """
        Start the AgentBridge server.
        Exposes /agent-registry, /execute, /audit, and /health endpoints.
        """
        if self.adapter:
            print("[AgentBridge] Running via framework adapter — use your framework's server to start.")
            return

        if show_summary:
            print(self.registry.summary())

        bridge_ref = self

        class AgentBridgeHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                if self.path == "/agent-registry":
                    self._send_json(bridge_ref.get_registry())
                elif self.path == "/health":
                    self._send_json({"status": "ok", "agentbridge": True})
                elif self.path == "/audit/summary":
                    if bridge_ref.audit:
                        self._send_json(bridge_ref.audit.get_summary())
                    else:
                        self._send_json({"error": "Audit logging is disabled"}, 404)
                elif self.path.startswith("/audit/logs"):
                    if bridge_ref.audit:
                        self._send_json({"logs": bridge_ref.audit.get_logs()})
                    else:
                        self._send_json({"error": "Audit logging is disabled"}, 404)
                else:
                    self._send_json({
                        "error": "Not found",
                        "available_endpoints": [
                            "GET /agent-registry",
                            "GET /health",
                            "GET /audit/summary",
                            "GET /audit/logs",
                            "POST /execute"
                        ]
                    }, status=404)

            def do_POST(self):
                if self.path == "/execute":
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length)
                    try:
                        payload = json.loads(body)
                        action_name = payload.get("action")
                        inputs = payload.get("inputs", {})
                        agent_id = payload.get("agent_id")
                        policy_name = payload.get("policy")
                        result = bridge_ref.execute(action_name, inputs, agent_id, policy_name)
                        self._send_json(result)
                    except json.JSONDecodeError:
                        self._send_json({"error": "Invalid JSON body"}, status=400)
                else:
                    self._send_json({"error": "Not found. Try POST /execute"}, status=404)

            def _send_json(self, data: Dict, status: int = 200):
                body = json.dumps(data, indent=2).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                print(f"[AgentBridge] {self.address_string()} - {format % args}")

        print(f"[AgentBridge] Server running at http://{self.host}:{self.port}")
        print(f"[AgentBridge] Registry   → GET  http://{self.host}:{self.port}/agent-registry")
        print(f"[AgentBridge] Execute    → POST http://{self.host}:{self.port}/execute")
        print(f"[AgentBridge] Audit      → GET  http://{self.host}:{self.port}/audit/summary")
        print(f"[AgentBridge] Health     → GET  http://{self.host}:{self.port}/health")
        print(f"[AgentBridge] Press Ctrl+C to stop\n")

        server = HTTPServer((self.host, self.port), AgentBridgeHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[AgentBridge] Server stopped.")
            server.server_close()
