import datetime
import json
import uuid
import os
import subprocess
from typing import Dict, Any
from config import is_simulation_mode
from utils.azure_cosmos import log_session
from utils.azure import get_container_app_logs

class MonitorAgent:
    def run(
        self,
        azure_config: dict,
        app_name: str = None,
        resource_group: str = None
    ) -> Dict[str, Any]:
        """
        Monitors one or all Azure Container Apps in the given resource group.
        Uses Azure CLI for monitoring.
        """
        execution_mode = "simulation" if is_simulation_mode() else "production"
        timestamp = datetime.datetime.utcnow().isoformat()
        results: Dict[str, Any] = {}
        
        if resource_group is None:
            resource_group = azure_config.get("resource_group", "agentops-rg")

        # Determine list of services to monitor
        apps = []
        if is_simulation_mode():
            apps = [app_name] if app_name else ["simulated-app"]
        else:
            try:
                # List container apps in resource group
                result = subprocess.run([
                    "az", "containerapp", "list",
                    "--resource-group", resource_group,
                    "--query", "[].name",
                    "--output", "tsv"
                ], capture_output=True, text=True, check=True)
                
                all_apps = result.stdout.strip().split('\n') if result.stdout.strip() else []
                for app in all_apps:
                    if app_name is None or app == app_name:
                        apps.append(app)
                        
            except subprocess.CalledProcessError as e:
                session_id = str(uuid.uuid4())
                error_result = {
                    "status": "error",
                    "summary": "Failed to list container apps",
                    "reason": str(e),
                    "traffic_status": "N/A",
                    "errors": [str(e)],
                    "last_deployed_revision": "unknown",
                    "timestamp": timestamp,
                    "input": {"azure_config": str(azure_config), "app_name": app_name, "mode": execution_mode}
                }
                log_session(session_id, "monitor", error_result)
                return {"error": error_result}

        # Describe and collect status for each app
        for app in apps:
            session_id = str(uuid.uuid4())
            
            if is_simulation_mode():
                result = {
                    "status": "success",
                    "summary": "Simulated monitoring - all healthy",
                    "reason": None,
                    "traffic_status": "100% → latest",
                    "errors": [],
                    "last_deployed_revision": "rev-001",
                    "timestamp": timestamp,
                    "input": {"azure_config": str(azure_config), "app_name": app, "mode": execution_mode}
                }
            else:
                try:
                    # Get container app details
                    app_result = subprocess.run([
                        "az", "containerapp", "show",
                        "--name", app,
                        "--resource-group", resource_group,
                        "--query", "{provisioningState: properties.provisioningState, fqdn: properties.configuration.ingress.fqdn, replicas: properties.template.scale}",
                        "--output", "json"
                    ], capture_output=True, text=True, check=True)
                    
                    app_info = json.loads(app_result.stdout)
                    provisioning_state = app_info.get("provisioningState", "Unknown")
                    fqdn = app_info.get("fqdn", "N/A")
                    
                    errors = []
                    if provisioning_state != "Succeeded":
                        errors.append(f"Provisioning state: {provisioning_state}")
                    
                    # Get logs for additional health info
                    logs = get_container_app_logs(app, azure_config)
                    if "error" in logs.lower() or "exception" in logs.lower():
                        errors.append("Errors found in recent logs")
                    
                    summary = "All conditions passed." if not errors else f"{len(errors)} issue(s) detected."
                    
                    result = {
                        "status": "success" if not errors else "error",
                        "summary": summary,
                        "reason": None if not errors else "; ".join(errors),
                        "traffic_status": f"FQDN: {fqdn}",
                        "errors": errors,
                        "last_deployed_revision": "latest",
                        "timestamp": timestamp,
                        "input": {"azure_config": str(azure_config), "app_name": app, "mode": execution_mode}
                    }
                except subprocess.CalledProcessError as e:
                    result = {
                        "status": "error",
                        "summary": "Failed to describe container app",
                        "reason": str(e),
                        "traffic_status": "N/A",
                        "errors": [str(e)],
                        "last_deployed_revision": "unknown",
                        "timestamp": timestamp,
                        "input": {"azure_config": str(azure_config), "app_name": app, "mode": execution_mode}
                    }
                    
            # Log and store result
            log_session(session_id, "monitor", result)
            results[app] = result

        return results
