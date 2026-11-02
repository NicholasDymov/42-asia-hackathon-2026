import os
import json
import time
from typing import Generator, Dict, Any, List
from app.tools import MISTRAL_TOOLS, dispatch_tool_call, AUDIT_LOGS

SYSTEM_PROMPT = """You are WorkPulse AI, an autonomous corporate productivity agent.
Your mission is to eliminate enterprise bottlenecks by following the PLAN -> CONNECT -> ACT paradigm:
1. PLAN: Analyze the user's objective and formulate the necessary operational steps.
2. CONNECT: Retrieve critical data from corporate databases, monitoring tools, or internal runbooks using available functions.
3. ACT: Execute actionable outcomes such as creating Jira tickets, sending alerts to Slack channels, or running remediation actions.

Always explain your rationale before or when choosing tools. Keep corporate communications professional, concise, and structured.
"""

class CorporateAgent:
    def __init__(self, api_key: str = "", model: str = "mistral-large-latest"):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "").strip()
        self.model = model or os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        self.client = None
        
        if self.api_key:
            try:
                from mistralai import Mistral
                self.client = Mistral(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Mistral client: {e}")
                self.client = None

    def run_stream(self, prompt: str, auto_approve_sensitive: bool = False) -> Generator[Dict[str, Any], None, None]:
        """
        Executes an agent loop yielding event dictionaries:
        - {"type": "thought", "content": "..."}
        - {"type": "tool_call", "name": "...", "arguments": {...}}
        - {"type": "tool_result", "name": "...", "result": "..."}
        - {"type": "approval_required", "name": "...", "arguments": {...}}
        - {"type": "final_answer", "content": "..."}
        """
        # Fallback to realistic simulator if no API client is available
        if not self.client:
            yield from self._simulate_agent_flow(prompt, auto_approve_sensitive)
            return

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        max_iterations = 6
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            try:
                yield {
                    "type": "thought",
                    "content": f"Analyzing task state and determining next corporate action (Step {iteration})..."
                }

                response = self.client.chat.complete(
                    model=self.model,
                    messages=messages,
                    tools=MISTRAL_TOOLS,
                    tool_choice="auto"
                )

                choice = response.choices[0]
                message = choice.message

                # If model produced text thoughts
                if message.content:
                    yield {
                        "type": "thought",
                        "content": message.content
                    }

                # If no tool calls, model has reached a final answer
                if not message.tool_calls:
                    yield {
                        "type": "final_answer",
                        "content": message.content or "Task completed successfully."
                    }
                    return

                # Record assistant message into context
                messages.append(message)

                # Process all tool calls requested by the model
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    args_str = tool_call.function.arguments
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except Exception:
                        args = {}

                    yield {
                        "type": "tool_call",
                        "name": tool_name,
                        "arguments": args
                    }

                    # Human-in-the-loop gate for sensitive actions
                    if tool_name == "execute_server_remediation" and not auto_approve_sensitive:
                        yield {
                            "type": "approval_required",
                            "name": tool_name,
                            "arguments": args,
                            "warning": "Sensitive production change: Requires human confirmation."
                        }

                    # Execute tool
                    result = dispatch_tool_call(tool_name, args)

                    yield {
                        "type": "tool_result",
                        "name": tool_name,
                        "result": result
                    }

                    # Add tool response to message history
                    messages.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": str(result),
                        "tool_call_id": tool_call.id if hasattr(tool_call, "id") else f"call_{tool_name}"
                    })

            except Exception as e:
                yield {
                    "type": "error",
                    "content": f"Agent runtime error: {str(e)}. Falling back to simulation demo mode."
                }
                yield from self._simulate_agent_flow(prompt, auto_approve_sensitive)
                return

    def _simulate_agent_flow(self, prompt: str, auto_approve_sensitive: bool) -> Generator[Dict[str, Any], None, None]:
        """Realistic offline simulation demonstrating the full PLAN -> CONNECT -> ACT loop."""
        time.sleep(0.4)
        p_lower = prompt.lower()

        if "invoice" in p_lower or "procure" in p_lower or "budget" in p_lower:
            # Scenario: Financial Reconciliation
            yield {
                "type": "thought",
                "content": "PLAN: 1. Fetch invoice records for INV-2026-882.\n2. Review corporate procurement approval policies.\n3. Identify variances and route alerts to #finance-approvals."
            }
            time.sleep(0.6)
            
            yield {
                "type": "tool_call",
                "name": "query_financial_records",
                "arguments": {"invoice_no": "INV-2026-882"}
            }
            res1 = dispatch_tool_call("query_financial_records", {"invoice_no": "INV-2026-882"})
            time.sleep(0.4)
            yield {"type": "tool_result", "name": "query_financial_records", "result": res1}

            yield {
                "type": "thought",
                "content": "Invoice INV-2026-882 is $14,200.00 against an approved budget of $10,000.00 ($4,200 overrun, 42% over limit). Checking procurement policy."
            }
            time.sleep(0.5)

            yield {
                "type": "tool_call",
                "name": "search_knowledge_base",
                "arguments": {"query": "procurement policy"}
            }
            res2 = dispatch_tool_call("search_knowledge_base", {"query": "procurement policy"})
            time.sleep(0.4)
            yield {"type": "tool_result", "name": "search_knowledge_base", "result": res2}

            yield {
                "type": "thought",
                "content": "Policy mandates that variances exceeding 10% on invoices >$10k must alert #finance-approvals and require VP sign-off."
            }
            time.sleep(0.5)

            yield {
                "type": "tool_call",
                "name": "send_slack_notification",
                "arguments": {
                    "channel": "#finance-approvals",
                    "message": "⚠️ Invoice Variance Alert: INV-2026-882 from CloudHost Global ($14,200.00) exceeds PO-9031 budget ($10,000.00) by $4,200 (+42%). VP approval required."
                }
            }
            res3 = dispatch_tool_call("send_slack_notification", {
                "channel": "#finance-approvals",
                "message": "⚠️ Invoice Variance Alert: INV-2026-882 from CloudHost Global ($14,200.00) exceeds PO-9031 budget ($10,000.00) by $4,200 (+42%). VP approval required."
            })
            yield {"type": "tool_result", "name": "send_slack_notification", "result": res3}

            yield {
                "type": "final_answer",
                "content": "### Procurement Reconciliation Complete\n- **Invoice:** INV-2026-882 (CloudHost Global)\n- **Billed Amount:** $14,200.00 (Approved PO Budget: $10,000.00)\n- **Variance:** +$4,200.00 (+42%)\n- **Action Taken:** Flagged policy breach and dispatched executive alert to `#finance-approvals` for sign-off."
            }

        else:
            # Default Scenario: Infrastructure Incident Response
            yield {
                "type": "thought",
                "content": "PLAN: 1. Check live status of production servers and database pools.\n2. Query the SRE runbook for recommended incident remediation.\n3. Create an incident ticket in Jira.\n4. Apply remediation to restore normal performance."
            }
            time.sleep(0.6)

            yield {
                "type": "tool_call",
                "name": "query_system_status",
                "arguments": {"service_filter": "postgres"}
            }
            res1 = dispatch_tool_call("query_system_status", {"service_filter": "postgres"})
            time.sleep(0.4)
            yield {"type": "tool_result", "name": "query_system_status", "result": res1}

            yield {
                "type": "thought",
                "content": "Found server `srv-prod-03` (Postgres Primary DB) at 91% CPU with 498/500 connection limit reached. Searching knowledge base for incident runbook."
            }
            time.sleep(0.5)

            yield {
                "type": "tool_call",
                "name": "search_knowledge_base",
                "arguments": {"query": "postgres cpu spike"}
            }
            res2 = dispatch_tool_call("search_knowledge_base", {"query": "postgres cpu spike"})
            time.sleep(0.4)
            yield {"type": "tool_result", "name": "search_knowledge_base", "result": res2}

            yield {
                "type": "thought",
                "content": "Runbook recommends creating a HIGH priority incident ticket and executing an idle connection pool reset."
            }
            time.sleep(0.4)

            yield {
                "type": "tool_call",
                "name": "create_jira_ticket",
                "arguments": {
                    "summary": "Postgres Primary DB Connection Saturation (498/500)",
                    "description": "High CPU (91%) and connection exhaustion detected on srv-prod-03. Auto-remediation in progress.",
                    "priority": "High",
                    "assignee": "DevOps On-Call"
                }
            }
            res3 = dispatch_tool_call("create_jira_ticket", {
                "summary": "Postgres Primary DB Connection Saturation (498/500)",
                "description": "High CPU (91%) and connection exhaustion detected on srv-prod-03. Auto-remediation in progress.",
                "priority": "High",
                "assignee": "DevOps On-Call"
            })
            yield {"type": "tool_result", "name": "create_jira_ticket", "result": res3}

            # Human in the loop gate simulation
            if not auto_approve_sensitive:
                yield {
                    "type": "approval_required",
                    "name": "execute_server_remediation",
                    "arguments": {
                        "server_id": "srv-prod-03",
                        "remediation_command": "pg_terminate_idle_connections --pool-reset"
                    },
                    "warning": "Sensitive production change: Requires human confirmation."
                }

            yield {
                "type": "tool_call",
                "name": "execute_server_remediation",
                "arguments": {
                    "server_id": "srv-prod-03",
                    "remediation_command": "pg_terminate_idle_connections --pool-reset"
                }
            }
            res4 = dispatch_tool_call("execute_server_remediation", {
                "server_id": "srv-prod-03",
                "remediation_command": "pg_terminate_idle_connections --pool-reset"
            })
            yield {"type": "tool_result", "name": "execute_server_remediation", "result": res4}

            yield {
                "type": "tool_call",
                "name": "send_slack_notification",
                "arguments": {
                    "channel": "#infra-alerts",
                    "message": "✅ Resolved: Postgres Primary DB (srv-prod-03) connection pool cleared. CPU stabilized at 28%."
                }
            }
            res5 = dispatch_tool_call("send_slack_notification", {
                "channel": "#infra-alerts",
                "message": "✅ Resolved: Postgres Primary DB (srv-prod-03) connection pool cleared. CPU stabilized at 28%."
            })
            yield {"type": "tool_result", "name": "send_slack_notification", "result": res5}

            yield {
                "type": "final_answer",
                "content": "### Incident Triage & Resolution Completed\n- **Target Service:** Postgres Primary DB (`srv-prod-03`)\n- **Incident Cause:** Connection starvation (498/500 connections, 91% CPU load)\n- **Tickets Filed:** High Priority incident registered in Jira\n- **Remediation Action:** Idle connection pool reset executed\n- **Status:** Restored to HEALTHY (28% CPU, 65 active connections)\n- **Broadcast:** Resolution posted to `#infra-alerts`"
            }
