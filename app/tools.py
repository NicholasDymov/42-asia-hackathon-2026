import json
from typing import Dict, Any, List

# In-memory mock database representing corporate systems
MOCK_DATABASE = {
    "servers": [
        {"id": "srv-prod-01", "name": "Payment Gateway API", "status": "DEGRADED", "cpu": "94%", "memory": "88%", "region": "ap-northeast-1 (Tokyo)"},
        {"id": "srv-prod-02", "name": "User Auth Service", "status": "HEALTHY", "cpu": "22%", "memory": "40%", "region": "ap-northeast-1 (Tokyo)"},
        {"id": "srv-prod-03", "name": "Postgres Primary DB", "status": "WARNING", "cpu": "91%", "connections": 498, "max_conn": 500}
    ],
    "invoices": [
        {"invoice_no": "INV-2026-882", "vendor": "CloudHost Global", "amount": 14200.00, "po_number": "PO-9031", "approved_budget": 10000.00, "status": "PENDING_REVIEW"},
        {"invoice_no": "INV-2026-883", "vendor": "Tokyo Office Supplies", "amount": 650.00, "po_number": "PO-9032", "approved_budget": 700.00, "status": "APPROVED"}
    ],
    "employees": [
        {"id": "EMP-1042", "name": "Kenji Sato", "role": "Senior Backend Engineer", "team": "Infrastructure", "start_date": "2026-11-15", "provisioned": False}
    ]
}

# In-memory knowledge base (runbooks & policies)
MOCK_KNOWLEDGE_BASE = {
    "postgres_cpu_spike": (
        "Runbook: Postgres Primary High CPU & Connection Saturation\n"
        "1. Check connection count. If >480/500, idle transactions from batch workers are typically blocking the pool.\n"
        "2. Action: Terminate idle client connections using connection pool reset.\n"
        "3. Notify #infra-alerts on Slack.\n"
        "4. Create a HIGH priority incident ticket in Jira assigned to On-Call DevOps."
    ),
    "procurement_policy": (
        "Policy: Vendor Invoicing and Discrepancies\n"
        "1. Invoices exceeding the approved PO budget by more than 10% require VP approval.\n"
        "2. For amounts exceeding $10,000, post an alert in #finance-approvals with the variance amount.\n"
        "3. Flag the invoice in the accounting database as 'REQUIRES_EXECUTIVE_SIGN_OFF'."
    ),
    "onboarding_sop": (
        "SOP: New Joiner Technical Provisioning\n"
        "1. Create corporate Google Workspace email and GitHub team access.\n"
        "2. Schedule a 30-minute Welcome 1-on-1 on day 1 with the engineering lead.\n"
        "3. Post an introduction banner to #general Slack channel."
    )
}

# Audit trail of actions performed
AUDIT_LOGS: List[Dict[str, Any]] = []

def search_knowledge_base(query: str) -> str:
    """Searches corporate runbooks, SOPs, and internal documentation."""
    q = query.lower()
    results = []
    for key, doc in MOCK_KNOWLEDGE_BASE.items():
        if any(term in doc.lower() for term in q.split()):
            results.append(f"[{key.upper()}]\n{doc}")
    if not results:
        return "No exact runbook found. Consult standard operating guidelines."
    return "\n\n---\n\n".join(results)

def query_system_status(service_filter: str = "") -> str:
    """Queries corporate server infrastructure status, database health, and metrics."""
    servers = MOCK_DATABASE["servers"]
    if service_filter:
        filtered = [s for s in servers if service_filter.lower() in s["name"].lower() or service_filter.lower() in s["id"].lower()]
        return json.dumps(filtered, indent=2)
    return json.dumps(servers, indent=2)

def query_financial_records(invoice_no: str = "") -> str:
    """Retrieves corporate invoice and purchase order records."""
    invoices = MOCK_DATABASE["invoices"]
    if invoice_no:
        filtered = [inv for inv in invoices if inv["invoice_no"].lower() == invoice_no.lower()]
        return json.dumps(filtered, indent=2)
    return json.dumps(invoices, indent=2)

def create_jira_ticket(summary: str, description: str, priority: str = "Medium", assignee: str = "DevOps On-Call") -> str:
    """Creates a tracking ticket in Jira / corporate ticketing system."""
    ticket_id = f"CORP-{len(AUDIT_LOGS) + 101}"
    record = {
        "action": "CREATE_JIRA_TICKET",
        "ticket_id": ticket_id,
        "summary": summary,
        "description": description,
        "priority": priority,
        "assignee": assignee,
        "status": "OPEN"
    }
    AUDIT_LOGS.append(record)
    return f"Success: Created Jira Ticket [{ticket_id}] with priority '{priority}' assigned to '{assignee}'."

def send_slack_notification(channel: str, message: str) -> str:
    """Dispatches a notification to a corporate Slack or Teams channel."""
    record = {
        "action": "SEND_SLACK_NOTIFICATION",
        "channel": channel,
        "message": message
    }
    AUDIT_LOGS.append(record)
    return f"Success: Broadcast message to {channel}: '{message}'"

def execute_server_remediation(server_id: str, remediation_command: str) -> str:
    """CRITICAL: Executes an infrastructure remediation or connection pool flush on production."""
    record = {
        "action": "EXECUTE_REMEDIATION",
        "server_id": server_id,
        "command": remediation_command,
        "status": "EXECUTED"
    }
    # Update mock database state
    for s in MOCK_DATABASE["servers"]:
        if s["id"] == server_id:
            s["status"] = "HEALTHY"
            s["cpu"] = "28%"
            if "connections" in s:
                s["connections"] = 65
    AUDIT_LOGS.append(record)
    return f"Success: Executed '{remediation_command}' on {server_id}. Server status restored to HEALTHY (CPU: 28%)."

# Tool registry
TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "query_system_status": query_system_status,
    "query_financial_records": query_financial_records,
    "create_jira_ticket": create_jira_ticket,
    "send_slack_notification": send_slack_notification,
    "execute_server_remediation": execute_server_remediation,
}

# Function definitions matching Mistral Tool Schema
MISTRAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches corporate runbooks, policies, and standard operating procedures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords describing the issue or policy to look up (e.g., 'postgres cpu spike', 'procurement policy')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_system_status",
            "description": "Fetches real-time server health, CPU load, and database metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_filter": {
                        "type": "string",
                        "description": "Optional name or ID filter (e.g. 'postgres', 'srv-prod-01')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_financial_records",
            "description": "Fetches corporate invoices, PO numbers, and budget balances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_no": {
                        "type": "string",
                        "description": "The specific invoice number to inspect (e.g. 'INV-2026-882')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_jira_ticket",
            "description": "Files an incident or task in Jira for the appropriate team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Short title of the issue"},
                    "description": {"type": "string", "description": "Detailed explanation of the problem and remediation steps"},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                    "assignee": {"type": "string", "description": "Team or person assigned"}
                },
                "required": ["summary", "description", "priority"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_slack_notification",
            "description": "Sends an alert or progress update to a corporate Slack channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel name, e.g., '#infra-alerts' or '#finance-approvals'"},
                    "message": {"type": "string", "description": "The message body to deliver"}
                },
                "required": ["channel", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_server_remediation",
            "description": "Executes production server remediation (e.g., connection reset, service restart). Requires caution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The target server ID, e.g. 'srv-prod-03'"},
                    "remediation_command": {"type": "string", "description": "The exact action/script to execute"}
                },
                "required": ["server_id", "remediation_command"]
            }
        }
    }
]

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Executes a function and returns a formatted JSON or string output."""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return f"Error: Tool '{tool_name}' not found."
    try:
        return func(**arguments)
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"
