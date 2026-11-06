from typing import Dict, Any, Tuple
from agents.base import BaseAgent
from core.audit import audit_ledger
from core.policies import policy_engine

SENTINEL_PROMPT = """You are the Sentinel Enterprise Policy & Security Guard.
Your role is to strictly validate all proposed agent actions against company policy thresholds.
"""

class SentinelAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SentinelGuard",
            role="Security",
            default_model="mistral-large-latest",
            system_prompt=SENTINEL_PROMPT
        )

    def evaluate_action(self, tool_name: str, arguments: Dict[str, Any], caller_role: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates tool execution parameters against enterprise policies.
        Returns: (is_approved, explanation, policy_evidence)
        """
        if tool_name == "allocate_emergency_funds":
            amount = arguments.get("amount_yen", 0)
            max_cap = policy_engine.get("finance", "emergency_fund_cap_yen", 200000)
            allow_off_hours = policy_engine.get("finance", "allow_off_hours_autonomous_delegation", True)

            if not allow_off_hours:
                return False, "Sentinel Violation: Off-hours autonomous delegation is disabled in Policy Engine.", {"policy_clause": "FIN-01.B", "threshold": "DISABLED"}

            if amount > max_cap:
                audit_ledger.record_event(
                    action="POLICY_VIOLATION_BLOCKED",
                    actor=self.name,
                    role="Security",
                    details={"tool": tool_name, "requested": amount, "cap": max_cap},
                    status="BLOCKED"
                )
                return False, f"Sentinel Violation: Emergency spend ¥{amount:,} exceeds authorized Policy Cap of ¥{max_cap:,}.", {"policy_clause": "FIN-04.A", "cap_yen": max_cap}

            evidence = {"policy_clause": "FIN-04.A (Emergency SRE Spend)", "cap_yen": max_cap, "verdict": "COMPLIANT"}
            audit_ledger.record_event(
                action="SENTINEL_APPROVED",
                actor=self.name,
                role="Security",
                details={"tool": tool_name, "evidence": evidence},
                status="PASSED"
            )
            return True, f"Policy Check Passed: Spend ¥{amount:,} compliant with Clause FIN-04.A (Cap: ¥{max_cap:,}).", evidence

        if tool_name == "execute_server_failover":
            cluster = arguments.get("cluster_id", "")
            if not cluster.startswith("srv-"):
                return False, f"Security Violation: Target cluster '{cluster}' is not a recognized infrastructure asset.", {"clause": "SEC-08"}

            evidence = {"policy_clause": "SRE-02.C (Automatic Standby Promotion)", "target": cluster, "verdict": "AUTHORIZED"}
            audit_ledger.record_event(
                action="SENTINEL_APPROVED",
                actor=self.name,
                role="Security",
                details={"tool": tool_name, "evidence": evidence},
                status="PASSED"
            )
            return True, f"Authorized by SRE Policy SRE-02.C for cluster {cluster}.", evidence

        # Default pass
        return True, "Standard operational policy clearance.", {"clause": "GEN-OPS"}
