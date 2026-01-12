# app/ui/streamlit_app.py
"""
Streamlit dashboard for Intralogistics Copilot - Multi-Agent System
Run from project root:
    streamlit run app/ui/streamlit_app.py
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import ast
import json

# ensure project root is on path for local imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import new multi-agent system
from app.agents.intralogistics_orchestrator import IntralogisticsOrchestrator
from app.agents.data_agent import DataAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent

# attempt to import LLM call helpers from llm_interface; fallback to decision_engine if needed
try:
    from scripts.llm_interface import call_cerebras, print_response_in_chunks
except Exception:
    try:
        from scripts.decision_engine import call_cerebras, print_response_chunks as print_response_in_chunks
    except Exception:
        # provide a safe stub if neither is available
        def call_cerebras(prompt, model="gpt-oss-120b"):
            return "[LLM not available — set CEREBRAS_API_KEY or check scripts/llm_interface.py]"

        def print_response_in_chunks(resp, chunk_size=80):
            print(resp)

st.set_page_config(layout="wide", page_title="Intralogistics Copilot - Multi-Agent System", initial_sidebar_state="expanded")

# -----------------------------
# Utilities
# -----------------------------
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_PATH = DATA_DIR / "processed" / "polished_action_plans.csv"

def load_polished_actions():
    """Load polished actions CSV and parse list-like columns if present."""
    if not PROCESSED_PATH.exists():
        return pd.DataFrame([])
    df = pd.read_csv(PROCESSED_PATH)
    # attempt to parse list-like columns
    for col in ["recommended_actions", "next_steps"]:
        if col in df.columns:
            def try_parse(x):
                if pd.isna(x): return []
                if isinstance(x, list): return x
                try:
                    return ast.literal_eval(x)
                except Exception:
                    # fallback: split on '||' or ';'
                    if isinstance(x, str) and "||" in x:
                        return [s.strip() for s in x.split("||") if s.strip()]
                    if isinstance(x, str) and ";" in x:
                        return [s.strip() for s in x.split(";") if s.strip()]
                    return [str(x)]
            df[col] = df[col].apply(try_parse)
    return df

def save_polished_actions(df):
    """Save polished actions (atomic write)."""
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)

def color_risk_badge(risk):
    """Return emoji & color for a risk label."""
    if risk == "HIGH":
        return "🔴", "#ff4d4d"
    if risk == "MEDIUM":
        return "🟡", "#ffcc00"
    return "🟢", "#3fbf5f"

def pretty_kpi(col, label, value, delta=None):
    """Display KPI with optional delta."""
    if delta is None:
        col.metric(label=label, value=value)
    else:
        col.metric(label=label, value=value, delta=delta)

# -----------------------------
# Multi-Agent System Integration
# -----------------------------
@st.cache_resource
def get_orchestrator():
    """Initialize and cache the orchestrator (cached)."""
    return IntralogisticsOrchestrator()

@st.cache_data(ttl=60)
def get_decision_df():
    """Return orchestrator decision DataFrame (cached)."""
    orchestrator = get_orchestrator()
    results = orchestrator.execute()
    return pd.DataFrame(results['prioritized_orders'])

@st.cache_data(ttl=60)
def get_system_status():
    """Get current system status from orchestrator."""
    orchestrator = get_orchestrator()
    results = orchestrator.execute()
    return results

@st.cache_data(ttl=60)
def get_robot_health():
    """Get robot health report from monitoring agent."""
    orchestrator = get_orchestrator()
    results = orchestrator.execute()
    return results['robot_health']

# -----------------------------
# Session state for chat & caching
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (user, assistant)

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# -----------------------------
# LLM helpers
# -----------------------------
def build_prompt_from_row(row):
    return f"""
You are an intralogistics operations expert.

Analyze the following warehouse order and robot status:

Order ID: {row['order_id']}
Order Status: {row['status']}
Robot ID: {row['robot_id']}
Robot Health: {row['health_status']}
Anomaly Count: {row['anomaly_count']}
Order Risk Level: {row['order_risk']}

Explain in simple business terms:
1. What is the problem (if any)?
2. Why it is happening?
3. What action should be taken next?

Keep the explanation short and clear.
"""

def get_cached_plan(order_id):
    df = load_polished_actions()
    if df.empty: return None
    if order_id in df["order_id"].values:
        return df[df["order_id"] == order_id].iloc[0].to_dict()
    return None

def save_plan(plan):
    df_existing = load_polished_actions()
    df_new = pd.DataFrame([plan])
    if df_existing.empty:
        df_out = df_new
    else:
        # remove existing with same order_id
        df_existing = df_existing[df_existing["order_id"] != plan["order_id"]]
        df_out = pd.concat([df_existing, df_new], ignore_index=True)
    save_polished_actions(df_out)

def call_llm_safe(prompt, model_choice="gpt-oss-120b"):
    """Call Cerebras while capturing exceptions."""
    try:
        resp = call_cerebras(prompt, model=model_choice)
        return resp
    except Exception as e:
        return f"[LLM error] {e}"

# -----------------------------
# Sidebar controls (global filters)
# -----------------------------
with st.sidebar:
    st.title("Intralogistics Copilot")
    st.caption("Multi-Agent System Dashboard")
    st.markdown("---")

    # Initialize orchestrator and get data
    orchestrator = get_orchestrator()
    df = get_decision_df()

    # System status display
    system_status = get_system_status()
    st.subheader("System Status")
    status_color = "🔴" if system_status['system_status'] == 'CRITICAL' else ("🟡" if system_status['system_status'] == 'WARNING' else "🟢")
    st.markdown(f"{status_color} **{system_status['system_status']}**")

    # Quick stats
    st.markdown("### Quick Stats")
    if df.empty:
        st.warning("Decision data empty — ensure DB is populated.")
    else:
        total_orders = len(df)
        total_delayed = len(df[df["status"] == "DELAYED"])
        total_critical_robots = int((df["health_status"] == "CRITICAL").sum())

        pretty_kpi(st.sidebar, "Total orders", total_orders)
        pretty_kpi(st.sidebar, "Delayed orders", total_delayed)
        pretty_kpi(st.sidebar, "Critical robots", total_critical_robots)

    st.markdown("---")
    st.subheader("Filters")

    risk_filter = st.multiselect("Filter by order risk", options=["HIGH", "MEDIUM", "LOW"], default=["HIGH","MEDIUM","LOW"])
    robot_options = sorted(df["robot_id"].unique().tolist()) if not df.empty else []
    robot_filter = st.multiselect("Filter by robot id", options=robot_options, default=robot_options)

    st.markdown("---")
    st.subheader("LLM Settings")
    model_choice = st.selectbox("Cerebras model", options=["gpt-oss-120b"], index=0)
    call_mode = st.radio("LLM Mode", options=["On-demand (default)", "Batch generate cache"], index=0)
    st.write("API calls may be slow or costly. Use batch mode carefully.")

    st.markdown("---")
    st.subheader("Actions")
    if st.button("Refresh data"):
        st.session_state.last_refresh = time.time()
        st.rerun()

    if st.button("Run System Diagnostic"):
        with st.spinner("Running diagnostic..."):
            diagnostic = orchestrator.run_diagnostic()
            st.success(f"Diagnostic complete: {diagnostic['status']}")

# -----------------------------
# Main layout: Tabs
# -----------------------------
tabs = st.tabs(["🏠 Overview", "📊 Decisions", "🤖 Robot Health", "💬 Chat/Copilot", "📈 Analytics", "🔧 System"])
tab_overview, tab_decisions, tab_health, tab_chat, tab_analytics, tab_system = tabs

# -----------------------------
# Tab: Overview
# -----------------------------
with tab_overview:
    st.header("🏠 Executive Dashboard")
    st.markdown("Real-time overview of warehouse intralogistics operations")

    # Get fresh system status
    system_status = get_system_status()
    df = get_decision_df()

    # Top KPI row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("System Status", system_status['system_status'])
    k2.metric("Total Orders", len(df))
    k3.metric("Delayed Orders", len(df[df["status"]=="DELAYED"]))
    k4.metric("High-Risk Orders", int((df["order_risk"]=="HIGH").sum()))
    k5.metric("Critical Robots", int((df["health_status"]=="CRITICAL").sum()))

    # Multi-agent system visualization
    st.markdown("### 🤖 Multi-Agent System Status")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Orchestrator", "🟢 Active")
    with col2:
        st.metric("Data Agent", "🟢 Active")
    with col3:
        st.metric("Monitoring Agent", "🟢 Active")
    with col4:
        st.metric("Risk Agent", "🟢 Active")
    with col5:
        st.metric("System Health", system_status['system_status'])

    # Risk Distribution
    st.markdown("### 📊 Risk Distribution")
    risk_counts = df["order_risk"].value_counts().reindex(["HIGH","MEDIUM","LOW"]).fillna(0).reset_index()
    risk_counts.columns = ["risk","count"]
    fig = px.pie(risk_counts, names="risk", values="count", color="risk",
                 color_discrete_map={"HIGH":"#ff4d4d","MEDIUM":"#ffcc00","LOW":"#3fbf5f"},
                 title="Order Risk Distribution")
    st.plotly_chart(fig, width='stretch')

    # Robot Health Overview
    st.markdown("### 🤖 Robot Health Overview")
    robot_health = get_robot_health()
    health_df = pd.DataFrame(robot_health)

    if not health_df.empty:
        health_counts = health_df["health_status"].value_counts().reindex(["CRITICAL","WARNING","HEALTHY"]).fillna(0).reset_index()
        health_counts.columns = ["status","count"]

        fig_health = px.bar(health_counts, x="status", y="count",
                           color="status",
                           color_discrete_map={"CRITICAL":"#ff4d4d","WARNING":"#ffcc00","HEALTHY":"#3fbf5f"},
                           title="Robot Health Status")
        st.plotly_chart(fig_health, width='stretch')

    # Recommendations
    st.markdown("### 💡 Actionable Recommendations")
    recommendations = system_status['recommendations']
    for i, recommendation in enumerate(recommendations, 1):
        st.info(f"{i}. {recommendation}")

# -----------------------------
# Tab: Decisions (table + controls)
# -----------------------------
with tab_decisions:
    st.header("📊 Decision Table")
    st.markdown("Prioritized orders with risk assessment and robot health data")

    df = get_decision_df()
    if df.empty:
        st.info("No decision data available.")
    else:
        # apply filters
        df_display = df[(df["order_risk"].isin(risk_filter)) & (df["robot_id"].isin(robot_filter))].copy()

        # add visual badge column
        df_display["risk_badge"] = df_display["order_risk"].map(lambda r: color_risk_badge(r)[0])
        df_display["health_badge"] = df_display["health_status"].map(lambda h: "🔴" if h=="CRITICAL" else ("🟡" if h=="WARNING" else "🟢"))

        # quick search
        q = st.text_input("🔍 Search orders (by id or status)", "")
        if q:
            try:
                qint = int(q)
                df_display = df_display[df_display["order_id"] == qint]
            except Exception:
                df_display = df_display[df_display["status"].str.contains(q, case=False, na=False)]

        # show interactive table
        show_cols = ["risk_badge","health_badge","order_id","robot_id","status","order_risk","anomaly_count","priority"]
        st.dataframe(
            df_display[show_cols]
            .sort_values(["priority", "order_risk", "anomaly_count"], ascending=[True, False, False])
            .reset_index(drop=True),
            height=400,
            width='stretch'
        )

        # Summary statistics
        st.markdown("### 📈 Filtered Data Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Filtered Orders", len(df_display))
        col2.metric("High Risk", len(df_display[df_display["order_risk"]=="HIGH"]))
        col3.metric("Critical Robots", len(df_display[df_display["health_status"]=="CRITICAL"]))

        st.markdown("### 🔍 Order Inspector")
        order_ids = df_display["order_id"].unique().tolist()
        selected_order = st.selectbox("Select Order ID", options=order_ids, index=0 if order_ids else None)

        if selected_order:
            row = df_display[df_display["order_id"] == selected_order].iloc[0]
            st.subheader(f"📦 Order #{selected_order} Detailed Analysis")

            # Order metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Order Risk", row["order_risk"])
            c2.metric("Robot Health", row["health_status"])
            c3.metric("Anomaly Count", int(row["anomaly_count"]))
            c4.metric("Priority", row["priority"])

            # Additional details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Order Details**")
                st.json({
                    "Order ID": row["order_id"],
                    "Robot ID": row["robot_id"],
                    "Status": row["status"],
                    "Items": row["items"]
                })

            with col2:
                st.markdown("**Risk Assessment**")
                st.json({
                    "Risk Level": row["order_risk"],
                    "Priority Score": row["priority"],
                    "Robot Anomalies": int(row["anomaly_count"]),
                    "Health Status": row["health_status"]
                })

            # LLM explanation
            if st.button("🤖 Explain with AI", key=f"explain_{selected_order}"):
                with st.spinner("🤖 AI is analyzing..."):
                    prompt = build_prompt_from_row(row)
                    explanation = call_llm_safe(prompt, model_choice)
                    st.markdown("### 🤖 AI Analysis")
                    st.write(explanation)

                    # show parsed bullets if possible
                    lines = [l.strip() for l in explanation.split("\n") if l.strip()]
                    if lines and len(lines) > 1:
                        st.markdown("### 📋 Action Items")
                        for ln in lines[1:]:  # Skip first line (problem statement)
                            st.write(f"- {ln}")

# -----------------------------
# Tab: Robot Health
# -----------------------------
with tab_health:
    st.header("🤖 Robot Health Monitoring")
    st.markdown("Real-time robot health status and anomaly detection")

    # Get robot health data
    robot_health = get_robot_health()
    health_df = pd.DataFrame(robot_health)

    if health_df.empty:
        st.info("No robot health data available.")
    else:
        # Robot health summary
        st.markdown("### 📊 Robot Health Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Robots", len(health_df))
        col2.metric("Critical", len(health_df[health_df["health_status"]=="CRITICAL"]))
        col3.metric("Warning", len(health_df[health_df["health_status"]=="WARNING"]))

        # Detailed robot health table
        st.markdown("### 🔍 Detailed Robot Health")
        health_display = health_df.copy()
        health_display["status_emoji"] = health_display["health_status"].map(
            lambda s: "🔴" if s == "CRITICAL" else ("🟡" if s == "WARNING" else "🟢")
        )

        display_cols = ["status_emoji", "robot_id", "health_status", "anomaly_count", "temp_anomalies", "vibration_anomalies"]
        st.dataframe(health_display[display_cols].sort_values("anomaly_count", ascending=False), width='stretch')

        # Robot selector for detailed analysis
        st.markdown("### 🔬 Individual Robot Analysis")
        robot_id = st.selectbox("Select Robot", options=health_df["robot_id"].tolist(), index=0)

        if robot_id:
            robot_data = health_df[health_df["robot_id"] == robot_id].iloc[0]

            # Robot health card
            st.subheader(f"🤖 Robot {robot_id} Health Report")

            col1, col2, col3 = st.columns(3)
            col1.metric("Health Status", robot_data["health_status"])
            col2.metric("Total Anomalies", robot_data["anomaly_count"])
            col3.metric("Temperature Issues", robot_data["temp_anomalies"])

            # Anomaly breakdown
            st.markdown("### 📊 Anomaly Breakdown")
            anomaly_data = {
                "Temperature Anomalies": robot_data["temp_anomalies"],
                "Vibration Anomalies": robot_data["vibration_anomalies"]
            }

            fig_anomaly = px.pie(
                values=list(anomaly_data.values()),
                names=list(anomaly_data.keys()),
                title=f"Anomaly Types for Robot {robot_id}"
            )
            st.plotly_chart(fig_anomaly, width='stretch')

            # Health assessment
            st.markdown("### 🏥 Health Assessment")
            if robot_data["health_status"] == "CRITICAL":
                st.error("🚨 This robot requires immediate maintenance!")
                st.markdown("**Recommended Actions:**")
                st.write("- Schedule emergency maintenance")
                st.write("- Reassign orders to other robots")
                st.write("- Investigate root cause of anomalies")
            elif robot_data["health_status"] == "WARNING":
                st.warning("⚠️ This robot needs attention soon")
                st.markdown("**Recommended Actions:**")
                st.write("- Schedule preventive maintenance")
                st.write("- Monitor performance closely")
                st.write("- Check for developing issues")
            else:
                st.success("✅ This robot is operating normally")
                st.markdown("**Recommended Actions:**")
                st.write("- Continue normal operations")
                st.write("- Maintain regular maintenance schedule")

# -----------------------------
# Tab: Chat / Copilot
# -----------------------------
with tab_chat:
    st.header("💬 AI Copilot Assistant")
    st.markdown("Ask natural-language questions about warehouse operations. The system uses multi-agent analysis and LLM for comprehensive responses.")

    user_input = st.text_area("Your question about warehouse operations:", height=160, key="chat_input")

    if st.button("🤖 Ask AI Copilot", key="send_chat"):
        if not user_input.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("🤖 Processing your request..."):
                try:
                    # Get current system data
                    system_status = get_system_status()
                    decision_df = get_decision_df()

                    # Build comprehensive context
                    summary = {
                        "system_status": system_status['system_status'],
                        "total_orders": len(decision_df),
                        "risk_distribution": decision_df["order_risk"].value_counts().to_dict(),
                        "critical_robots": int((decision_df["health_status"] == "CRITICAL").sum())
                    }

                    # Create enhanced prompt with system context
                    prompt = f"""Warehouse Intralogistics Context:
{json.dumps(summary, indent=2)}

User Question: {user_input}

As an intralogistics AI assistant, provide a comprehensive answer that:
1. Addresses the specific question
2. References relevant system data
3. Provides actionable recommendations
4. Explains the reasoning clearly

Format your response with clear sections and bullet points where appropriate."""

                    resp = call_llm_safe(prompt, model_choice)

                    # Store in chat history
                    st.session_state.chat_history.append(("You", user_input))
                    st.session_state.chat_history.append(("AI Copilot", resp))

                    # Display response
                    st.markdown("### 🤖 AI Copilot Response")
                    st.write(resp)

                except Exception as e:
                    resp = f"Error: {e}"
                    st.error(resp)

    # Show chat history
    if st.session_state.chat_history:
        st.markdown("### 💬 Conversation History")
        for speaker, text in reversed(st.session_state.chat_history[-10:]):
            if speaker == "You":
                st.markdown(f"**You:** {text}")
            else:
                st.markdown(f"**AI Copilot:** {text}")

# -----------------------------
# Tab: Analytics
# -----------------------------
with tab_analytics:
    st.header("📈 Advanced Analytics")
    st.markdown("Deep dive into warehouse performance metrics and trends")

    # Get data
    df = get_decision_df()
    system_status = get_system_status()

    # Risk trends by robot
    st.markdown("### 📊 Risk Distribution by Robot")
    risk_by_robot = df.groupby(['robot_id', 'order_risk']).size().reset_index(name='count')
    fig_risk_robot = px.bar(
        risk_by_robot,
        x='robot_id',
        y='count',
        color='order_risk',
        barmode='group',
        title='Order Risk Distribution by Robot',
        color_discrete_map={"HIGH":"#ff4d4d","MEDIUM":"#ffcc00","LOW":"#3fbf5f"}
    )
    st.plotly_chart(fig_risk_robot, width='stretch')

    # Priority distribution
    st.markdown("### 🎯 Priority Distribution")
    priority_counts = df["priority"].value_counts().sort_index().reset_index()
    priority_counts.columns = ["priority", "count"]

    fig_priority = px.bar(
        priority_counts,
        x="priority",
        y="count",
        title="Order Priority Distribution",
        labels={"priority": "Priority Level", "count": "Number of Orders"}
    )
    st.plotly_chart(fig_priority, width='stretch')

    # Risk vs Anomaly correlation
    st.markdown("### 🔗 Risk vs Robot Anomalies Correlation")
    fig_scatter = px.scatter(
        df,
        x="anomaly_count",
        y="order_risk",
        color="health_status",
        title="Order Risk vs Robot Anomaly Count",
        labels={"anomaly_count": "Robot Anomalies", "order_risk": "Order Risk Level"},
        color_discrete_map={"CRITICAL":"#ff4d4d","WARNING":"#ffcc00","HEALTHY":"#3fbf5f"}
    )
    st.plotly_chart(fig_scatter, width='stretch')

    # System metrics
    st.markdown("### 📊 System Performance Metrics")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Order Statistics")
        st.metric("Total Orders", system_status['metadata']['total_orders'])
        st.metric("High Risk Orders", system_status['risk_assessment']['high_risk_count'])
        st.metric("Medium Risk Orders", system_status['risk_assessment']['medium_risk_count'])
        st.metric("Low Risk Orders", system_status['risk_assessment']['low_risk_count'])

    with col2:
        st.subheader("Robot Statistics")
        robot_health = get_robot_health()
        health_df = pd.DataFrame(robot_health)
        st.metric("Total Robots", len(health_df))
        st.metric("Critical Robots", len(health_df[health_df["health_status"]=="CRITICAL"]))
        st.metric("Warning Robots", len(health_df[health_df["health_status"]=="WARNING"]))
        st.metric("Healthy Robots", len(health_df[health_df["health_status"]=="HEALTHY"]))

# -----------------------------
# Tab: System
# -----------------------------
with tab_system:
    st.header("🔧 System Information")
    st.markdown("Multi-agent system status, diagnostics, and configuration")

    # System status
    st.markdown("### 📋 System Status")
    system_status = get_system_status()

    # Display system status card
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Status")
        status_emoji = "🔴" if system_status['system_status'] == 'CRITICAL' else ("🟡" if system_status['system_status'] == 'WARNING' else "🟢")
        st.markdown(f"### {status_emoji} {system_status['system_status']}")

        st.markdown("**System Metadata**")
        st.json({
            "Timestamp": system_status['metadata']['timestamp'],
            "Total Orders": system_status['metadata']['total_orders'],
            "Total Sensor Records": system_status['metadata']['total_sensor_records'],
            "Orchestrator ID": system_status['metadata']['orchestrator_id'][:16] + "..."
        })

    with col2:
        st.subheader("Risk Assessment Summary")
        st.json({
            "High Risk": system_status['risk_assessment']['high_risk_count'],
            "Medium Risk": system_status['risk_assessment']['medium_risk_count'],
            "Low Risk": system_status['risk_assessment']['low_risk_count'],
            "Distribution": system_status['risk_assessment']['distribution']
        })

    # Agent status
    st.markdown("### 🤖 Multi-Agent System")
    st.markdown("All agents in the intralogistics system are operating normally.")

    # Run diagnostic
    if st.button("🔄 Run Full System Diagnostic"):
        with st.spinner("Running comprehensive diagnostic..."):
            orchestrator = get_orchestrator()
            diagnostic = orchestrator.run_diagnostic()

            st.success("Diagnostic Complete!")
            st.markdown(f"**Status:** {diagnostic['status']}")
            st.markdown(f"**Timestamp:** {diagnostic['diagnostic_timestamp']}")

            # Show agent details
            st.markdown("**Agent Details:**")
            for agent_name, agent_info in diagnostic['agents'].items():
                st.markdown(f"- **{agent_name}**: {agent_info['status']} (ID: {agent_info['agent_id'][:8]}...)")

    # System recommendations
    st.markdown("### 💡 System Recommendations")
    recommendations = system_status['recommendations']
    for i, recommendation in enumerate(recommendations, 1):
        st.info(f"{i}. {recommendation}")

    # Export functionality
    st.markdown("### 📥 Export Data")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export Decision Table"):
            df = get_decision_df()
            out_path = DATA_DIR / "processed" / "decision_export.csv"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_path, index=False)
            st.success(f"✅ Decision table exported to {out_path}")

    with col2:
        if st.button("Export System Status"):
            out_path = DATA_DIR / "processed" / "system_status.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'w') as f:
                json.dump(system_status, f, indent=2)
            st.success(f"✅ System status exported to {out_path}")

st.markdown("---")
st.caption("🚀 **Intralogistics Copilot** - Multi-Agent System for Warehouse Optimization | Built with Python, Streamlit, and Cerebras LLM")
