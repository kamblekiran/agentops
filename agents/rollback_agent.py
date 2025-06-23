import datetime
import uuid
from config import is_simulation_mode
from utils.firebase_logger import log_session
from google.cloud import run_v2
from google.api_core.exceptions import GoogleAPIError


class RollbackAgent:
    def run(self, gcp_project: str, service_name: str = "agentops-app", region: str = "us-central1") -> dict:
        session_id = str(uuid.uuid4())
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()

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
                "gcp_project": gcp_project,
                "service_name": service_name,
                "mode": execution_mode
            }
            log_session(session_id, "rollback", result)
            return result

        try:
            print("[PROD MODE] Attempting GCP rollback using Cloud Run API...")

            client = run_v2.ServicesClient()
            parent = f"projects/{gcp_project}/locations/{region}/services/{service_name}"
            
            # List revisions (desc order)
            revisions_client = run_v2.RevisionsClient()
            revisions = list(revisions_client.list_revisions(parent=f"projects/{gcp_project}/locations/{region}"))
            revisions = [r for r in revisions if r.metadata.name.startswith(service_name)]
            revisions.sort(key=lambda r: r.metadata.create_time, reverse=True)

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
                prev_revision = revisions[1].metadata.name
                service = client.get_service(name=parent)

                service.traffic = [
                    run_v2.TrafficTarget(
                        type_=run_v2.TrafficTargetAllocationType.REVISION,
                        revision=prev_revision,
                        percent=100
                    )
                ]

                update_operation = client.update_service(service=service)
                update_operation.result()  # Wait for it

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

        except GoogleAPIError as e:
            result = {
                "status": "error",
                "restored": False,
                "reason": f"API error: {e.message if hasattr(e, 'message') else str(e)}",
                "critical": False,
                "skippable": True,
                "timestamp": timestamp,
                "output": "Rollback failed due to API error."
            }

        # ✅ Input payload for logging
        result["input"] = {
            "repo_url": "N/A",
            "gcp_project": gcp_project,
            "service_name": service_name,
            "mode": execution_mode
        }

        log_session(session_id, "rollback", result)
        return result
