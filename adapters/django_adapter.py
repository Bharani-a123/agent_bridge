class DjangoAdapter:
    """
    Integrates AgentBridge with an existing Django application.

    Usage:
        # In your urls.py
        from agentbridge import AgentBridge
        from agentbridge.adapters import DjangoAdapter

        bridge = AgentBridge(adapter=DjangoAdapter())

        @bridge.action(
            name="get_order_status",
            description="Get order status",
            permissions=["read_only"]
        )
        def get_order_status(order_id: str):
            return {"status": "shipped"}

        # Add to urlpatterns
        urlpatterns = [
            ...
            *bridge.adapter.get_urls(bridge),
        ]
    """

    def __init__(self):
        self._bridge = None

    def mount(self, bridge):
        """Store bridge reference for URL generation."""
        self._bridge = bridge
        print("[AgentBridge] Django adapter initialized")
        print("[AgentBridge] Add bridge.adapter.get_urls(bridge) to your urlpatterns")

    def get_urls(self, bridge):
        """Returns Django URL patterns to add to urlpatterns."""
        try:
            from django.urls import path
            from django.http import JsonResponse
            from django.views.decorators.csrf import csrf_exempt
            from django.views.decorators.http import require_http_methods
            import json
        except ImportError:
            raise ImportError(
                "Django is required for DjangoAdapter. "
                "Install it with: pip install django"
            )

        @require_http_methods(["GET"])
        def agent_registry(request):
            return JsonResponse(bridge.get_registry())

        @require_http_methods(["GET"])
        def health(request):
            return JsonResponse({"status": "ok", "agentbridge": True})

        @csrf_exempt
        @require_http_methods(["POST"])
        def execute(request):
            try:
                payload = json.loads(request.body)
                action_name = payload.get("action")
                inputs = payload.get("inputs", {})
                result = bridge.execute(action_name, inputs)
                return JsonResponse(result)
            except Exception as e:
                return JsonResponse(
                    {"success": False, "error": str(e)},
                    status=400
                )

        return [
            path("agent-registry", agent_registry),
            path("health", health),
            path("execute", execute),
        ]