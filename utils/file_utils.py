import os
from utils.python_parser import PythonParser


SUPPORTED_EXTENSIONS = {'.py', '.js', '.tsx', '.jsx', '.java', '.ipynb',
                         '.cpp', '.ts', '.go', '.rs', '.vue', '.swift', '.c', '.h'}

IGNORED_DIRS = {'node_modules', 'venv', 'env', 'dist', 'build', '.git',
                '__pycache__', '.next', '.vscode', 'vendor', 'Lib'}
def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except UnicodeDecodeError:
        print(f"Could not decode {path} with UTF-8. Trying with 'latin-1'.")
        with open(path, 'r', encoding='latin-1') as file:
            content = file.read()
            return content
    

def list_files_recursive(path, files):
    for entry in os.listdir(path):
        # Skip ignored directories and .pyc files
        if entry == ".git" or entry.endswith('.pyc') or entry == '__pycache__':
            continue
            
        full_path = os.path.join(path, entry)
        
        # Skip if the path contains any ignored directory
        if any(ignored in full_path for ignored in IGNORED_DIRS):
            continue
            
        if os.path.isdir(full_path):
            list_files_recursive(full_path, files)
        else:
            # Only process files with supported extensions
            file_extension = get_file_extension(full_path)
            if file_extension in SUPPORTED_EXTENSIONS:
                file = {
                    "src": full_path,
                    "content": read_file(full_path)
                }
                files.append(file)
    

def get_file_extension(filename):
    split_tup = os.path.splitext(filename)
    # extract the file name and extension
    file_name = split_tup[0]
    file_extension = split_tup[1]
    print("File Name: ", file_name)
    print("File Extension: ", file_extension)
    return file_extension


def process_python_files(file):
    parser = PythonParser()
    tree = parser.convert_python_to_ast(file['content'])['ast_representation']

    return {
        "src": file['src'],
        "ast_representation": tree
    }

def get_file_content(file_path, repo_path):
    """
    Get content of a single file.

    Args:
        file_path (str): Path to the file

    Returns:
        Optional[Dict[str, str]]: Dictionary with file name and content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get relative path from repo root
        rel_path = os.path.relpath(file_path, repo_path)

        return {
            "name": rel_path,
            "content": content
        }
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None


def get_main_files_content(repo_paths: list[str]):
    """
    Get content of supported code files from the local repository.

    Args:
        repo_paths: List of paths to the local repositories

    Returns:
        Dictionary of lists containing file names and contents
    """
    repo_files = {}

    try:
        for repo_path in repo_paths:
            files_content = []
            try:
                # Skip if the repository path itself is in IGNORED_DIRS
                if any(ignored in repo_path for ignored in IGNORED_DIRS):
                    print(f"Skipping ignored directory: {repo_path}")
                    continue
                
                # Call the recursive function to list files
                list_files_recursive(repo_path, files_content)
                
                # Filter out any files from ignored directories
                filtered_content = [
                    file for file in files_content 
                    if not any(ignored in file['src'] for ignored in IGNORED_DIRS)
                ]
                
                repo_files[repo_path] = filtered_content
            except Exception as e:
                print(f"Error reading repository: {str(e)}")
    except Exception as e:
        print(f"Error reading list of repositories: {str(e)}")

    return repo_files

