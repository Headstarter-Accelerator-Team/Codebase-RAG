import streamlit as st
from streamlit_chat import message
from utils.git_utils import clone_repository
from utils.file_utils import list_files_recursive, get_file_extension, process_python_files
from utils.embeddings_utils import embed_code
from utils.rag_utils import perform_rag


# Create a form for user input to accept a GitHub repository URL
with st.form("my_form"):
    url = st.text_input("Enter Github http url...") # Text input for GitHub URL
    submit = st.form_submit_button("Submit") # Submit button to process the input

# Check if the form was submitted
if submit:
    print("Url: ", url)
    # If URL is provided, clone the repository
    if url:
        print("Calling function clone_repository...")
        path = "./" + clone_repository(url) # Clone the repository to a local path
        print("Rep has been clone to: ", path)

        # Initialize an empty list to store file information
        files = []
        list_files_recursive(path, files) # Recursively list all files in the repository
        print(files)

        # Process only Python files in the cloned repository
        processedFiles = files[:] # Make a copy of the file list
        for i in range(0, len(processedFiles)):
            if get_file_extension(processedFiles[i]['src']) == '.py': # Check if the file has a .py extension
                processedFiles[i] = process_python_files(processedFiles[i]) # Process the Python file
                print(processedFiles[i])

        # print("\n\n", processedFiles)

        # Embed the code from the repository which will be inserted into Pinecone db
        embed_code(files, url)
        
        # Show success message in the Streamlit app
        st.success('Repository successfully added!', icon="✅")
    else:
        # Handle case where URL is not provided
        print("Please, type in a github repository url.")
        st.error('Please, type in a github repository url.', icon="🚨")



# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = [] # Create an empty list for storing chat messages


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

    rag_response = perform_rag(prompt, url, "llama3-70b-8192")

    response = f"Echo: {rag_response}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
