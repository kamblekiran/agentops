import os
import datetime
import tempfile
import subprocess
import uuid
import shutil
from github import Github
from config import is_simulation_mode
from utils.azure_openai import azure_openai_prompt
from utils.azure_cosmos import log_session
from dotenv import load_dotenv

load_dotenv()

class TestWriterAgent:
    def run(self, repo_url: str) -> dict:
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()
        generated_tests = []
        coverage_percent = "0%"
        coverage_output = ""
        note = ""

        if is_simulation_mode():
            print("[SIM MODE] Returning mock output for TestWriterAgent")
            result = {
                "status": "success",
                "generated_tests": ["test_login.py", "test_api.py"],
                "coverage_increase": "12%",
                "timestamp": timestamp,
                "critical": False,
                "skippable": False,
                "output": "Simulated test generation successful.",
                "input": {"repo_url": repo_url, "mode": execution_mode}
            }
            log_session(session_id, "test_writer", result)
            return result

        # Try to extract real repo structure for better LLM prompting
        file_list_text = ""
        try:
            from utils.github import validate_and_clone_repo
            local_repo_path = validate_and_clone_repo(repo_url)
            for root, _, files in os.walk(local_repo_path):
                for file in files:
                    if file.endswith(".py") and "test" not in file:
                        relative_path = os.path.relpath(os.path.join(root, file), local_repo_path)
                        file_list_text += f"- {relative_path}\n"
        except Exception as e:
            note += f"⚠️ Repo scan failed: {str(e)}\n"

        # Build LLM prompt
        prompt = [{
            "content": f"""
You are a senior QA engineer. Write Python `unittest` test cases for the following GitHub repo:

Repository: {repo_url}
Files:
{file_list_text or '[Repo structure unavailable]'}

- Use unittest.TestCase
- Include at least 3 tests
- Focus on error handling, edge cases, and expected behavior
- Output only a Python file named `test_generated.py`
            """
        }]

        try:
            print("[PROD MODE] Generating real test code...")
            test_code = azure_openai_prompt(prompt)

            # Sanity check: is it valid Python?
            try:
                compile(test_code, "<string>", "exec")
            except Exception as e:
                note += f"⚠️ Generated test code has syntax errors: {str(e)}\n"
                test_code = "# Invalid test code generated.\n"

            # Push to GitHub if token is set
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                note += "⚠️ GITHUB_TOKEN missing — skipping push to GitHub.\n"
            else:
                g = Github(github_token)
                repo_full_name = repo_url.replace("https://github.com/", "").replace(".git", "")
                repo = g.get_repo(repo_full_name)

                # Prepare temporary test directory
                with tempfile.TemporaryDirectory() as tmpdir:
                    test_dir = os.path.join(tmpdir, "tests")
                    os.makedirs(test_dir, exist_ok=True)
                    test_file_path = os.path.join(test_dir, "test_generated.py")
                    with open(test_file_path, "w") as f:
                        f.write(test_code)
                    generated_tests.append("tests/test_generated.py")

                    # Push to GitHub
                    path_in_repo = "tests/test_generated.py"
                    try:
                        existing = repo.get_contents(path_in_repo)
                        repo.update_file(
                            path_in_repo,
                            "🔁 Update auto-generated tests",
                            test_code,
                            existing.sha
                        )
                    except Exception:
                        repo.create_file(
                            path_in_repo,
                            "🔧 Add auto-generated tests",
                            test_code
                        )

                    # Run tests and measure coverage
                    try:
                        subprocess.run(["pip", "install", "coverage"], check=True)
                        subprocess.run(["coverage", "run", "-m", "unittest", "discover", "-s", "tests"], cwd=tmpdir, check=True)
                        proc = subprocess.run(["coverage", "report"], cwd=tmpdir, capture_output=True, text=True)
                        coverage_output = proc.stdout
                        for line in coverage_output.splitlines():
                            if "TOTAL" in line and "%" in line:
                                coverage_percent = line.split()[-1]
                    except subprocess.CalledProcessError as e:
                        note += f"⚠️ Test run failed: {e.stderr or str(e)}\n"

        except Exception as e:
            note += f"⚠️ Unexpected error: {str(e)}\n"

        result = {
            "status": "success",
            "generated_tests": generated_tests,
            "coverage_increase": coverage_percent,
            "timestamp": timestamp,
            "critical": False,
            "skippable": False,
            "output": (coverage_output or "No coverage output.") + "\n" + note,
            "input": {
                "repo_url": repo_url,
                "mode": execution_mode,
                "prompt_used": prompt
            }
        }

        log_session(session_id, "test_writer", result)
        return result
