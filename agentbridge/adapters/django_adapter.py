class DjangoAdapter:
    """Expose AgentBridge endpoints inside a Django project."""

    def __init__(self):
        self._bridge = None

    def mount(self, bridge):
        self._bridge = bridge

    def get_urls(self, bridge=None):
        active_bridge = bridge or self._bridge
        if active_bridge is None:
            raise ValueError("DjangoAdapter is not attached to an AgentBridge instance.")

        try:
            import json
            from django.http import JsonResponse
            from django.urls import path
            from django.views.decorators.csrf import csrf_exempt
            from django.views.decorators.http import require_http_methods
        except ImportError as exc:
            raise ImportError(
                "DjangoAdapter requires Django. Install it with: pip install 'agentbridge[django]'"
            ) from exc

        @require_http_methods(["GET"])
        def agent_registry(_request):
            return JsonResponse(active_bridge.get_registry())

        @require_http_methods(["GET"])
        def health(_request):
            return JsonResponse({"status": "ok", "agentbridge": True})

        @require_http_methods(["GET"])
        def audit_summary(_request):
            if active_bridge.audit:
                return JsonResponse(active_bridge.audit.get_summary())
            return JsonResponse({"error": "Audit logging is disabled"}, status=404)

        @require_http_methods(["GET"])
        def audit_logs(_request):
            if active_bridge.audit:
                return JsonResponse({"logs": active_bridge.audit.get_logs()})
            return JsonResponse({"error": "Audit logging is disabled"}, status=404)

        @csrf_exempt
        @require_http_methods(["POST"])
        def execute(request):
            try:
                payload = json.loads(request.body or b"{}")
                result = active_bridge.execute(
                    action_name=payload.get("action"),
                    inputs=payload.get("inputs", {}),
                    agent_id=payload.get("agent_id"),
                    policy_name=payload.get("policy"),
                )
                return JsonResponse(result)
            except Exception as exc:
                return JsonResponse({"success": False, "error": str(exc)}, status=400)

        return [
            path("agent-registry", agent_registry),
            path("health", health),
            path("audit/summary", audit_summary),
            path("audit/logs", audit_logs),
            path("execute", execute),
        ]
