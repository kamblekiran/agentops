import streamlit as st
import pandas as pd
import json
import os
from config import is_simulation_mode
from utils.azure_cosmos import fetch_all_sessions

# st.set_page_config(page_title="🕓 Historical Runs", layout="wide")
st.title("🕓 Historical Azure Pipeline Runs")

# === Load Data ===
if is_simulation_mode():
    st.info("🔁 Simulation Mode Enabled — using mock data")
    mock_data_path = os.path.join(os.getcwd(), "mock_data", "historical_runs.json")
    if not os.path.exists(mock_data_path):
        st.error("Missing mock_data/historical_runs.json")
        st.stop()
    with open(mock_data_path, "r") as f:
        sessions = json.load(f)
else:
    sessions = fetch_all_sessions()
    print("sessions", sessions)

    # ✅ DEBUGGING — Confirm Cosmos DB Data Structure
    try:
        session_count = len(sessions) if hasattr(sessions, "__len__") else "unknown"
        st.info(f"✅ Cosmos DB fetched {session_count} session(s).")
    except Exception as e:
        st.error(f"❌ Could not determine session count: {e}")

    try:
        if isinstance(sessions, dict) and sessions:
            st.markdown("### 🔍 First Cosmos DB Session (Preview):")
            st.json(dict(list(sessions.items())[:1]))  # show one session
        else:
            st.warning("⚠️ No session data found in Cosmos DB.")
    except Exception as e:
        st.error(f"❌ Error displaying Cosmos DB session preview: {e}")

# === Flatten Session Logs ===
rows = []

if isinstance(sessions, list):  # Simulation mode
    for s in sessions:
        session_id = s.get("session_id", "mock-session")
        agents = s.get("agents", {})
        for agent_name, log in agents.items():
            output = log.get("output", {})
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except json.JSONDecodeError:
                    output = {}
            rows.append({
                "session_id": session_id,
                "agent": agent_name,
                "timestamp": log.get("timestamp"),
                "repo": log.get("input", {}).get("repo_url", "N/A"),
                "mode": log.get("input", {}).get("mode", "simulation"),
                "status": log.get("status", "unknown"),
                "issues_found": str(output.get("issues_found", "N/A") if output else "N/A"),
            })
else:
    for session_id, session in sessions.items():
        agents = session.get("agents", {})
        for agent_name, log in agents.items():
            output = log.get("output", {})
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except json.JSONDecodeError:
                    output = {}
            rows.append({
                "session_id": session_id,
                "agent": agent_name,
                "timestamp": log.get("timestamp"),
                "repo": log.get("input", {}).get("repo_url", "N/A"),
                "mode": log.get("input", {}).get("mode", "production"),
                "status": log.get("status", "unknown"),
                "issues_found": str(output.get("issues_found", "N/A") if output else "N/A"),
            })

    df = pd.DataFrame(rows)
    print(df)

    # 🔍 Debug: Show what's inside the DataFrame
    st.subheader("🔧 Debug Info")
    st.text(f"Columns in DataFrame: {list(df.columns)}")
    st.text(f"Number of rows: {len(df)}")

    # ✅ Fallback if 'mode' column is missing
    if "mode" not in df.columns:
        st.warning("⚠️ 'mode' column missing — injecting fallback value")
        df["mode"] = "unknown"

    # === Filters ===
    st.sidebar.header("🔍 Filters")

    selected_mode = st.sidebar.selectbox("Mode", ["All", "simulation", "production"])
    selected_status = st.sidebar.selectbox("Status", ["All"] + sorted(df["status"].dropna().unique()) if not df.empty else ["All"])
    selected_agent = st.sidebar.selectbox("Agent", ["All"] + sorted(df["agent"].unique()) if not df.empty else ["All"])

    if selected_mode != "All":
        df = df[df["mode"] == selected_mode]

    if selected_status != "All":
        df = df[df["status"] == selected_status]

    if selected_agent != "All":
        df = df[df["agent"] == selected_agent]
        
    if "mode" in df.columns:
        df = df[df["mode"] == selected_mode]
    else:
        print("Column 'mode' not found in DataFrame")

    # === Display Table as Clean Cards ===
    st.markdown("### 📄 Filtered Run Log")

    if df.empty:
        st.warning("No matching records found with the selected filters.")
    else:
        for _, row in df.sort_values("timestamp", ascending=False).iterrows():
            with st.container():
                col1, col2, col3 = st.columns([1.4, 1.6, 2.5])
                with col1:
                    st.markdown(f"**🧪 Agent:** `{row.agent}`")
                    st.markdown(f"**🕒 Time:** `{row.timestamp}`")
                    st.markdown(f"**🆔 Session:** `{row.session_id}`")
                with col2:
                    st.markdown(f"**🗂 Repo:** [{row.repo}]({row.repo})")
                    st.markdown(f"**📌 Mode:** `{row.mode}`")
                    st.markdown(f"**🐞 Issues:** `{row.issues_found}`")
                with col3:
                    status = str(row.status)
                    if "✅" in status:
                        icon = "🟢"
                    elif "❌" in status:
                        icon = "🔴"
                    elif "⚠️" in status:
                        icon = "🟠"
                    else:
                        icon = "⚪️"
                    st.markdown(f"**📊 Status:** {icon} `{status.replace('✅','').replace('❌','').replace('⚠️','').strip()}`")
                st.markdown("---")

        # === Download Option ===
        st.download_button(
            label="⬇️ Download Filtered CSV",
            data=df.to_csv(index=False),
            file_name="filtered_historical_runs.csv",
            mime="text/csv"
        )
