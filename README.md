# WorkPulse AI — Autonomous Corporate Productivity Agent
> **42 Asia Hackathon 2026 Tokyo** (Powered by Mistral AI)  
> *Theme:* "AI Agents for Corporate Productivity"  
> *Core Pattern:* **PLAN → CONNECT → ACT**

---

## 📌 Architecture & Design

WorkPulse AI removes corporate productivity bottlenecks by turning model reasoning into deterministic enterprise actions:

```
                  ┌──────────────────────────────────────────────┐
                  │   Streamlit Web Interface (Port 8501)        │
                  │   - Live step-by-step Execution Trace        │
                  │   - Real-time Audit & Governance Log         │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    CorporateAgent (Orchestration Engine)     │
                  │    - Powered by `mistralai` Python SDK       │
                  │    - Dynamic Function Calling loop           │
                  │    - Human-in-the-Loop Approval Safeguards   │
                  └──────────────────────┬───────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
       ┌────────────────────────┐                ┌─────────────────────────┐
       │   Corporate Systems    │                │  Knowledge & Monitoring │
       │ - Jira Ticket Creation │                │ - SRE Incident Runbooks │
       │ - Slack Notifications  │                │ - Procurement Policies  │
       │ - Server Remediation   │                │ - Server Health Metrics │
       └────────────────────────┘                └─────────────────────────┘
```

---

## 🔒 Sandboxed Execution (Docker)

To protect your host machine, the entire application runs in an isolated non-root container sandbox.

### 1. Configure Your API Key
Edit the `.env` file in the root directory:
```bash
MISTRAL_API_KEY=your_actual_mistral_api_key
MISTRAL_MODEL=mistral-large-latest
```
*(If left blank, the application will automatically run in the built-in **Simulation Mode**, allowing you to test and demo the complete PLAN $\rightarrow$ CONNECT $\rightarrow$ ACT loop without an active API key).*

### 2. Start the Sandbox Container
Run the included helper script:
```bash
./run_sandbox.sh
```
Or run Docker directly:
```bash
docker build -t mistral-hackathon-agent .
docker run -d --rm --name workpulse_sandbox -p 8501:8501 --env-file .env mistral-hackathon-agent
```

### 3. Access the Dashboard
Open your web browser at:
👉 **`http://localhost:8501`**

---

## 🚀 Pre-configured 1-Click Scenarios for Hackathon Demo

1. **🚨 Database CPU Spike & Failover (IT Operations):**
   * **Plan:** Detects degraded servers, consults SRE runbooks.
   * **Connect:** Fetches metrics for Postgres DB pool saturation (498/500 connections).
   * **Act:** Files high-priority Jira ticket, prompts for human approval, executes connection pool reset, broadcasts resolution to `#infra-alerts`.

2. **💰 Invoice Overrun & Compliance (Finance / Procurement):**
   * **Plan:** Evaluates incoming vendor invoice `INV-2026-882` from CloudHost Global.
   * **Connect:** Pulls approved purchase order budget and cross-checks corporate procurement threshold policies.
   * **Act:** Flags 42% budget discrepancy ($14,200 vs $10,000) and alerts `#finance-approvals` for VP sign-off.

---

## 📂 Project Structure

```text
.
├── 42-Asia-Hackathon-2026-Tokyo.pdf  # Hackathon guidelines and brief
├── Dockerfile                        # Sandboxed container definition
├── docker-compose.yml                # Compose orchestration configuration
├── run_sandbox.sh                    # 1-click startup script
├── requirements.txt                  # Python dependencies (mistralai, streamlit)
├── .env.example                      # Environment variables template
├── app/
│   ├── __init__.py
│   ├── config.py                     # App configuration & env loader
│   ├── tools.py                      # Corporate tool definitions & Mistral JSON schemas
│   ├── agent.py                      # Mistral Agent loop (Plan -> Connect -> Act)
│   └── main.py                       # Streamlit UI with live trace & audit log
└── README.md                         # Documentation
```
