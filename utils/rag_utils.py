import streamlit as st
from openai import OpenAI
from utils.embeddings_utils import get_huggingface_embeddings
from pinecone import Pinecone


client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=st.secrets["GROQ_API_KEY"]
)


# Define fallback models
FALLBACK_MODELS = {
    "mixtral-8x7b-32768": ["llama-3.1-8b-instant","gemma-7b-it", "gemma2-9b-it", "llama-3.1-70b-versatile", "llama-3.2-11b-text-preview", "llama-3.2-11b-vision-preview", "llama-3.2-1b-preview", "llama-3.2-3b-preview", "llama-3.2-90b-text-preview", "llama-3.2-90b-vision-preview", "llama-guard-3-8b", "llama3-70b-8192", "llama3-8b-8192", "llama3-groq-70b-8192-tool-use-preview", "llama3-groq-8b-8192-tool-use-preview", "llava-v1.5-7b-4096-preview", "mixtral-8x7b-32768"
],
    "llama-3.1-70b-versatile": ["llama-3.2-1b-preview", "llama-3.2-3b-preview"],
}

def perform_rag(query, repo_url,  primary_model="mixtral-8x7b-32768"):
    """
    Perform RAG (retrieval-augmented generation) with fallback models
    when the primary model fails due to rate limits or errors.

    Args:
        query (str): The query to perform RAG on.
        repo_url (str): The URL of the repository.
        primary_model (str): The primary model to use for RAG.

    Returns:
        str: The response from the language model.
    """
    fallback_models = FALLBACK_MODELS.get(primary_model, [])
    models_to_try = [primary_model] + fallback_models  # Primary + fallback models

    # Get PINECONE_API_KEY from an environment variable
    pinecone_api_key = st.secrets["PINECONE_API_KEY"]

    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)

    # Connect to your Pinecone index
    pinecone_index = pc.Index("codebase-rag")

    for model in models_to_try:
        try:
            # Perform the RAG operation
            raw_query_embedding = get_huggingface_embeddings(query)

            top_matches = pinecone_index.query(
                vector=raw_query_embedding.tolist(),
                top_k=5,
                include_metadata=True,
                namespace=repo_url
            )

            # Get the list of retrieved texts
            contexts = [item['metadata']['text'] for item in top_matches['matches']]
            print(contexts)

            augmented_query = (
                "<CONTEXT>\n" +
                "\n\n-------\n\n".join(contexts[:10]) +
                "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" +
                query
            )

            # Modify the prompt below as needed to improve the response quality
            system_prompt = f"""You are a Senior Software Engineer, specializing in TypeScript and Python.

            Answer any questions I have about the codebase, based on the code provided. The code will be in Abstract Syntax Tree (AST) format. Always consider all of the context provided when forming a response.
            """



            llm_response = client.chat.completions.create(
                model=model,
                messages=[
                    #{"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{augmented_query}  {system_prompt}"}
                ]
            )

            print(f"Response successfully retrieved from {model}")
            return llm_response.choices[0].message.content

        except Exception as e:
            error_message = str(e)  # Capture the exception as a string

            if "max_tokens" in error_message.lower():
              print("Maximum token limit reached.")
            elif "rate_limit" in error_message.lower():
              print("Rate limit exceeded.")

            print(f"Error occurred with model {model} \n {error_message}")

            print(f"Trying next fallback model...")

    raise Exception("All models failed due to rate limits or other errors.")
