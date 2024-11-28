import os
from utils.python_parser import PythonParser

def read_file(path):
    with open(path, 'r') as file:
        content = file.read()
        # print(content)
        return content
    

def list_files_recursive(path, files):
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
        "content": tree
    }


