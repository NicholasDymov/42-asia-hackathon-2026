import json
from typing import Dict, Any, List
from pathlib import Path

POLICY_FILE = Path(__file__).resolve().parent.parent / "skills" / "policies.json"

DEFAULT_POLICIES = {
    "finance": {
        "emergency_fund_cap_yen": 200000,
        "dual_approval_threshold_yen": 500000,
        "allow_off_hours_autonomous_delegation": True,
        "required_tax_id_format": "^T[0-9]{13}$",
        "budget_variance_tolerance_pct": 10.0
    },
    "sre": {
        "max_auto_remediation_retries": 2,
        "latency_critical_threshold_ms": 2000,
        "cpu_critical_threshold_pct": 90,
        "allowed_failover_regions": ["ap-northeast-1", "ap-northeast-3"],
        "require_backup_before_schema_change": True
    },
    "security": {
        "banned_python_modules": ["subprocess", "os.system", "socket", "ctypes", "pty"],
        "enforce_ast_validation": True,
        "redact_pii_in_logs": True
    }
}

class PolicyEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PolicyEngine, cls).__new__(cls)
            cls._instance.policies = {}
            cls._instance._load()
        return cls._instance

    def _load(self):
        if POLICY_FILE.exists():
            try:
                with open(POLICY_FILE, "r", encoding="utf-8") as f:
                    self.policies = json.load(f)
            except Exception:
                self.policies = DEFAULT_POLICIES
        else:
            self.policies = DEFAULT_POLICIES
            self.save()

    def save(self):
        try:
            with open(POLICY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.policies, f, indent=2)
        except Exception as e:
            print(f"Error saving policies: {e}")

    def get(self, domain: str, key: str, default: Any = None) -> Any:
        return self.policies.get(domain, {}).get(key, default)

    def update(self, domain: str, key: str, value: Any):
        if domain not in self.policies:
            self.policies[domain] = {}
        self.policies[domain][key] = value
        self.save()

policy_engine = PolicyEngine()
