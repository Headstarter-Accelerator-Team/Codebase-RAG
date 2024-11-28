import streamlit as st
from streamlit_chat import message
from utils.git_utils import clone_repository
from utils.file_utils import list_files_recursive, get_file_extension, process_python_files
from utils.embeddings_utils import embed_code
from utils.rag_utils import perform_rag

with st.form("my_form"):
    url = st.text_input("Enter Github http url...")
    submit = st.form_submit_button("Submit")

if submit:
    print("Url: ", url)
    if url:
        print("Calling function clone_repository...")
        path = "./" + clone_repository(url)
        print("Rep has been clone to: ", path)
        st.success('Repository successfully added!', icon="✅")
        files = []
        list_files_recursive(path, files)
        print(files)

        processedFiles = files[:]
        for i in range(0, len(processedFiles)):
            if get_file_extension(processedFiles[i]['src']) == '.py':
                processedFiles[i] = process_python_files(processedFiles[i])
                print(processedFiles[i])

        # print("\n\n", processedFiles)
        embed_code(files, url)
        



    else:
        print("Please, type in a github repository url.")
        st.error('Please, type in a github repository url.', icon="🚨")




# uploaded_files = st.file_uploader(
#     "Choose a CSV file", accept_multiple_files=True
# )

# for uploaded_file in uploaded_files:
#     bytes_data = uploaded_file.read()
#     st.write("filename:", uploaded_file.name)
    # st.write(bytes_data)

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

    rag_response = perform_rag(prompt, url, "llama3-70b-8192")

    response = f"Echo: {rag_response}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
