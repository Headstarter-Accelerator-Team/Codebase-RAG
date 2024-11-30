import streamlit as st
from streamlit_chat import message
from utils.file_utils import preprocess_code_to_ast
from utils.git_utils import process_repository, is_valid_github_url
from utils.embeddings_utils import embed_code
from utils.rag_utils import perform_rag
import html


st.markdown("""
    <style>
    .custom-banner {
        padding: 0px; 
        border-radius: 5px; 
        text-align: center; 
        color: var(--text-color);
        background-color: var(--primary-background-color);
    }
    /* Remove extra space above text input */
    div[data-testid="stTextInput"] label {
        display: none; /* Hide the label completely */
    }
    </style>
    <div class="custom-banner">
        <h1>📦 GitHub Repository Analyzer</h1>
        <p>Analyze and embed code from GitHub repositories efficiently with <strong>ease</strong>.</p>
        <p>A <strong>Senior Software Engineer</strong> in your digital pocket.</p>
    </div>
""", unsafe_allow_html=True)

with st.container():
    with st.form("my_form"):
        col1, col2 = st.columns([5, 1])
        with col1:
            url = st.text_input("", placeholder="🔗 Enter GitHub repository URL")
        with col2:
            submit = st.form_submit_button("🚀 Analyze")

# Check if the form was submitted
if submit:
    print("Url: ", url)
    # If URL is provided, clone the repository
    if not url:
        st.error('Please provide a GitHub repository URL.', icon="🚨")
    elif not is_valid_github_url(url):
        st.error('Invalid GitHub repository URL. Ensure it follows the pattern: https://github.com/user/repo.', icon="🚨")
    else:
        with st.spinner("Cloning repository..."):
            files = process_repository(url)


        with st.sidebar:
            # Define the file extensions you want to support
            supported_extensions = [".py", ".js", ".ts"]

            with st.expander("View Repository Files"):
                for file in files:
                    # Check if the file has one of the supported extensions
                    if any(file['src'].endswith(ext) for ext in supported_extensions):
                        # Display the file name as a collapsible element
                        st.markdown(f"""
                            <details>
                            <summary>{file['src']}</summary>
                            <pre style="background-color: #f7f7f7; padding: 10px; border-radius: 5px;">
                                {open(file['src'], 'r').read()}
                            </pre>
                            </details>
                        """, unsafe_allow_html=True)

        with st.spinner("Processing files..."):
            # Process only Python files in the cloned repository
            processedFiles = preprocess_code_to_ast(files)

            # Embed the code from the repository which will be inserted into Pinecone db
            embed_code(files, url)
        
        # Show success message in the Streamlit app
        st.success('Repository successfully added!', icon="✅")




# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = [] # Create an empty list for storing chat messages


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a Senior Software Engineer your question"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    rag_response = perform_rag(prompt, url, "llama-3.1-8b-instant")

    response = f"Senior Software Engineer: {rag_response}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

