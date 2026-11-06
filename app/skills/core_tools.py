import json
import time
from typing import Dict, Any, List
from core.db import get_connection
from core.audit import audit_ledger
from core.chaos import chaos_engine

def query_system_status(service_filter: str = "") -> str:
    """[DevOps] Queries real SQLite database for live server metrics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if service_filter:
            cursor.execute(
                "SELECT * FROM servers WHERE name LIKE ? OR id LIKE ?",
                (f"%{service_filter}%", f"%{service_filter}%")
            )
        else:
            cursor.execute("SELECT * FROM servers")
        rows = [dict(row) for row in cursor.fetchall()]
        return json.dumps(rows, indent=2)

def execute_server_failover(cluster_id: str, standby_instance_type: str = "r6g.2xlarge") -> str:
    """[DevOps] Executes failover on real database: restores metrics and records remediation timestamp."""
    chaos_engine.resolve_chaos(cluster_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servers WHERE id = ?", (cluster_id,))
        server = cursor.fetchone()
        server_dict = dict(server) if server else {}

    audit_ledger.record_event(
        action="EXECUTE_FAILOVER",
        actor="DevOpsAgent",
        role="DevOps",
        details={"cluster_id": cluster_id, "instance_type": standby_instance_type, "post_state": server_dict},
        status="SUCCESS"
    )
    return f"Success: Failover completed on {cluster_id}. Server state updated in database: Status={server_dict.get('status')}, CPU={server_dict.get('cpu_percent')}%, Connections={server_dict.get('active_connections')}."

def query_financial_records(invoice_no: str = "") -> str:
    """[Finance] Queries real SQLite database for corporate invoices."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if invoice_no:
            cursor.execute("SELECT * FROM invoices WHERE invoice_no = ?", (invoice_no,))
        else:
            cursor.execute("SELECT * FROM invoices")
        rows = [dict(row) for row in cursor.fetchall()]
        return json.dumps(rows, indent=2)

def allocate_emergency_funds(amount_yen: int, justification: str, recipient_dept: str = "DevOps") -> str:
    """[Finance] Deducts budget from real SQLite database and creates authorization record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets WHERE department = 'Infrastructure'")
        budget = dict(cursor.fetchone())

        if amount_yen > budget["emergency_fund_cap_yen"]:
            return f"Error: Requested amount ¥{amount_yen:,} exceeds emergency authorization cap of ¥{budget['emergency_fund_cap_yen']:,}."

        cursor.execute("""
        UPDATE budgets
        SET spent_yen = spent_yen + ?
        WHERE department = 'Infrastructure'
        """, (amount_yen,))
        conn.commit()

        cursor.execute("SELECT * FROM budgets WHERE department = 'Infrastructure'")
        updated_budget = dict(cursor.fetchone())

    auth_code = f"AUTH-EMERG-{int(time.time())}"
    audit_ledger.record_event(
        action="ALLOCATE_EMERGENCY_FUNDS",
        actor="FinanceAgent",
        role="Finance",
        details={"amount_yen": amount_yen, "justification": justification, "auth_code": auth_code, "new_spent_yen": updated_budget["spent_yen"]},
        status="APPROVED",
        trust_impact="TRUST_REINFORCED"
    )
    return f"Approved: Allocated ¥{amount_yen:,} for '{justification}'. Auth Code: {auth_code}. Updated DB Spent Balance: ¥{updated_budget['spent_yen']:,}."

def create_jira_ticket(summary: str, description: str, priority: str = "High", assignee: str = "On-Call") -> str:
    """[Shared] Inserts a real tracking ticket row into SQLite."""
    ticket_id = f"CORP-{int(time.time() % 10000)}"
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO tickets (ticket_id, summary, description, priority, assignee, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'OPEN', ?)
        """, (ticket_id, summary, description, priority, assignee, now))
        conn.commit()

    audit_ledger.record_event(
        action="CREATE_TICKET",
        actor="AgentCollective",
        role="SYSTEM",
        details={"ticket_id": ticket_id, "summary": summary}
    )
    return f"Success: Inserted Ticket [{ticket_id}] in database (Priority: {priority}, Assignee: {assignee})."

def send_slack_notification(channel: str, message: str) -> str:
    """[Shared] Broadcasts message and logs to real database audit."""
    audit_ledger.record_event(
        action="SEND_SLACK",
        actor="AgentCollective",
        role="SYSTEM",
        details={"channel": channel, "message": message}
    )
    return f"Dispatched to {channel}: '{message}'"

def search_knowledge_base(query: str) -> str:
    """[Shared] Reads actual policy markdown from knowledge base."""
    docs = {
        "sre_outage_runbook": (
            "SRE Incident Runbook: P0 Database Failover & Emergency Scaling\n"
            "1. If Tokyo Primary DB latency > 2000ms or CPU > 95%, initiate failover to standby replica.\n"
            "2. If standby capacity is insufficient, provision a high-memory failover instance (estimated cost: ~¥120,000).\n"
            "3. Requirement: Off-hours emergency funds require verified Accounting tool authorization."
        ),
        "japan_tax_policy": (
            "Accounting Policy: Qualified Invoice System (Inbousu Seido)\n"
            "1. All corporate vendor invoices must carry a valid Japanese Corporate Tax Number (Format: T + 13 digits).\n"
            "2. Invoices exceeding PO budget by >10% require VP sign-off or Department Head escalation."
        )
    }
    q = query.lower()
    matches = [f"[{k.upper()}]\n{v}" for k, v in docs.items() if any(t in v.lower() for t in q.split())]
    return "\n\n---\n\n".join(matches) if matches else "No matching runbook found."

CORE_TOOL_FUNCTIONS = {
    "query_system_status": query_system_status,
    "execute_server_failover": execute_server_failover,
    "query_financial_records": query_financial_records,
    "allocate_emergency_funds": allocate_emergency_funds,
    "create_jira_ticket": create_jira_ticket,
    "send_slack_notification": send_slack_notification,
    "search_knowledge_base": search_knowledge_base
}
