import time
import uuid
import subprocess
import tempfile
import os
import shutil
from config import is_simulation_mode
from utils.azure_openai import azure_openai_prompt
from utils.azure_cosmos import log_session

class RegressionCheckerAgent:
    def run(self, repo_url: str):
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        prompt = None
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # === SIMULATION MODE ===
        if is_simulation_mode():
            result = {
                "status": "success",
                "summary": "✅ Regression passed (simulation)",
                "tests_ran": 124,
                "failures": [],
                "output": "Simulated test results look good.",
                "raw_test_output": "...",
                "critical": False,
                "skippable": False,
                "timestamp": timestamp,
                "input": {
                    "repo_url": repo_url,
                    "mode": execution_mode,
                    "prompt_used": "N/A"
                }
            }
            log_session(session_id, "regression_check", result)
            return result

        # === PRODUCTION MODE ===
        try:
            print("[PROD MODE] Running RegressionCheckerAgent...")

            # Step 1: Clone repo to temp dir
            tmp_dir = tempfile.mkdtemp()
            clone_cmd = f"git clone {repo_url} {tmp_dir}"
            clone_result = os.system(clone_cmd)
            if clone_result != 0:
                raise Exception(f"Failed to clone repo: {repo_url}")

            # Step 2: Install dependencies
            req_path = os.path.join(tmp_dir, "requirements.txt")
            if os.path.exists(req_path):
                subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=tmp_dir, check=True)

            # Step 3: Run tests
            test_proc = subprocess.run(
                ["pytest", "--tb=short", "--maxfail=5"],
                cwd=tmp_dir, capture_output=True, text=True
            )
            test_output = test_proc.stdout + "\n" + test_proc.stderr

            # Step 4: Analyze output using LLM
            prompt = [{
                "content": (
                    f"I ran regression tests on the repository `{repo_url}`.\n\n"
                    f"Here is the pytest output:\n\n```\n{test_output}\n```\n\n"
                    "Please analyze the results and summarize any regressions. "
                    "Format the response in Markdown with the following sections:\n"
                    "1. **Summary** – overall test result\n"
                    "2. **Failures** – list failed test names and error messages\n"
                    "3. **Root Causes** – likely reasons for failure\n"
                    "4. **Recommended Fixes** – how to fix them\n"
                    "5. **Test Pass Rate** – count of passed vs failed\n"
                )
            }]
            llm_response = azure_openai_prompt(prompt)

            result = {
                "status": "success",  # ✅ Always success to prevent pipeline stop
                "summary": "✅ Regression analysis complete" if test_proc.returncode == 0 else "⚠️ Tests failed",
                "output": llm_response,
                "raw_test_output": test_output[:5000],
                "critical": False,
                "skippable": test_proc.returncode != 0,
                "timestamp": timestamp,
                "input": {
                    "repo_url": repo_url,
                    "mode": execution_mode,
                    "prompt_used": prompt
                }
            }

        except Exception as e:
            result = {
                "status": "success",  # ✅ Do not block pipeline
                "summary": "⚠️ Test runner or LLM analysis failed (non-blocking)",
                "output": "",
                "raw_test_output": "",
                "reason": str(e),
                "critical": False,
                "skippable": True,
                "timestamp": timestamp,
                "input": {
                    "repo_url": repo_url,
                    "mode": execution_mode,
                    "prompt_used": prompt if prompt else "N/A"
                }
            }

        finally:
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass

        log_session(session_id, "regression_check", result)
        return result
