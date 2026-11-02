import os
import sys
from pathlib import Path
import json
import streamlit as st

# Ensure project root is in sys.path
_root_dir = str(Path(__file__).resolve().parent.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from app.config import MISTRAL_API_KEY, MISTRAL_MODEL
    from app.agent import CorporateAgent
    from app.tools import MOCK_DATABASE, AUDIT_LOGS
except ImportError:
    from config import MISTRAL_API_KEY, MISTRAL_MODEL
    from agent import CorporateAgent
    from tools import MOCK_DATABASE, AUDIT_LOGS

st.set_page_config(
    page_title="WorkPulse AI - Corporate Productivity Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern corporate dashboard look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #888888;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-mistral { background-color: #ff7000; color: white; }
    .badge-pattern { background-color: #2b5cff; color: white; }
    .badge-sandbox { background-color: #00aa6c; color: white; }
    .trace-card {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #4a69bd;
        background-color: rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<div class="main-title">⚡ WorkPulse AI — Autonomous Corporate Agent</div>', unsafe_allow_html=True)
st.markdown("""
<div>
    <span class="badge-pill badge-mistral">Powered by Mistral AI</span>
    <span class="badge-pill badge-pattern">PLAN → CONNECT → ACT</span>
    <span class="badge-pill badge-sandbox">Containerized Sandbox</span>
</div>
<div class="sub-title" style="margin-top: 10px;">
    42 Asia Hackathon 2026 Tokyo prototype — Removing corporate productivity bottlenecks with live action execution.
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Agent Settings")
    
    api_key_input = st.text_input(
        "Mistral API Key",
        value=MISTRAL_API_KEY,
        type="password",
        help="Paste your Mistral AI API key here or leave blank to use the built-in offline simulator."
    )
    
    model_choice = st.selectbox(
        "Mistral Model",
        options=["mistral-large-latest", "mistral-small-latest", "codestral-latest"],
        index=0
    )
    
    st.divider()
    
    st.subheader("🛡️ Enterprise Governance")
    human_in_the_loop = st.checkbox(
        "Human-in-the-Loop Confirmation",
        value=True,
        help="Require human approval before applying critical server remediation or releasing large payments."
    )
    
    st.divider()
    st.subheader("💡 1-Click Demo Scenarios")
    
    scenario_1 = st.button("🚨 Database CPU Spike & Failover", use_container_width=True)
    scenario_2 = st.button("💰 Invoice Overrun & Compliance", use_container_width=True)
    
    st.divider()
    with st.expander("📊 Corporate DB State Inspector"):
        st.write("**Servers:**")
        st.json(MOCK_DATABASE["servers"])
        st.write("**Invoices:**")
        st.json(MOCK_DATABASE["invoices"])
        st.write("**Audit Log:**")
        st.write(f"{len(AUDIT_LOGS)} actions executed so far.")

# Determine current prompt
current_prompt = ""
if scenario_1:
    current_prompt = "There is an alert that our Postgres database is experiencing severe CPU lag. Investigate server health, check the SRE runbook, file a Jira ticket, execute remediation, and update #infra-alerts."
elif scenario_2:
    current_prompt = "Review pending invoice INV-2026-882 from CloudHost Global against company procurement policy. If there is a budget overrun, alert the appropriate Slack channel."

user_input = st.chat_input("Instruct the agent (e.g. 'Audit production servers and report any degraded services')...")

prompt_to_run = user_input or current_prompt

if prompt_to_run:
    st.markdown(f"### 🎯 Mission Objective: `{prompt_to_run}`")
    
    agent = CorporateAgent(api_key=api_key_input, model=model_choice)
    
    progress_col, status_col = st.columns([3, 1])
    
    with progress_col:
        st.write("#### 🔄 Live Execution Trace (Plan → Connect → Act)")
        trace_container = st.container()
        
    approval_granted = True
    
    with trace_container:
        for event in agent.run_stream(prompt_to_run, auto_approve_sensitive=not human_in_the_loop):
            event_type = event.get("type")
            
            if event_type == "thought":
                with st.chat_message("assistant", avatar="🧠"):
                    st.markdown(f"**Planning / Reasoning:**\n\n{event['content']}")
                    
            elif event_type == "tool_call":
                with st.chat_message("assistant", avatar="🛠️"):
                    st.markdown(f"**Invoking Tool:** `{event['name']}`")
                    st.code(json.dumps(event['arguments'], indent=2), language="json")
                    
            elif event_type == "approval_required":
                st.warning(f"⚠️ **Human Approval Required:** Action `{event['name']}` will modify production state.")
                
            elif event_type == "tool_result":
                with st.chat_message("user", avatar="⚡"):
                    st.markdown(f"**Tool Output (`{event['name']}`):**")
                    st.code(str(event['result']), language="text")
                    
            elif event_type == "final_answer":
                st.success("✅ **Mission Completed**")
                st.markdown(event['content'])
                
            elif event_type == "error":
                st.error(event['content'])

    with status_col:
        st.write("#### 📋 Real-Time Audit Log")
        if AUDIT_LOGS:
            for log in reversed(AUDIT_LOGS[-4:]):
                action = log.get("action", "UNKNOWN")
                st.info(f"**{action}**\n\n`{json.dumps(log, indent=1)}`")
        else:
            st.caption("No actions recorded yet.")
else:
    st.info("👈 Select one of the **1-Click Demo Scenarios** in the sidebar or type a task below to see the agent in action.")
