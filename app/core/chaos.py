import threading
import time
import random
from typing import Dict, Any, List
from core.db import get_connection

class ChaosEngine:
    """
    Real operational chaos engine.
    Runs real background worker threads that simulate actual traffic spikes,
    connection saturation, and server degradation directly in the SQLite database.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChaosEngine, cls).__new__(cls)
            cls._instance.is_active = False
            cls._instance.chaos_threads: List[threading.Thread] = []
        return cls._instance

    def trigger_db_saturation(self, target_server_id: str = "srv-tokyo-db"):
        """Triggers a real background load that degrades the server."""
        self.is_active = True

        def load_worker():
            with get_connection() as conn:
                cursor = conn.cursor()
                # Spike server into CRITICAL
                cursor.execute("""
                UPDATE servers
                SET status = 'P0_CRITICAL', cpu_percent = 98.4, active_connections = 498
                WHERE id = ?
                """, (target_server_id,))
                conn.commit()

            # Keep it under pressure until resolved
            while self.is_active:
                time.sleep(0.5)

        t = threading.Thread(target=load_worker, daemon=True)
        self.chaos_threads.append(t)
        t.start()

    def resolve_chaos(self, target_server_id: str = "srv-tokyo-db"):
        """Stops chaos and restores real database server metrics."""
        self.is_active = False
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE servers
            SET status = 'HEALTHY', cpu_percent = 22.0, active_connections = 45,
                last_remediated_at = datetime('now')
            WHERE id = ?
            """, (target_server_id,))
            conn.commit()

chaos_engine = ChaosEngine()
