from typing import Any, Dict


class FastAPIAdapter:
    """
    Integrates AgentBridge with an existing FastAPI application.

    Usage:
        from fastapi import FastAPI
        from agentbridge import AgentBridge
        from agentbridge.adapters import FastAPIAdapter

        app = FastAPI()
        bridge = AgentBridge(adapter=FastAPIAdapter(app))

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
        """Mount AgentBridge routes onto the FastAPI app."""
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
        except ImportError:
            raise ImportError(
                "FastAPI is required for FastAPIAdapter. "
                "Install it with: pip install fastapi"
            )

        @self.app.get("/agent-registry")
        async def agent_registry():
            return JSONResponse(content=bridge.get_registry())

        @self.app.get("/health")
        async def health():
            return JSONResponse(content={"status": "ok", "agentbridge": True})

        @self.app.post("/execute")
        async def execute(request: Request):
            try:
                payload = await request.json()
                action_name = payload.get("action")
                inputs = payload.get("inputs", {})
                result = bridge.execute(action_name, inputs)
                return JSONResponse(content=result)
            except Exception as e:
                return JSONResponse(
                    content={"success": False, "error": str(e)},
                    status_code=400
                )

        print("[AgentBridge] Mounted on FastAPI app")
        print("[AgentBridge] Routes: GET /agent-registry, POST /execute, GET /health")