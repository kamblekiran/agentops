import uuid
import datetime
from utils.gcp import build_container
from utils.firebase_logger import log_session
from config import is_simulation_mode

class BuildAgent:
    def run(self, repo_url, gcp_project):
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"

        # Predefine common structured result
        default_result = {
            "status": "unknown",
            "image_url": None,
            "reason": "N/A",
            "llm_analysis": "N/A",  # placeholder to align with other agents
            "critical": True,
            "skippable": False,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        if is_simulation_mode():
            result = default_result | {
                "status": "success",
                "image_url": f"gcr.io/{gcp_project}/example-image:latest",
                "reason": "Simulated build success",
                "critical": False
            }
        else:
            try:
                image_url = build_container(repo_url, gcp_project)
                result = default_result | {
                    "status": "success",
                    "image_url": image_url,
                    "reason": "Build succeeded",
                    "critical": False
                }
            except Exception as e:
                result = default_result | {
                    "status": "success",
                    "reason": f"Build failed: {str(e)}",
                    "critical": True
                }

        # Add consistent input block
        log_session(session_id, "build", {
            "input": {
                "repo_url": repo_url or "N/A",
                "gcp_project": gcp_project or "N/A",
                "mode": execution_mode
            },
            "output": result,
            "status": result["status"],
            "critical": result["critical"]
        })

        return result
