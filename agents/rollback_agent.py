import datetime
import uuid
import subprocess
import json
from config import is_simulation_mode
from utils.azure_cosmos import log_session


class RollbackAgent:
    def run(self, azure_config: dict, app_name: str = "agentops-app") -> dict:
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()
        resource_group = azure_config.get("resource_group", "agentops-rg")

        if is_simulation_mode():
            result = {
                "status": "success",
                "restored": True,
                "previous_revision": "rev-001",
                "reason": "Simulated rollback succeeded",
                "critical": False,
                "skippable": True,
                "timestamp": timestamp,
                "output": "Rollback successful (simulated)"
            }
            result["input"] = {
                "repo_url": "N/A",
                "azure_config": str(azure_config),
                "app_name": app_name,
                "mode": execution_mode
            }
            log_session(session_id, "rollback", result)
            return result

        try:
            print("[PROD MODE] Attempting Azure rollback using Container Apps...")

            # Get container app revisions
            revisions_result = subprocess.run([
                "az", "containerapp", "revision", "list",
                "--name", app_name,
                "--resource-group", resource_group,
                "--query", "[].{name: name, createdTime: properties.createdTime, active: properties.active}",
                "--output", "json"
            ], capture_output=True, text=True, check=True)
            
            revisions = json.loads(revisions_result.stdout)
            revisions.sort(key=lambda r: r["createdTime"], reverse=True)

            if len(revisions) < 2:
                result = {
                    "status": "error",
                    "restored": False,
                    "reason": "No previous revision available for rollback.",
                    "critical": False,
                    "skippable": True,
                    "timestamp": timestamp,
                    "output": "Rollback skipped due to lack of previous revision."
                }
            else:
                prev_revision = revisions[1]["name"]
                
                # Update traffic to route 100% to previous revision
                subprocess.run([
                    "az", "containerapp", "ingress", "traffic", "set",
                    "--name", app_name,
                    "--resource-group", resource_group,
                    "--revision-weight", f"{prev_revision}=100"
                ], check=True)

                result = {
                    "status": "success",
                    "restored": True,
                    "previous_revision": prev_revision,
                    "reason": "Rollback completed successfully.",
                    "critical": False,
                    "skippable": True,
                    "timestamp": timestamp,
                    "output": f"Rolled back to revision: {prev_revision}"
                }

        except subprocess.CalledProcessError as e:
            result = {
                "status": "error",
                "restored": False,
                "reason": f"Azure CLI error: {str(e)}",
                "critical": False,
                "skippable": True,
                "timestamp": timestamp,
                "output": "Rollback failed due to Azure CLI error."
            }

        # ✅ Input payload for logging
        result["input"] = {
            "repo_url": "N/A",
            "azure_config": str(azure_config),
            "app_name": app_name,
            "mode": execution_mode
        }

        log_session(session_id, "rollback", result)
        return result
