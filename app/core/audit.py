import json
import time
from typing import Dict, Any, List, Optional
from core.db import get_connection

class AuditLedger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuditLedger, cls).__new__(cls)
        return cls._instance

    def record_event(
        self,
        action: str,
        actor: str,
        role: str,
        details: Dict[str, Any],
        status: str = "SUCCESS",
        trust_impact: Optional[str] = None
    ) -> Dict[str, Any]:
        """Inserts an immutable governance event directly into SQLite."""
        event_id = f"EVT-{int(time.time() * 1000)}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        details_with_trust = dict(details)
        if trust_impact:
            details_with_trust["trust_impact"] = trust_impact

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO audit_events (event_id, timestamp, action, actor, role, status, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, timestamp, action, actor, role, status, json.dumps(details_with_trust)))
            conn.commit()

        return {
            "event_id": event_id,
            "timestamp": timestamp,
            "action": action,
            "actor": actor,
            "role": role,
            "status": status,
            "trust_impact": trust_impact,
            "details": details
        }

    def get_recent(self, limit: int = 25, role_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            if role_filter and role_filter != "Executive":
                cursor.execute("""
                SELECT * FROM audit_events
                WHERE role = ? OR role = 'SYSTEM'
                ORDER BY timestamp DESC LIMIT ?
                """, (role_filter, limit))
            else:
                cursor.execute("""
                SELECT * FROM audit_events
                ORDER BY timestamp DESC LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["details"] = json.loads(item["details_json"])
                except Exception:
                    item["details"] = {}
                item["trust_impact"] = item["details"].get("trust_impact", "NONE")
                result.append(item)
            return result

audit_ledger = AuditLedger()
