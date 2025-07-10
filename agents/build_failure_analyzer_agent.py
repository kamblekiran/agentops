import datetime
import uuid
from config import is_simulation_mode
from utils.azure_openai import azure_openai_prompt
from utils.azure_cosmos import log_session

class BuildFailureAnalyzerAgent:
    def run(self, build_logs: str, repo_url: str = "") -> dict:
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"

        # Define consistent structure with all expected fields
        default_result = {
            "status": "unknown",
            "root_cause": "N/A",
            "recommendations": "N/A",
            "step_failed": "N/A",
            "confidence": "low",
            "llm_analysis": "",
            "critical": False,
            "skippable": True,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        prompt = None

        if is_simulation_mode():
            result = default_result | {
                "status": "success",
                "root_cause": "Missing Dockerfile in root directory.",
                "recommendations": "Ensure `Dockerfile` exists in the root and is correctly formatted.",
                "step_failed": "Docker Build",
                "confidence": "high",
                "llm_analysis": "Build failed due to missing Dockerfile..."
            }
        else:
            try:
                prompt = [{
                    "content": f"""
                    You are a Build Failure Analyzer AI agent.

                    Given the following build logs, analyze the root cause of the failure and suggest a precise resolution.
                    Return your analysis in the following format:

                    ---
                    Step Failed: <step or phase name>
                    Issue: <summary of the root cause>
                    Fix Recommendation: <clear, actionable fix>
                    Confidence: <low / medium / high>
                    ---

                    Build Logs:
                    {build_logs}
                    (Repo: {repo_url})
                    """
                }]

                raw_response = azure_openai_prompt(prompt)
                parsed = self._parse_response(raw_response)

                result = default_result | {
                    "status": "success",
                    "root_cause": parsed.get("Issue", "N/A"),
                    "recommendations": parsed.get("Fix Recommendation", "N/A"),
                    "step_failed": parsed.get("Step Failed", "N/A"),
                    "confidence": parsed.get("Confidence", "low"),
                    "llm_analysis": raw_response
                }
            except Exception as e:
                result = default_result | {
                    "status": "error",
                    "root_cause": "Unparsed",
                    "recommendations": "LLM failed to generate actionable feedback.",
                    "step_failed": "Unknown",
                    "confidence": "low",
                    "llm_analysis": str(e)
                }

        # Ensure consistent logging shape
        log_session(session_id, "build_failure_analyzer", {
            "input": {
                "repo_url": repo_url,
                "mode": execution_mode,
                "build_logs": build_logs[:300] + "..." if len(build_logs) > 300 else build_logs,
                "prompt_used": prompt or "N/A"
            },
            "output": result,
            "status": result["status"],
            "critical": result["critical"]
        })

        return result

    def _parse_response(self, response: str) -> dict:
        result = {}
        for line in response.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result
