import os

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



def read_file(path):
    with open(path, 'r') as file:
        content = file.read()
        # print(content)
        return content