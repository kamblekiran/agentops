import subprocess
import tempfile
import shutil
import os
from urllib.parse import urlparse
from config import is_simulation_mode
from utils.github import validate_and_clone_repo


def _extract_repo_name(repo_url: str) -> str:
    """
    Extracts the repository name from a GitHub URL.
    E.g., https://github.com/user/repo.git -> repo
    """
    path = urlparse(repo_url).path
    name = os.path.basename(path)
    return name.replace('.git', '')


def build_container(repo_url: str, gcp_project: str) -> str:
    """
    Builds a Docker image for the given repository and pushes it to GCR.
    The image and service names are derived from the repository name.
    """
    if is_simulation_mode():
        repo_name = _extract_repo_name(repo_url)
        return f"gcr.io/{gcp_project}-sim/{repo_name}"

    repo_path = None
    try:
        repo_path = validate_and_clone_repo(repo_url)
        repo_name = _extract_repo_name(repo_url)
        image_url = f"gcr.io/{gcp_project}/{repo_name}"

        subprocess.run([
            "gcloud", "builds", "submit",
            "--tag", image_url,
            repo_path,
            "--project", gcp_project,
            "--quiet"
        ], check=True)

        return image_url
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Build failed: {e}")
    finally:
        if repo_path:
            shutil.rmtree(repo_path, ignore_errors=True)


def deploy_to_cloud_run(
    image_url: str,
    gcp_project: str,
    service_name: str = None,
    region: str = "us-central1"
) -> str:
    """
    Deploys the specified image to Cloud Run. Service name defaults to the image's repo name.
    Returns the public URL of the deployed service.
    """

    def _sanitize_service_name(name: str) -> str:
        """
        Converts any invalid service name (e.g., underscores) to Cloud Run-compatible format.
        - Lowercase, alphanumeric and hyphens only
        - Max 63 characters
        - Must start/end with alphanumeric
        """
        sanitized = name.replace("_", "-").lower()
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
        sanitized = sanitized.strip('-')
        return sanitized[:63]

    if is_simulation_mode():
        repo_name = image_url.split('/')[-1]
        return f"https://{gcp_project}-sim.cloudrun.app/{repo_name}"

    # Derive and sanitize service name from image if not provided
    if not service_name:
        raw_name = image_url.split('/')[-1].split(":")[0]
        service_name = _sanitize_service_name(raw_name)

    try:
        subprocess.run([
            "gcloud", "run", "deploy", service_name,
            "--image", image_url,
            "--project", gcp_project,
            "--region", region,
            "--platform", "managed",
            "--allow-unauthenticated",
            "--quiet"
        ], check=True)

        return f"https://{service_name}-{region}-a.run.app"
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Deploy failed: {e}")
