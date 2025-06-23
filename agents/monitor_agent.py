import datetime
import json
import uuid
import os
from typing import Dict, Any
from config import is_simulation_mode
from utils.firebase_logger import log_session
from google.cloud import run_v2
from google.api_core.exceptions import GoogleAPICallError

class MonitorAgent:
    def run(
        self,
        gcp_project: str,
        service_name: str = None,
        region: str = "us-central1"
    ) -> Dict[str, Any]:
        """
        Monitors one or all Cloud Run services in the given project and region.
        Uses the Google Cloud Run Python client instead of CLI.
        """
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()
        results: Dict[str, Any] = {}

        # Determine list of services to monitor
        services = []
        if is_simulation_mode():
            services = [service_name] if service_name else ["simulated-service"]
        else:
            client = run_v2.ServicesClient()
            parent = f"projects/{gcp_project}/locations/{region}"
            try:
                response = client.list_services(parent=parent)
                for svc_obj in response:
                    name = os.path.basename(svc_obj.name)
                    if service_name is None or name == service_name:
                        services.append(name)
            except GoogleAPICallError as e:
                session_id = str(uuid.uuid4())
                error_result = {
                    "status": "error",
                    "summary": "Failed to list services",
                    "reason": str(e),
                    "traffic_status": "N/A",
                    "errors": [str(e)],
                    "last_deployed_revision": "unknown",
                    "timestamp": timestamp,
                    "input": {"gcp_project": gcp_project, "service_name": service_name, "mode": execution_mode}
                }
                log_session(session_id, "monitor", error_result)
                return {"error": error_result}

        # Describe and collect status for each service
        client = run_v2.ServicesClient()
        for svc in services:
            session_id = str(uuid.uuid4())
            full_name = f"projects/{gcp_project}/locations/{region}/services/{svc}"
            try:
                service = client.get_service(name=full_name)
                # Use direct attributes
                conditions = list(service.conditions)
                traffic = list(service.traffic)
                last_ready = service.latest_ready_revision

                # errors = [c.message for c in conditions if c.status != run_v2.Condition.State.STATE_TRUE]
                errors = [
                            c.message for c in conditions
                            if c is not None and hasattr(c, "status") and c.status != run_v2.Condition.State.TRUE
            ]

                traffic_info = ", ".join(f"{t.percent}% → {t.revision}" for t in traffic)
                summary = "All conditions passed." if not errors else f"{len(errors)} issue(s) detected."

                result = {
                    "status": "success" if not errors else "error",
                    "summary": summary,
                    "reason": None if not errors else "; ".join(errors),
                    "traffic_status": traffic_info or "No traffic info",
                    "errors": errors,
                    "last_deployed_revision": last_ready,
                    "timestamp": timestamp,
                    "input": {"gcp_project": gcp_project, "service_name": svc, "mode": execution_mode}
                }
            except GoogleAPICallError as e:
                result = {
                    "status": "success",
                    "summary": "Failed to describe service",
                    "reason": str(e),
                    "traffic_status": "N/A",
                    "errors": [str(e)],
                    "last_deployed_revision": "unknown",
                    "timestamp": timestamp,
                    "input": {"gcp_project": gcp_project, "service_name": svc, "mode": execution_mode}
                }
            # Log and store result
            log_session(session_id, "monitor", result)
            results[svc] = result

        return results
