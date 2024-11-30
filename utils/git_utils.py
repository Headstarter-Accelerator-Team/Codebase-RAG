import os
import shutil
import re
from git import Repo
from utils.file_utils import list_files_recursive


def is_valid_github_url(url):
    # Basic validation for GitHub URL structure
    github_pattern = re.compile(r'https:\/\/github\.com\/[\w\-]+\/[\w\-]+(\.git)?$')
    return bool(github_pattern.match(url))


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
    print("Repo path: ", repo_path)

    print("Detected repo locally.")
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)  # Remove the directory and its contents
        print("Directory deleted successfully.")

    Repo.clone_from(repo_url, repo_path)
    relative_repo_path = os.path.relpath(repo_path, os.getcwd())
    return relative_repo_path


def process_repository(url):
    path = "./" + clone_repository(url) # Clone the repository to a local path
    # Initialize an empty list to store file information
    files = []
    list_files_recursive(path, files) # Recursively list all files in the repository
    return files