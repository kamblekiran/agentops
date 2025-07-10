import datetime
import uuid
from config import is_simulation_mode
from utils.azure_openai import azure_openai_prompt
from utils.azure_cosmos import log_session

class CodeReviewerAgent:
    def run(self, repo_url: str) -> dict:
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()
        prompt = None

        # === Default result structure ===
        result = {
            "status": "unknown",
            "review": "N/A",
            "issues_found": 0,
            "llm_analysis": "N/A",
            "critical": False,
            "skippable": False,
            "timestamp": timestamp
        }

        if is_simulation_mode():
            print("[SIM MODE] Returning mock output for CodeReviewerAgent")
            result.update({
                "status": "success",
                "review": "This is a simulated code review summary.",
                "issues_found": 3,
                "llm_analysis": "Simulated output",
                "critical": False,
                "skippable": False
            })

        else:
            try:
                print("[PROD MODE] Running CodeReviewerAgent with real logic...")

                prompt = [{
                    "role": "user",
                    "content": f"""
                            You are an expert code reviewer AI assisting a developer in evaluating the code quality, security, maintainability, and documentation of a repository.

                            🔍 Review Scope:
                            - Repository URL: `{repo_url}`
                            - Programming language(s): Auto-detect or infer
                            - File types: Prioritize source files (.py, .js, .ts, .java, etc.) and test files
                            - Assume this is a full repository review unless a Pull Request ID is explicitly provided.

                            🎯 Objectives:
                            1. Identify **code quality issues**, style violations, duplication, or bad practices.
                            2. Detect **security vulnerabilities**, exposed secrets, or unsafe code patterns.
                            3. Highlight **architectural or design flaws** and suggest improvements.
                            4. Detect **missing docstrings**, poor comments, or confusing logic.
                            5. Recommend **test coverage improvements**, edge cases, or missing assertions.
                            6. Include **actionable suggestions** that a developer can quickly act on.
                            7. Provide a **summary risk score** (0–100) with reasoning.

                            💡 Output Format:
                            Respond in structured markdown with these sections:
                            - 🧠 Summary
                            - 🛑 Issues Detected
                            - ✅ Good Practices Observed
                            - 🛠️ Recommended Changes
                            - 📈 Risk Score (0–100) with reasoning

                            Respond in plain text.
                        """
                }]

                review = azure_openai_prompt(prompt)

                result.update({
                    "status": "success",
                    "review": review,
                    "llm_analysis": review,
                    "issues_found": 2,  # You can update this later by parsing
                    "critical": False,
                    "skippable": False
                })

            except Exception as e:
                print(f"[ERROR] CodeReviewerAgent failed: {e}")
                result.update({
                    "status": "error",
                    "review": "N/A",
                    "llm_analysis": "",
                    "issues_found": 0,
                    "reason": f"Code review failed: {e}",
                    "critical": False,  # Don't block the pipeline
                    "skippable": True
                })

        # === Logging ===
        log_session(session_id, "code_review", {
            "input": {
                "repo_url": repo_url or "N/A",
                "mode": execution_mode,
                "prompt_used": prompt if prompt else "N/A"
            },
            "output": result,
            "status": result["status"],
            "critical": result["critical"]
        })

        return result
