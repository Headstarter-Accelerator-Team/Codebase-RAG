import os
import time
import streamlit as st
from streamlit_chat import message
from utils.git_utils import clone_repository
from utils.file_utils import get_main_files_content, list_files_recursive, get_file_extension, process_python_files
from utils.embeddings_utils import embed_code
from utils.rag_utils import perform_rag

if not os.path.exists("./uploaded_images"):
    os.makedirs("./uploaded_images")

# Add at the beginning of the file after imports
if 'repo_url_mapping' not in st.session_state:
    st.session_state.repo_url_mapping = {}

# Function to get repository names
def get_repository_names(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d != ".git"]

# Initialize URL mapping for existing repositories if not already present
repo_names = get_repository_names("./repositories")
for repo_name in repo_names:
    if repo_name not in st.session_state.repo_url_mapping:
        # For existing repositories, construct a default GitHub URL or mark as local
        if os.path.exists(f"./repositories/{repo_name}/.git"):
            try:
                with open(f"./repositories/{repo_name}/.git/config", 'r') as f:
                    config = f.read()
                    # Extract URL from git config IMPORTANT for finding data from the pincone db
                    url_start = config.find('url = ') + 6
                    url_end = config.find('\n', url_start)
                    url = config[url_start:url_end]
                    st.session_state.repo_url_mapping[repo_name] = url
            except:
                st.session_state.repo_url_mapping[repo_name] = f"local/{repo_name}"
        else:
            st.session_state.repo_url_mapping[repo_name] = f"local/{repo_name}"

with st.form("my_form"):
    url = st.text_input("Enter Github http url...")
    selected_repo = []
    repo_names = get_repository_names("./repositories")  
    # Multi-select for repo selection
    selected_repo = (st.multiselect("Select repositories:", repo_names) ) 
    submit = st.form_submit_button("Submit")

if submit:
    print("Url: ", url)
    if selected_repo not in repo_names:
        if url:
            print("Calling function clone_repository...")
            path = "./" + clone_repository(url)
            repo_name = path.split('/')[-1]  # Get repository name from path
            st.session_state.repo_url_mapping[repo_name] = url  # Store the mapping
            print("Repo has been cloned to: ", path)
            st.success('Repository successfully added!', icon="✅")
            files = []
            list_files_recursive(path, files)
            print(files)


            processedFiles = files[:]
            for i in range(0, len(processedFiles)):
                if get_file_extension(processedFiles[i]['src']) == '.py':
                    ast_file = process_python_files(files[i])
                    ast_file['src'] = files[i]['src'] + '.astpy'  # Add .ast extension to differentiate
                    processedFiles.append(ast_file)
                    print(processedFiles[i])

            # print("\n\n", processedFiles)
            embed_code(processedFiles, url)

            # Check if the selected repository is in the repositories directory
        elif not (url.strip())  and not selected_repo: 
            print("Please, type in a github repository url or select a repository")
            error_placeholder = st.empty()  # Create a placeholder for the error message
            error_placeholder.error('Please, type in a GitHub repository URL or select a repository.')
            # Wait for 5 seconds before clearing the error message
            time.sleep(2)
            error_placeholder.empty()  # Clear the error message




uploaded_files = st.file_uploader(
    "Upload images", accept_multiple_files=True, type=["jpg", "jpeg", "png"]
)

# for uploaded_file in uploaded_files:
#     bytes_data = uploaded_file.read()
#     st.write("filename:", uploaded_file.name)
#     st.write(bytes_data)

uploaded_image_paths = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = f"./uploaded_images/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        uploaded_image_paths.append(file_path)
    st.success(f"{len(uploaded_image_paths)} image(s) uploaded successfully.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    if uploaded_image_paths:
        st.chat_message("user").markdown(f"Uploaded images: {', '.join([os.path.basename(p) for p in uploaded_image_paths])}")

    # Debug prints for URL mapping
    print("\n=== DEBUG: URL MAPPING ===")
    print("Session state mapping:", st.session_state.repo_url_mapping)
    print("Selected repos:", selected_repo)
    
    # Convert selected repo names to their URLs
    selected_urls = [st.session_state.repo_url_mapping[repo] for repo in selected_repo if repo in st.session_state.repo_url_mapping]
    print("Selected URLs:", selected_urls)
    print("=== END URL MAPPING ===\n")
    
    # Use the URLs as namespaces for querying Pinecone
    rag_response = perform_rag(prompt, selected_urls, images=uploaded_image_paths)
    response = f"Echo: {rag_response}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

