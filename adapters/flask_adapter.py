class FlaskAdapter:
    """
    Integrates AgentBridge with an existing Flask application.

    Usage:
        from flask import Flask
        from agentbridge import AgentBridge
        from agentbridge.adapters import FlaskAdapter

        app = Flask(__name__)
        bridge = AgentBridge(adapter=FlaskAdapter(app))

        @bridge.action(
            name="get_order_status",
            description="Get order status",
            permissions=["read_only"]
        )
        def get_order_status(order_id: str):
            return {"status": "shipped"}
    """

    def __init__(self, app):
        self.app = app

    def mount(self, bridge):
        """Mount AgentBridge routes onto the Flask app."""
        try:
            from flask import jsonify, request
        except ImportError:
            raise ImportError(
                "Flask is required for FlaskAdapter. "
                "Install it with: pip install flask"
            )

        @self.app.route("/agent-registry", methods=["GET"])
        def agent_registry():
            return jsonify(bridge.get_registry())

        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "agentbridge": True})

        @self.app.route("/execute", methods=["POST"])
        def execute():
            try:
                payload = request.get_json()
                action_name = payload.get("action")
                inputs = payload.get("inputs", {})
                result = bridge.execute(action_name, inputs)
                return jsonify(result)
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400

        print("[AgentBridge] Mounted on Flask app")
        print("[AgentBridge] Routes: GET /agent-registry, POST /execute, GET /health")