import uuid
import datetime
from utils.azure import build_container
from utils.azure_cosmos import log_session
from config import is_simulation_mode, get_azure_config

class BuildAgent:
    def run(self, repo_url, azure_config=None):
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        
        if azure_config is None:
            azure_config = get_azure_config()

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
            registry = azure_config.get("container_registry", "agentopssim")
            result = default_result | {
                "status": "success",
                "image_url": f"{registry}.azurecr.io/example-image:latest",
                "reason": "Simulated build success",
                "critical": False
            }
        else:
            try:
                image_url = build_container(repo_url, azure_config)
                result = default_result | {
                    "status": "success",
                    "image_url": image_url,
                    "reason": "Build succeeded",
                    "critical": False
                }
            except Exception as e:
                result = default_result | {
                    "status": "error",
                    "reason": f"Build failed: {str(e)}",
                    "critical": True
                }

        # Add consistent input block
        log_session(session_id, "build", {
            "input": {
                "repo_url": repo_url or "N/A",
                "azure_config": str(azure_config) or "N/A",
                "mode": execution_mode
            },
            "output": result,
            "status": result["status"],
            "critical": result["critical"]
        })

        return result
