import datetime
import uuid
from config import is_simulation_mode
from utils.gemini import gemini_prompt
from utils.firebase_logger import fetch_agent_history, log_session

class SREAgent:
    def run(self, repo_url: str, gcp_project: str) -> dict:
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()

        prompt = None  # Predefine safely

        if is_simulation_mode():
            result = {
                "status": "success",
                "summary": "The service had 3 rollbacks and 5 deployments in the last 24h. Frequent redeployments signal instability.",
                "root_cause": "Likely due to missing integration tests.",
                "recommended_actions": "Add smoke tests, enforce health checks, and limit rollout to 10% traffic before scaling.",
                "risk_score": 82,
                "critical": True,
                "skippable": False,
                "timestamp": timestamp,
                "output": "Simulated stability analysis complete.",
                "input": {
                    "repo_url": repo_url,
                    "gcp_project": gcp_project,
                    "mode": execution_mode
                }
            }
            log_session(session_id, "sre", result)
            return result

        try:
            print("[PROD MODE] Running SREAgent trend analysis...")

            monitor_logs = fetch_agent_history(agent="monitor", limit=10)
            deploy_logs = fetch_agent_history(agent="deploy", limit=10)
            rollback_logs = fetch_agent_history(agent="rollback", limit=10)

            def extract_entries(logs, key):
                return [log.get("data", log).get(key, "") for log in logs]

            monitor_summary = "\n".join(extract_entries(monitor_logs, "summary"))
            deploy_summary = "\n".join(extract_entries(deploy_logs, "status"))
            rollback_summary = "\n".join(extract_entries(rollback_logs, "status"))

            fake_metrics = """
            CPU usage: spike at 85% during deploy 3
            Memory: stable around 60%
            Request latency: 99th percentile hit 1200ms
            5xx error rate: 2% during rollout of rev-002
            """

            prompt = [{
                "role": "user",
                "parts": [f"""
                You are a production SRE assistant. Use the logs below to identify trends and generate a risk report.

                🧠 Context:
                - GitHub Repo: {repo_url}
                - GCP Project: {gcp_project}

                📉 Deployments:
                {deploy_summary}

                🚨 Rollbacks:
                {rollback_summary}

                📈 Monitoring Logs:
                {monitor_summary}

                📊 Simulated Metrics:
                {fake_metrics}

                🎯 Your job:
                1. Summarize current system stability (plain English)
                2. Explain the most likely root cause if issues were detected
                3. Recommend actions for stability
                4. Assign a risk score (0–100) and mark if critical

                Respond in this structured format:
                ---
                Summary: <...>
                Root Cause: <...>
                Recommended Actions: <...>
                Risk Score: <int 0–100>
                Critical: <true/false>
                ---
                """]
            }]

            response = gemini_prompt(prompt)

            def safe_extract(key, fallback="N/A"):
                try:
                    return response.split(f"{key}:")[1].split("\n", 1)[0].strip()
                except Exception:
                    return fallback

            summary = safe_extract("Summary")
            root_cause = safe_extract("Root Cause")
            recommended = safe_extract("Recommended Actions")
            risk_score = safe_extract("Risk Score", "0")
            critical_flag = "true" in response.lower()

            result = {
                "status": "success",
                "summary": summary,
                "root_cause": root_cause,
                "recommended_actions": recommended,
                "risk_score": int(risk_score) if risk_score.isdigit() else 0,
                "critical": critical_flag,
                "skippable": False,
                "timestamp": timestamp,
                "output": response,
                "input": {
                    "repo_url": repo_url,
                    "gcp_project": gcp_project,
                    "mode": execution_mode,
                    "prompt_used": prompt
                }
            }

        except Exception as e:
            result = {
                "status": "error",
                "summary": "SRE analysis failed",
                "root_cause": "N/A",
                "recommended_actions": "N/A",
                "risk_score": 0,
                "critical": False,
                "skippable": True,
                "timestamp": timestamp,
                "output": f"Exception: {str(e)}",
                "input": {
                    "repo_url": repo_url,
                    "gcp_project": gcp_project,
                    "mode": execution_mode
                }
            }

        log_session(session_id, "sre", result)
        return result
