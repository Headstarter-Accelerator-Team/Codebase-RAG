import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.schema import Document




def get_huggingface_embeddings(text, model_name="sentence-transformers/all-mpnet-base-v2"):
    """
    Generates embeddings for the given text using a Hugging Face model.

    Args:
        text (str): The text to embed.
        model_name (str): The name of the Hugging Face model to use.

    Returns:
        numpy.ndarray: The embeddings for the text.
    """
    model = SentenceTransformer(model_name)
    return model.encode(text)


# Define a function to split text into smaller chunks
def split_text_into_chunks(text, chunk_size=1000, overlap=200):
    """
    Splits text into chunks of size `chunk_size` with `overlap` between chunks.

    Args:
        text (str): The text to split.
        chunk_size (int): The size of each chunk.
        overlap (int): The number of overlapping characters between chunks.

    Returns:
        list: A list of text chunks.
    """
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks


def embed_code(files, repo_url):
    """
    Embeds the code files and stores the embeddings in a Pinecone index.

    Args:
        files (list): A list of dictionaries containing file information.
        repo_url (str): The URL of the repository.

    Returns:
        None
    """
    # Get PINECONE_API_KEY from an environment variable
    pinecone_api_key = st.secrets["PINECONE_API_KEY"]

    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)

    # Connect to your Pinecone index
    pinecone_index = pc.Index("codebase-rag")

    vectorstore = PineconeVectorStore(index_name="codebase-rag", embedding=HuggingFaceEmbeddings())

    documents = []
    for file in files:
        file_content = file['content']
        file_name = file['src']

        # Split the file content into smaller chunks
        content_chunks = split_text_into_chunks(file_content, chunk_size=4096)  # Adjust size as needed

        # Create a Document for each chunk
        for chunk_index, chunk in enumerate(content_chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": file_name,
                    "chunk_index": chunk_index,
                    "total_chunks": len(content_chunks)
                }
            )
            documents.append(doc)


    vectorstore = PineconeVectorStore.from_documents(
        documents=documents,
        embedding=HuggingFaceEmbeddings(),
        index_name="codebase-rag",
        namespace= repo_url
    )
    print("Namespace has been added.")