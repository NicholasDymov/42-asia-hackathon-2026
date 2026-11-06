import time
from typing import Dict, Any, List

class SystemTelemetry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemTelemetry, cls).__new__(cls)
            cls._instance._init_history()
        return cls._instance

    def _init_history(self):
        # 10 data points showing an escalating incident
        self.history: List[Dict[str, Any]] = [
            {"time": "02:05", "latency_ms": 32, "cpu_pct": 28, "connections": 75, "status": "HEALTHY"},
            {"time": "02:07", "latency_ms": 48, "cpu_pct": 34, "connections": 110, "status": "HEALTHY"},
            {"time": "02:09", "latency_ms": 120, "cpu_pct": 52, "connections": 240, "status": "NORMAL"},
            {"time": "02:11", "latency_ms": 850, "cpu_pct": 78, "connections": 395, "status": "WARNING"},
            {"time": "02:12", "latency_ms": 2400, "cpu_pct": 92, "connections": 470, "status": "CRITICAL"},
            {"time": "02:13", "latency_ms": 3800, "cpu_pct": 96, "connections": 490, "status": "CRITICAL"},
            {"time": "02:14", "latency_ms": 4200, "cpu_pct": 98, "connections": 498, "status": "P0_OUTAGE"},
        ]

    def record_remediation(self):
        """Appends recovered state post-agent action."""
        self.history.append({"time": "02:15", "latency_ms": 420, "cpu_pct": 45, "connections": 150, "status": "RECOVERING"})
        self.history.append({"time": "02:16", "latency_ms": 18, "cpu_pct": 24, "connections": 42, "status": "HEALTHY"})

    def get_latest(self) -> Dict[str, Any]:
        return self.history[-1]

    def get_series(self) -> List[Dict[str, Any]]:
        return self.history

telemetry = SystemTelemetry()
