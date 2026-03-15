import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.schema import Document

from utils.file_utils import get_file_extension


#get embeddings from huggingface

def get_huggingface_embeddings(text, model_name="sentence-transformers/all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    return model.encode(text)


# Define a function to split text into smaller chunks
def split_text_into_chunks(text, chunk_size=1000, overlap=200):
    """
    Splits text into chunks of size `chunk_size` with `overlap` between chunks.
    """
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks


def embed_code(files, repo_url, max_chunk_size=40620):
    """
    Embed code files into Pinecone, only chunking files that exceed max_chunk_size.
    
    Args:
        files: List of dictionaries containing file information
        repo_url: Repository URL to use as namespace
        max_chunk_size: Maximum size of a single document before chunking
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
        if get_file_extension(file['src']) == '.astpy':
            file_content = file['ast_representation']
            file_name = file['src']
        else:
            file_content = file['content']
            file_name = file['src']
    

        # Check if the file content exceeds the maximum size
        if len(file_content) > max_chunk_size:
            print(f"Chunking large file: {file_name}")
            # Split the file content into smaller chunks
            content_chunks = split_text_into_chunks(file_content, chunk_size=max_chunk_size)
            
            # Create a Document for each chunk
            for chunk_index, chunk in enumerate(content_chunks):
                doc = Document(
                    page_content=f"{file_name}\n{chunk}",
                    metadata={ #metadata for the chunk
                        "source": file_name,
                        "chunk_index": chunk_index,
                        "total_chunks": len(content_chunks),
                        "is_chunked": True,
                        "file_type": get_file_extension(file_name),
                        "file_size": len(file_content),
                        "repository": repo_url,
                        "is_ast": file_name.endswith('.astpy'),
                        
                    }
                )
                documents.append(doc)
        else:
            # For smaller files, store the entire content as one document
            doc = Document(
                page_content=f"{file_name}\n{file_content}",
                metadata={"source": file_name,
                          "chunk_index": 0,
                        "total_chunks": 0,
                          "is_chunked": False,
                          "file_type": get_file_extension(file_name),
                    "file_size": len(file_content),
                    "repository": repo_url,
                    "is_ast": file_name.endswith('.astpy')
                          }
            )
            
            documents.append(doc)

# add documents as vectors to the vector store in pinecone
    vectorstore = PineconeVectorStore.from_documents(
        documents=documents,
        embedding=HuggingFaceEmbeddings(),
        index_name="codebase-rag",
        namespace= repo_url
    )
    print(f"Added {len(documents)} documents to namespace: {repo_url}")