class FlaskAdapter:
    """Mount AgentBridge routes onto an existing Flask application."""

    def __init__(self, app):
        self.app = app

    def mount(self, bridge):
        try:
            from flask import jsonify, request
        except ImportError as exc:
            raise ImportError(
                "FlaskAdapter requires Flask. Install it with: pip install 'agentbridge[flask]'"
            ) from exc

        @self.app.route("/agent-registry", methods=["GET"])
        def agent_registry():
            return jsonify(bridge.get_registry())

        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "agentbridge": True})

        @self.app.route("/audit/summary", methods=["GET"])
        def audit_summary():
            if bridge.audit:
                return jsonify(bridge.audit.get_summary())
            return jsonify({"error": "Audit logging is disabled"}), 404

        @self.app.route("/audit/logs", methods=["GET"])
        def audit_logs():
            if bridge.audit:
                return jsonify({"logs": bridge.audit.get_logs()})
            return jsonify({"error": "Audit logging is disabled"}), 404

        @self.app.route("/execute", methods=["POST"])
        def execute():
            try:
                payload = request.get_json(silent=True) or {}
                result = bridge.execute(
                    action_name=payload.get("action"),
                    inputs=payload.get("inputs", {}),
                    agent_id=payload.get("agent_id"),
                    policy_name=payload.get("policy"),
                )
                return jsonify(result)
            except Exception as exc:
                return jsonify({"success": False, "error": str(exc)}), 400
