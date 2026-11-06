import os
import sys
from pathlib import Path
import json
import pandas as pd
import streamlit as st

_root_dir = str(Path(__file__).resolve().parent.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from core.db import get_connection, init_database
from core.chaos import chaos_engine
from core.doc_parser import extract_text_from_pdf_bytes
from core.test_runner import run_skill_unit_test
from core.orchestrator import Orchestrator
from core.trust_engine import trust_engine
from core.audit import audit_ledger
from core.policies import policy_engine

init_database()

st.set_page_config(
    page_title="WorkPulse AI | Production Operations Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .top-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 20px; background: #111827; border-radius: 8px;
        border: 1px solid #1f2937; margin-bottom: 16px;
    }
    .metric-chip {
        display: inline-block; padding: 4px 10px; border-radius: 6px;
        font-size: 0.8rem; font-weight: 600; margin-right: 8px;
        background: #1e293b; border: 1px solid #334155;
    }
    .chip-green { color: #10b981; border-color: rgba(16, 185, 129, 0.3); }
    .chip-orange { color: #f59e0b; border-color: rgba(245, 158, 11, 0.3); }
    .chip-red { color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
    .chip-blue { color: #3b82f6; border-color: rgba(59, 130, 246, 0.3); }
</style>
""", unsafe_allow_html=True)

# Top Bar
st.markdown("""
<div class="top-header">
    <div>
        <span style="font-size: 1.4rem; font-weight: 800; color: #f8fafc;">
            🛡️ WORKPULSE AI <span style="font-weight: 400; color: #94a3b8; font-size: 1rem;">| Production Operations Console</span>
        </span>
    </div>
    <div>
        <span class="metric-chip chip-green">🟢 SQLITE ENGINE: CONNECTED</span>
        <span class="metric-chip chip-blue">🤖 MULTI-AGENT HUB: ACTIVE</span>
        <span class="metric-chip chip-orange">🛡️ SUBPROCESS SANDBOX: READY</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize Orchestrator in session state so it persists
if "orchestrator" not in st.session_state:
    st.session_state["orchestrator"] = Orchestrator()

orchestrator = st.session_state["orchestrator"]

# Sidebar
with st.sidebar:
    st.markdown("### 🔐 RBAC Identity")
    active_role = st.selectbox("Current Role", ["DevOps", "Finance", "Executive"], index=0)
    st.caption(f"Role: `{active_role}` | Clearance: `L4-RESTRICTED`")

    st.divider()
    st.markdown("### 🔑 Mistral AI API Key")
    api_key_input = st.text_input(
        "Enter Mistral API Key (Optional)",
        type="password",
        value=os.getenv("MISTRAL_API_KEY", ""),
        help="Paste your key to activate live Mistral Large & Codestral models. If empty, local engine runs."
    )
    if api_key_input:
        orchestrator.update_api_key(api_key_input)
        st.caption("🟢 Live Mistral API Active")
    else:
        st.caption("ℹ️ Running in Local Deterministic Engine")

    st.divider()
    st.markdown("### 💥 Real Chaos Generator")
    st.caption("Injects real SQL load to spike CPU and saturate connections on srv-tokyo-db.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚨 Spike DB Load", width="stretch"):
            chaos_engine.trigger_db_saturation("srv-tokyo-db")
            st.session_state["chaos_status"] = "SPIKED"
            st.rerun()
    with c2:
        if st.button("🧹 Clear Chaos", width="stretch"):
            chaos_engine.resolve_chaos("srv-tokyo-db")
            st.session_state["chaos_status"] = "CLEARED"
            st.rerun()

    if st.session_state.get("chaos_status") == "SPIKED":
        st.error("⚠️ Chaos Active: srv-tokyo-db CPU spiked to 98.4%!")
    elif st.session_state.get("chaos_status") == "CLEARED":
        st.success("✅ Baseline Restored: srv-tokyo-db HEALTHY (22%).")

    st.divider()
    st.markdown("### ⚡ Quick Operational Actions")
    trig_outage = st.button("🚀 Remediate Tokyo DB Outage", width="stretch")
    trig_evolution = st.button("🧬 Learn Qualified Invoice Skill", width="stretch")

# Tabs
tab_ops, tab_real_db, tab_docs, tab_rfc_runner, tab_audit = st.tabs([
    "🖥️ Operations Command Center",
    "🗄️ Real SQLite Database Inspector",
    "📄 Real PDF & Document Ingestion",
    "🧪 Skill Subprocess Test Runner & RFC",
    "📜 Live Database Audit Ledger"
])

# --- Tab 1: Operations ---
with tab_ops:
    col_status, col_agent = st.columns([1, 2])

    with col_status:
        st.markdown("#### 📡 Real Server Health (SQLite)")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, status, cpu_percent, active_connections FROM servers")
            servers = [dict(r) for r in cursor.fetchall()]

        for s in servers:
            is_crit = s["status"] != "HEALTHY"
            chip_color = "chip-red" if is_crit else "chip-green"
            st.markdown(f"""
            <div style="background:#131c2e; border:1px solid #1e293b; padding:10px 14px; border-radius:6px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between;">
                    <b>{s['name']}</b>
                    <span class="metric-chip {chip_color}">{s['status']}</span>
                </div>
                <div style="font-size:0.82rem; color:#94a3b8; margin-top:4px;">
                    CPU: {s['cpu_percent']}% • Conn: {s['active_connections']}/500
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### 💰 Cloud Budget Balance (SQLite)")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM budgets WHERE department = 'Infrastructure'")
            b_row = dict(cursor.fetchone())
        st.write(f"- Monthly Cap: **¥{b_row['monthly_allocation_yen']:,}**")
        st.write(f"- Real Spent: **¥{b_row['spent_yen']:,}**")
        st.write(f"- Available: **¥{(b_row['monthly_allocation_yen'] - b_row['spent_yen']):,}**")

    with col_agent:
        st.markdown("#### ⚡ Multi-Agent Execution Matrix")
        prompt_to_run = ""

        if trig_outage:
            prompt_to_run = "PagerDuty Incident #88392: Tokyo Postgres Cluster (srv-tokyo-db) latency critical (4,200ms). Perform emergency diagnosis, cross-department spend delegation, and failover."
        elif trig_evolution:
            prompt_to_run = "Verify Japanese Qualified Invoice INV-TYO-901 from Sakura Cloud Solutions against National Tax Agency Inbousu Seido rules."

        chat_in = st.chat_input(f"Dispatch command as [{active_role}] (e.g. 'Check server status and remediate failures')...")
        if chat_in:
            prompt_to_run = chat_in

        if prompt_to_run:
            st.markdown(f"**Target Objective:** `{prompt_to_run}`")
            box = st.container()
            with box:
                for event in orchestrator.run_workflow_stream(prompt_to_run, active_role=active_role):
                    etype = event.get("type")
                    if etype == "thought":
                        with st.chat_message("assistant", avatar="🧠"):
                            st.markdown(f"**{event['agent']}:**\n\n{event['content']}")
                    elif etype == "delegation":
                        st.info(f"🤝 **Cross-Departmental Delegation:** {event['from_agent']} ➔ {event['to_agent']}\n\n**Reason:** {event['reason']}")
                    elif etype == "sentinel_check":
                        st.success(f"🛡️ **Sentinel Policy Evaluation ({event['status']}):** {event['reason']}")
                    elif etype == "tool_call":
                        with st.chat_message("assistant", avatar="🛠️"):
                            st.markdown(f"**Tool Call:** `{event['name']}`")
                            st.code(json.dumps(event['arguments'], indent=2), language="json")
                    elif etype == "tool_result":
                        with st.chat_message("user", avatar="⚡"):
                            st.code(str(event['result']), language="text")
                    elif etype == "propose_new_skill":
                        st.session_state["pending_skill"] = event["skill"]
                        st.warning("🧬 **Curator synthesized a new skill!** Open 'Skill Subprocess Test Runner' tab to test and approve.")
                    elif etype == "final_summary":
                        st.success("✅ **Objective Remediated & State Persisted**")
                        st.markdown(event['content'])
                    elif etype == "error":
                        st.error(f"❌ Error: {event['content']}")
        else:
            st.caption("Agent collective is standing by. Type a command or click an action.")

# --- Tab 2: Real Database Inspector ---
with tab_real_db:
    st.subheader("🗄️ Real SQLite Tables (`enterprise.db`)")
    st.caption("These tables are real database rows on disk, updated live when the agent calls tools.")

    t_serv, t_inv, t_tick = st.tabs(["Servers Table", "Invoices Table", "Jira Tickets Table"])
    with t_serv:
        with get_connection() as conn:
            st.dataframe(pd.read_sql("SELECT * FROM servers", conn), width="stretch")
    with t_inv:
        with get_connection() as conn:
            st.dataframe(pd.read_sql("SELECT * FROM invoices", conn), width="stretch")
    with t_tick:
        with get_connection() as conn:
            st.dataframe(pd.read_sql("SELECT * FROM tickets", conn), width="stretch")

# --- Tab 3: Real PDF Ingestion ---
with tab_docs:
    st.subheader("📄 Real PDF Parsing & Document Pipeline")
    st.caption("Upload any real enterprise PDF (e.g. hackathon rules, invoices, or agreements) to parse text and test extraction.")

    uploaded_pdf = st.file_uploader("Upload Corporate PDF Document", type=["pdf"])
    if uploaded_pdf:
        pdf_bytes = uploaded_pdf.read()
        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
        st.write(f"**Extracted {len(extracted_text)} characters from `{uploaded_pdf.name}`**")
        st.text_area("Parsed Text Content", value=extracted_text, height=250)
    else:
        # Pre-load the hackathon PDF that exists in the repo
        candidate_paths = [
            Path(__file__).resolve().parent / "docs" / "hackathon_brief.pdf",
            Path("/app/app/docs/hackathon_brief.pdf"),
            Path("/home/nic/code/hackathon/42-Asia-Hackathon-2026-Tokyo.pdf")
        ]
        found_pdf = next((p for p in candidate_paths if p.exists()), None)
        if found_pdf:
            if st.button(f"📖 Read Repository PDF ('{found_pdf.name}')"):
                with open(found_pdf, "rb") as f:
                    pdf_bytes = f.read()
                extracted = extract_text_from_pdf_bytes(pdf_bytes)
                st.write(f"**Successfully extracted {len(extracted)} characters from `{found_pdf.name}`!**")
                st.text_area("Extracted Document Content", value=extracted[:2500] + "\n\n...[truncated for display]", height=280)
        else:
            st.info("No default PDF found in container. You can drag and drop any PDF file above.")

# --- Tab 4: Subprocess Test Runner & RFC ---
with tab_rfc_runner:
    st.subheader("🧪 Subprocess Sandbox Test Runner & RFC")
    st.caption("Executes AI-synthesized skills in an isolated Python subprocess before human approval.")

    pending = st.session_state.get("pending_skill")
    if pending:
        st.write(f"### Proposed Skill: `{pending['skill_name']}` (Category: `{pending['category']}`)")
        st.code(pending["code"], language="python")

        test_call = f"{pending['skill_name']}('INV-TEST-01', 'T1010001001234', 110000)"
        st.write(f"**Target Test Call:** `{test_call}`")

        if st.button("▶️ Execute Subprocess Unit Test"):
            with st.spinner("Spawning isolated Python subprocess..."):
                passed, output = run_skill_unit_test(pending["code"], pending["skill_name"], test_call)
                if passed:
                    st.success(f"✅ Subprocess Unit Test PASSED!\n\n**Output:** `{output}`")
                    st.session_state["unit_test_passed"] = True
                else:
                    st.error(f"❌ Subprocess Test FAILED: {output}")

        if st.session_state.get("unit_test_passed"):
            if st.button("✅ Commit Verified Skill to Dynamic Registry", type="primary"):
                reg_res = trust_engine.register_new_skill(
                    name=pending["skill_name"],
                    code=pending["code"],
                    description=pending["description"],
                    schema=pending["schema"],
                    category=pending["category"]
                )
                if reg_res.get("success"):
                    st.success(f"🎉 Skill '{pending['skill_name']}' is now committed and hot-loaded into active memory!")
                    st.session_state["pending_skill"] = None
                    st.session_state["unit_test_passed"] = False
                    st.rerun()
                else:
                    st.error(f"Registration failed: {reg_res.get('error')}")
    else:
        st.info("No pending RFCs. Click 'Learn Qualified Invoice Skill' in the sidebar to generate one.")

# --- Tab 5: Live Database Audit ---
with tab_audit:
    st.subheader("📜 Live Database Audit Events (`audit_events` table)")
    st.caption("Real rows permanently committed to SQLite for every event.")
    with get_connection() as conn:
        st.dataframe(pd.read_sql("SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT 50", conn), width="stretch")
