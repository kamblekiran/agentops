import subprocess
import tempfile
import shutil
import os
from urllib.parse import urlparse
from config import is_simulation_mode, get_azure_config
from utils.github import validate_and_clone_repo


def _extract_repo_name(repo_url: str) -> str:
    """
    Extracts the repository name from a GitHub URL.
    E.g., https://github.com/user/repo.git -> repo
    """
    path = urlparse(repo_url).path
    name = os.path.basename(path)
    return name.replace('.git', '')


def build_container(repo_url: str, azure_config: dict) -> str:
    """
    Builds a Docker image for the given repository and pushes it to Azure Container Registry.
    The image and service names are derived from the repository name.
    """
    if is_simulation_mode():
        repo_name = _extract_repo_name(repo_url)
        registry = azure_config.get("container_registry", "agentopssim")
        return f"{registry}.azurecr.io/{repo_name}:latest"

    repo_path = None
    try:
        repo_path = validate_and_clone_repo(repo_url)
        repo_name = _extract_repo_name(repo_url)
        registry = azure_config["container_registry"]
        image_url = f"{registry}.azurecr.io/{repo_name}:latest"

        # Login to Azure Container Registry
        subprocess.run([
            "az", "acr", "login",
            "--name", registry
        ], check=True)

        # Build and push image
        subprocess.run([
            "az", "acr", "build",
            "--registry", registry,
            "--image", f"{repo_name}:latest",
            repo_path
        ], check=True)

        return image_url
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Build failed: {e}")
    finally:
        if repo_path:
            shutil.rmtree(repo_path, ignore_errors=True)


def deploy_to_container_apps(
    image_url: str,
    azure_config: dict,
    app_name: str = None
) -> str:
    """
    Deploys the specified image to Azure Container Apps.
    Returns the public URL of the deployed service.
    """

    def _sanitize_app_name(name: str) -> str:
        """
        Converts any invalid app name to Azure Container Apps-compatible format.
        - Lowercase, alphanumeric and hyphens only
        - Max 32 characters
        - Must start/end with alphanumeric
        """
        sanitized = name.replace("_", "-").lower()
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
        sanitized = sanitized.strip('-')
        return sanitized[:32]

    if is_simulation_mode():
        repo_name = image_url.split('/')[-1].split(':')[0]
        return f"https://{repo_name}-sim.azurecontainerapps.io"

    # Derive and sanitize app name from image if not provided
    if not app_name:
        raw_name = image_url.split('/')[-1].split(":")[0]
        app_name = _sanitize_app_name(raw_name)

    try:
        resource_group = azure_config["resource_group"]
        location = azure_config["location"]
        
        # Create container app environment if it doesn't exist
        env_name = f"{app_name}-env"
        subprocess.run([
            "az", "containerapp", "env", "create",
            "--name", env_name,
            "--resource-group", resource_group,
            "--location", location
        ], check=False)  # Don't fail if already exists

        # Deploy container app
        subprocess.run([
            "az", "containerapp", "create",
            "--name", app_name,
            "--resource-group", resource_group,
            "--environment", env_name,
            "--image", image_url,
            "--target-port", "8501",
            "--ingress", "external",
            "--query", "properties.configuration.ingress.fqdn",
            "--output", "tsv"
        ], check=True)

        # Get the FQDN
        result = subprocess.run([
            "az", "containerapp", "show",
            "--name", app_name,
            "--resource-group", resource_group,
            "--query", "properties.configuration.ingress.fqdn",
            "--output", "tsv"
        ], capture_output=True, text=True, check=True)

        fqdn = result.stdout.strip()
        return f"https://{fqdn}"
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Deploy failed: {e}")


def get_container_app_logs(app_name: str, azure_config: dict) -> str:
    """
    Retrieves logs from Azure Container Apps.
    """
    if is_simulation_mode():
        return "Simulated Azure Container Apps logs"

    try:
        resource_group = azure_config["resource_group"]
        
        result = subprocess.run([
            "az", "containerapp", "logs", "show",
            "--name", app_name,
            "--resource-group", resource_group,
            "--follow", "false",
            "--tail", "100"
        ], capture_output=True, text=True, check=True)

        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Failed to retrieve logs: {e}"


def scale_container_app(app_name: str, azure_config: dict, min_replicas: int = 0, max_replicas: int = 10) -> bool:
    """
    Scales Azure Container App.
    """
    if is_simulation_mode():
        return True

    try:
        resource_group = azure_config["resource_group"]
        
        subprocess.run([
            "az", "containerapp", "update",
            "--name", app_name,
            "--resource-group", resource_group,
            "--min-replicas", str(min_replicas),
            "--max-replicas", str(max_replicas)
        ], check=True)

        return True
    except subprocess.CalledProcessError:
        return False