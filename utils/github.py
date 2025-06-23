import os
import tempfile
import subprocess

def validate_and_clone_repo(repo_url: str) -> str:
    """
    Validates a GitHub repo URL and clones it to a temporary directory.
    Returns the local path to the cloned repo.
    """
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL")

    temp_dir = tempfile.mkdtemp()
    subprocess.run(["git", "clone", repo_url, temp_dir], check=True)

    return temp_dir
