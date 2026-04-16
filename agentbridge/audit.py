import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    action_name: str
    inputs: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    agent_id: Optional[str]
    policy_name: Optional[str]
    duration_ms: float
    error: Optional[str] = None


class AuditLogger:
    """Records action executions for monitoring, debugging, and compliance."""

    def __init__(self):
        self._entries: List[AuditEntry] = []

    def log(
        self,
        action_name: str,
        inputs: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
        agent_id: Optional[str] = None,
        policy_name: Optional[str] = None,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            action_name=action_name,
            inputs=inputs,
            result=result,
            success=success,
            agent_id=agent_id,
            policy_name=policy_name,
            duration_ms=duration_ms,
            error=error,
        )
        self._entries.append(entry)
        return asdict(entry)

    def get_logs(
        self,
        action_name: Optional[str] = None,
        success: Optional[bool] = None,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        logs = [asdict(entry) for entry in self._entries]
        if action_name is not None:
            logs = [log for log in logs if log["action_name"] == action_name]
        if success is not None:
            logs = [log for log in logs if log["success"] is success]
        if agent_id is not None:
            logs = [log for log in logs if log["agent_id"] == agent_id]
        return logs

    def get_summary(self) -> Dict[str, Any]:
        total_actions = len(self._entries)
        total_success = sum(1 for entry in self._entries if entry.success)
        total_failure = total_actions - total_success
        success_rate = round((total_success / total_actions) * 100, 2) if total_actions else 0.0

        action_breakdown: Dict[str, int] = {}
        for entry in self._entries:
            action_breakdown[entry.action_name] = action_breakdown.get(entry.action_name, 0) + 1

        avg_duration_ms = (
            round(sum(entry.duration_ms for entry in self._entries) / total_actions, 2)
            if total_actions
            else 0.0
        )

        return {
            "total_actions": total_actions,
            "total_success": total_success,
            "total_failure": total_failure,
            "success_rate": success_rate,
            "average_duration_ms": avg_duration_ms,
            "action_breakdown": action_breakdown,
        }

    def export_json(self, path: str) -> str:
        payload = {
            "summary": self.get_summary(),
            "logs": self.get_logs(),
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return path
