class FastAPIAdapter:
    """Mount AgentBridge routes onto an existing FastAPI application."""

    def __init__(self, app):
        self.app = app

    def mount(self, bridge):
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
        except ImportError as exc:
            raise ImportError(
                "FastAPIAdapter requires FastAPI. Install it with: pip install 'agentbridge[fastapi]'"
            ) from exc

        @self.app.get("/agent-registry")
        async def agent_registry():
            return JSONResponse(content=bridge.get_registry())

        @self.app.get("/health")
        async def health():
            return JSONResponse(content={"status": "ok", "agentbridge": True})

        @self.app.get("/audit/summary")
        async def audit_summary():
            if bridge.audit:
                return JSONResponse(content=bridge.audit.get_summary())
            return JSONResponse(content={"error": "Audit logging is disabled"}, status_code=404)

        @self.app.get("/audit/logs")
        async def audit_logs():
            if bridge.audit:
                return JSONResponse(content={"logs": bridge.audit.get_logs()})
            return JSONResponse(content={"error": "Audit logging is disabled"}, status_code=404)

        @self.app.post("/execute")
        async def execute(request: Request):
            try:
                payload = await request.json()
                result = bridge.execute(
                    action_name=payload.get("action"),
                    inputs=payload.get("inputs", {}),
                    agent_id=payload.get("agent_id"),
                    policy_name=payload.get("policy"),
                )
                return JSONResponse(content=result)
            except Exception as exc:
                return JSONResponse(content={"success": False, "error": str(exc)}, status_code=400)
