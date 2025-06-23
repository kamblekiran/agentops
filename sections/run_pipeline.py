import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import uuid
from utils.firebase_logger import fetch_agent_history, log_session
from agents.code_reviewer_agent import CodeReviewerAgent
from agents.test_writer_agent import TestWriterAgent
from agents.regression_checker_agent import RegressionCheckerAgent
from agents.builder_agent import BuildAgent
from agents.deployer_agent import DeployAgent
from agents.monitor_agent import MonitorAgent
from agents.rollback_agent import RollbackAgent
from agents.sre_agent import SREAgent
from agents.build_failure_analyzer_agent import BuildFailureAnalyzerAgent

st.title("🔹 Run Pipeline")
st.markdown("## 🚀 Run Full Agent Pipeline")

# === Inputs ===
repo_url = st.text_input("🔗 GitHub Repo URL", placeholder="https://github.com/user/repo")
gcp_project = st.text_input("☁️ GCP Project ID", placeholder="your-gcp-project")
st.markdown(f"<b>Execution Mode:</b> <code style='color:limegreen'>{st.session_state.get('mode', 'SIMULATION').upper()}</code>", unsafe_allow_html=True)

# === Load History ===
history_options = {
    "code_review": fetch_agent_history(agent="code_review", limit=5),
    "test_writer": fetch_agent_history(agent="test_writer", limit=5),
    "regression_check": fetch_agent_history(agent="regression_check", limit=5),
    "build": fetch_agent_history(agent="build", limit=5),
    "build_failure_analyzer": fetch_agent_history(agent="build_failure_analyzer", limit=5),
    "deploy": fetch_agent_history(agent="deploy", limit=5),
    "monitor": fetch_agent_history(agent="monitor", limit=5),
    "rollback": fetch_agent_history(agent="rollback", limit=5),
    "sre": fetch_agent_history(agent="sre", limit=5),
}

agent_outputs = {}
STATUS_ICONS = {
    "pending": "⏳", "running": "🔄", "success": "✅", "error": "❌"
}

# === Pipeline Execution ===
if st.button("▶️ Run Full Agent Pipeline") and repo_url and gcp_project:
    session_id = str(uuid.uuid4())
    with st.spinner("⏱️ Running all agents..."):

        output = CodeReviewerAgent().run(repo_url)
        log_session(session_id, "code_review", output)
        agent_outputs["code_review"] = output

        output = TestWriterAgent().run(repo_url)
        log_session(session_id, "test_writer", output)
        agent_outputs["test_writer"] = output

        output = RegressionCheckerAgent().run(repo_url)
        log_session(session_id, "regression_check", output)
        agent_outputs["regression_check"] = output

        output = BuildAgent().run(repo_url, gcp_project)
        log_session(session_id, "build", output)
        agent_outputs["build"] = output

        if output.get("status") == "error" and "logs" in output:
            failure_output = BuildFailureAnalyzerAgent().run(
                build_logs=output["logs"],
                repo_url=repo_url
            )
            log_session(session_id, "build_failure_analyzer", failure_output)
            agent_outputs["build_failure_analyzer"] = failure_output

        if all([
            agent_outputs.get("code_review", {}).get("status") == "success",
            agent_outputs.get("test_writer", {}).get("status") == "success",
            agent_outputs.get("regression_check", {}).get("status") == "success",
            agent_outputs.get("build", {}).get("status") == "success"
        ]):
            image_url = agent_outputs["build"].get("image_url")
            if image_url:
                deploy_output = DeployAgent().run(image_url, gcp_project)
            else:
                deploy_output = {
                    "status": "error",
                    "reason": "Missing image_url from BuildAgent output",
                    "critical": True,
                    "skippable": False
                }
            log_session(session_id, "deploy", deploy_output)
            agent_outputs["deploy"] = deploy_output

            monitor_output = MonitorAgent().run(gcp_project)
            rollback_output = RollbackAgent().run(gcp_project)
            sre_output = SREAgent().run(repo_url, gcp_project)

            log_session(session_id, "monitor", monitor_output)
            log_session(session_id, "rollback", rollback_output)
            log_session(session_id, "sre", sre_output)

            agent_outputs["monitor"] = monitor_output
            agent_outputs["rollback"] = rollback_output
            agent_outputs["sre"] = sre_output
            st.success("✅ Pipeline completed successfully!")
            st.balloons()

# === Output Viewer ===
def render_output_block(title, agent_key):
    status = agent_outputs.get(agent_key, {}).get("status", "pending")
    icon = STATUS_ICONS.get(status, "⏳")
    with st.expander(f"{icon} {title}", expanded=False):
        if history_options.get(agent_key):
            selected = st.selectbox(
                f"📜 Past Runs — {agent_key.replace('_', ' ').title()}",
                options=history_options[agent_key],
                format_func=lambda x: f"{x['timestamp']} ({x['session_id'][:8]})",
                key=f"{agent_key}_history"
            )
            st.markdown("### 🔁 Replayed Output")
            output = selected.get("data", selected)
        elif agent_key in agent_outputs:
            st.markdown("### ✅ Latest Output")
            output = agent_outputs[agent_key]
        else:
            st.info("No output yet.")
            return

        if agent_key == "build_failure_analyzer":
            st.markdown("#### 🔍 **Failure Diagnosis Summary**")
            st.markdown(f"- **Root Cause**: `{output.get('root_cause', 'N/A')}`")
            st.markdown("#### 💡 **Recommendations**")
            st.code(output.get("recommendations", "No suggestions"), language="markdown")
            st.markdown("#### 📝 **Detailed LLM Analysis**")
            st.code(output.get("llm_analysis", "No analysis available."), language="markdown")
        else:
            st.json(output)

# === Render Blocks ===
render_output_block("🧠 Code Reviewer", "code_review")
render_output_block("🧪 Test Writer", "test_writer")
render_output_block("🔁 Regression Checker", "regression_check")
render_output_block("🏗️ Builder", "build")
render_output_block("📉 Build Failure Analysis", "build_failure_analyzer")
render_output_block("🚀 Deployer", "deploy")
render_output_block("📈 Monitor", "monitor")
render_output_block("↩️ Rollback", "rollback")
render_output_block("🛡️ SRE Audit", "sre")
