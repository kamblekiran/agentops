import uuid
import datetime
from config import is_simulation_mode
from utils.firebase_logger import log_session
from utils.gcp import deploy_to_cloud_run

class DeployAgent:
    def run(self, image_url, gcp_project):
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()

        # === Default Output Skeleton ===
        result = {
            "status": "unknown",
            "deployed_url": None,
            "reason": "Not started",
            "critical": False,
            "skippable": True,
            "timestamp": timestamp
        }

        if is_simulation_mode():
            print("[SIM MODE] DeployAgent returning mock result")
            result.update({
                "status": "success",
                "deployed_url": f"https://{gcp_project}.cloudrun.simulated.app",
                "reason": "Mock deployment successful",
                "critical": False,
                "skippable": False
            })
        else:
            try:
                if not image_url or not image_url.startswith("gcr.io"):
                    result.update({
                        "status": "error",
                        "reason": f"Invalid or missing image URL: {image_url}",
                        "critical": False,
                        "skippable": True
                    })
                else:
                    deployed_url = deploy_to_cloud_run(image_url, gcp_project)
                    result.update({
                        "status": "success",
                        "deployed_url": deployed_url,
                        "reason": "Deployment successful",
                        "critical": False,
                        "skippable": False
                    })

            except Exception as e:
                result.update({
                    "status": "error",
                    "reason": f"Deploy failed: {str(e)}",
                    "deployed_url": None,
                    "critical": False,  # allow pipeline to continue
                    "skippable": True
                })

        # === Required input block ===
        result["input"] = {
            "image_url": image_url,
            "gcp_project": gcp_project,
            "mode": execution_mode
        }

        # === Final Logging ===
        log_session(session_id, "deploy", result)
        return result
