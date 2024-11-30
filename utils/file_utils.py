import os
from utils.python_parser import PythonParser

def read_file(path):
    """
    Reads the content of a file.

    Args:
        path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(path, 'r') as file:
        content = file.read()
        return content
    

def list_files_recursive(path, files):
    """
    Recursively lists all files in a directory, excluding .git directories.

    Args:
        path (str): The path to the directory.
        files (list): The list to store file information.

    Returns:
        None
    """
    for entry in os.listdir(path):
        if entry == ".git":
            continue
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            list_files_recursive(full_path)
        else:
            # print(full_path)
            file = {
                "src": full_path,
                "content": read_file(full_path)
            }
            files.append(file)
    

def get_file_extension(filename):
    """
    Gets the file extension of a given filename.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The file extension.
    """
    split_tup = os.path.splitext(filename)
    file_name = split_tup[0]
    file_extension = split_tup[1]
    print("File Name: ", file_name)
    print("File Extension: ", file_extension)
    return file_extension


def process_python_files(file):
    """
    Processes a Python file by converting its content to an AST representation.

    Args:
        file (dict): A dictionary containing the file's source path and content.

    Returns:
        dict: A dictionary containing the file's source path and its AST representation.
    """
    parser = PythonParser()
    tree = parser.convert_python_to_ast(file['content'])['ast_representation']

    return {
        "src": file['src'],
        "content": tree
    }


