import os
from git import Repo

def clone_repository(repo_url):
    """Clones a GitHub repository to a temporary directory.

    Args:
        repo_url: The URL of the GitHub repository.

    Returns:
        The path to the cloned repository.
    """
    repo_name = repo_url.split("/")[-1]  # Extract repository name from URL
    repo_name = repo_url.split("/")[-1]  # Extract repository name from URL
    repo_path = os.path.join(os.getcwd(), "repositories", repo_name)
    Repo.clone_from(repo_url, repo_path)
    relative_repo_path = os.path.relpath(repo_path, os.getcwd())
    return relative_repo_path