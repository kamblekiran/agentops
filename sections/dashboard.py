import streamlit as st
import pandas as pd
import json
import os
import altair as alt

# === Styling ===
st.markdown("""
<style>
body {
    font-family: 'Inter', sans-serif;
    background-color: #f7f9fc;
    color: #111;
}
h1 {
    font-size: 2.3rem;
    font-weight: 800;
}
.card {
    background: white;
    padding: 1.5rem;
    margin: 1rem 0;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.kpi {
    font-size: 2rem;
    font-weight: 700;
    color: #0078D4;
}
.label {
    font-weight: 600;
    font-size: 1rem;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Azure AgentOps Dashboard")

# === Expandable Latest Run Summary ===
with st.expander("🕒 Latest Run Summary", expanded=False):
    if "repo_url" in st.session_state:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**🔗 Repository:** `{st.session_state['repo_url']}`")

        agent_keys = [
            ("🧠 Code Review", "code_review_result"),
            ("🧪 Unit Testing", "unit_test_result"),
            ("📉 Regression Checks", "regression_result"),
            ("🏗️ Build Process", "build_result"),
            ("🚀 Deployment", "deploy_result"),
            ("📈 Monitoring", "monitor_result"),
            ("↩️ Rollback Plan", "rollback_result"),
        ]
        for title, key in agent_keys:
            st.markdown(f"**{title}**")
            if key in st.session_state:
                result = st.session_state[key]
                for k, v in result.items():
                    if isinstance(v, (str, int, float)):
                        st.markdown(f"- **{k}**: {v}")
            else:
                st.info("No result available.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No run data available. Run pipeline to populate this.")

# === Mocked Historical Data ===
mock_data_path = os.path.join(os.getcwd(), "mock_data", "historical_runs.json")
if not os.path.exists(mock_data_path):
    st.error("Missing mock_data/historical_runs.json")
    st.stop()

with open(mock_data_path, "r") as f:
    history = json.load(f)

df = pd.DataFrame(history)

# === KPI Section ===
st.subheader("📌 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.markdown('<div class="card">', unsafe_allow_html=True)
col1.markdown(f"<div class='kpi'>{len(df)}</div>", unsafe_allow_html=True)
col1.markdown("<div class='label'>Total Runs</div>", unsafe_allow_html=True)
col1.markdown('</div>', unsafe_allow_html=True)

# ✅ Safe handling for missing 'status' column
col2.markdown('<div class="card">', unsafe_allow_html=True)
if 'status' in df.columns:
    success_pct = int((df['status'] == 'success').mean() * 100)
    col2.markdown(f"<div class='kpi'>{success_pct}%</div>", unsafe_allow_html=True)
    col2.markdown("<div class='label'>Success Rate</div>", unsafe_allow_html=True)
else:
    col2.markdown(f"<div class='kpi'>N/A</div>", unsafe_allow_html=True)
    col2.markdown("<div class='label'>Success Rate (missing)</div>", unsafe_allow_html=True)
col2.markdown('</div>', unsafe_allow_html=True)

# ✅ Safe handling for missing 'mode' column
col3.markdown('<div class="card">', unsafe_allow_html=True)
if 'mode' in df.columns:
    prod_runs = df[df["mode"] == "production"].shape[0]
    col3.markdown(f"<div class='kpi'>{prod_runs}</div>", unsafe_allow_html=True)
    col3.markdown("<div class='label'>Production Runs</div>", unsafe_allow_html=True)
else:
    col3.markdown(f"<div class='kpi'>N/A</div>", unsafe_allow_html=True)
    col3.markdown("<div class='label'>Production Runs (missing)</div>", unsafe_allow_html=True)
col3.markdown('</div>', unsafe_allow_html=True)

# === Charts ===
st.subheader("📈 Run Status Over Time")
if 'timestamp' in df.columns and 'status_score' in df.columns and 'status' in df.columns:
    line_chart = alt.Chart(df).mark_line(point=True).encode(
        x="timestamp:T",
        y=alt.Y("status_score:Q", title="Run Score (0–1)"),
        color="status:N"
    ).properties(height=300)
    st.altair_chart(line_chart, use_container_width=True)
else:
    st.warning("📉 Cannot render line chart — required columns missing.")

st.subheader("📊 Agent Success Rate")
agent_cols = [c for c in df.columns if c.startswith("agent_")]
if agent_cols:
    agent_scores = df[agent_cols].mean().reset_index()
    agent_scores.columns = ["Agent", "SuccessRate"]
    bar_chart = alt.Chart(agent_scores).mark_bar().encode(
        x=alt.X("Agent", sort="-y"),
        y="SuccessRate"
    ).properties(height=300)
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.warning("📊 No agent_* columns found to generate bar chart.")