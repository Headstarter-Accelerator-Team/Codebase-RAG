import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from utils.embeddings_utils import get_huggingface_embeddings
from pinecone import Pinecone
import time
from collections import defaultdict
from PIL import Image
# Configure Gemini




client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=st.secrets["GROQ_API_KEY"]
)

# Initialize Pinecone with the API key
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])

# Connect to your Pinecone index
pinecone_index = pc.Index("codebase-rag")

# Define fallback models




def perform_rag(query,repositories , primary_model="llama3-8b-8192", images=None ):
    # Process images if provided
    image_parts = []
    if images:
        for image_path in images:
            try:
                image = Image.open(image_path)
                image_parts.append(image)
            except Exception as img_error:
                print(f"Error processing image {image_path}: {img_error}")
    
    FALLBACK_MODELS = {
     "llama3-8b-819": ["llama-3.1-8b-instant","gemma-7b-it", "gemma2-9b-it", "llama-3.1-70b-versatile", "llama-3.2-11b-text-preview", "llama-3.2-11b-vision-preview", "llama-3.2-1b-preview", "llama-3.2-3b-preview", "llama-3.2-90b-text-preview", "llama-3.2-90b-vision-preview", "llama-guard-3-8b", "llama3-70b-8192", "llama3-8b-8192", "llama3-groq-70b-8192-tool-use-preview", "llama3-groq-8b-8192-tool-use-preview", "llava-v1.5-7b-4096-preview", "mixtral-8x7b-32768"
 ],
     "llama-3.1-70b-versatil": ["llama-3.2-1b-preview", "llama-3.2-3b-preview"],
}
    """
    Perform RAG (retrieval-augmented generation) with fallback models
    when the primary model fails due to rate limits or errors.
    """
    fallback_models = FALLBACK_MODELS.get(primary_model, [])
    models_to_try = [primary_model] + fallback_models  # Primary + fallback models

    for model in models_to_try:
        try:
            # Perform the RAG operation
            raw_query_embedding = get_huggingface_embeddings(query)

            # Debug print before Pinecone query
            print("\n=== DEBUG: QUERY INFO ===")
            print(f"Repositories to search: {repositories}")
            print(f"Query: {query}")
            print("=== END QUERY INFO ===\n")

            # Feel free to change the "top_k" parameter to be a higher or lower number
            top_matches = {}
            for repo in repositories:
                matches = pinecone_index.query(
                    vector=raw_query_embedding.tolist(), 
                    top_k=15, 
                    include_metadata=True, 
                    namespace=repo
                )
                print(f"\n=== DEBUG: PINECONE RESPONSE for {repo} ===")
                print(f"Number of matches: {len(matches['matches'])}")
                if len(matches['matches']) > 0:
                    print(f"First match score: {matches['matches'][0].score}")
                    print(f"First match metadata: {matches['matches'][0].metadata}")
                print("=== END PINECONE RESPONSE ===\n")
                top_matches[repo] = matches

            # Get the list of retrieved texts and their metadata
            contexts = {}
            for repo_key in top_matches.keys():
                contexts[repo_key] = [{
                    'text': item.metadata.get('text', ''),
                    'source': item.metadata.get('source', ''),
                    'chunk_index': item.metadata.get('chunk_index'),
                    'total_chunks': item.metadata.get('total_chunks'),
                    'is_chunked': item.metadata.get('is_chunked', False),
                    'file_type': item.metadata.get('file_type'),
                    'file_size': item.metadata.get('file_size'),
                    'is_ast': item.metadata.get('is_ast', False)
                } for item in top_matches[repo_key]['matches']]

            # Debug print to check what we're getting from Pinecone
            print("\n=== DEBUG: PINECONE MATCHES ===")
            for repo_key in top_matches.keys():
                print(f"\nRepository: {repo_key}")
                for match in top_matches[repo_key]['matches'][:1]:  # Print first match as example
                    print("Match metadata:", match.metadata)
            print("=== END DEBUG ===\n")

            augmented_query = ""
            # Add context for each repository
            for repo_key in contexts.keys():
                augmented_query += f"<CONTEXT for {repo_key}>\n"
                for context in contexts[repo_key]:  # [:5] ->Still limiting to top 10 matches for readability
                    augmented_query += f"""
                    File: {context['source']}
                    Type: {'AST' if context['is_ast'] else 'Source Code'}
                    Size: {context['file_size']} bytes
                    {f'Chunk {context["chunk_index"] + 1} of {context["total_chunks"]}' if context['is_chunked'] else 'Complete File'}

                    Content:
                    {context["text"]}
                    -------
                    """
                augmented_query += f"</CONTEXT for {repo_key}>\n\n"

            augmented_query += f"MY QUESTION:\n{query}"

            # Modify the prompt below as needed to improve the response quality
            system_prompt = f"""You are a Senior Software Engineer

            Provide answers to questions based on the code provided. Always consider all of the context given in the <Context> tags when forming a response. Present your answers in a concise, structured, and user-friendly format.

            **Instructions for Formatting**:
            - Split the answers clearly based on the repositories mentioned in the <Context>/content<repository name> tags.
            - Use bullet points or numbered lists for clarity where applicable.
            - Provide summaries in plain, easy-to-read language.
            - If there are multiple repositories, ensure each one has its own clear section header with a brief explanation of its purpose.
            - Avoid technical jargon unless necessary, and provide examples where helpful.
            - Ensure unrelated repositories or snippets are separated under an "Other Repositories" section.

            **Response Format Example**:
            **<Repository Name>**
            - Purpose: Briefly explain what the repository is for.
            - Key Features:
              - Highlight specific functionalities or code blocks in simple terms.
              - Provide examples or notable snippets.
            - Overall Summary: Conclude with a concise description of what the repository focuses on.

            **Other Repositories**
            - Briefly summarize other repositories if context is unclear or limited."""
            
            #query being sent
            print("\n=== QUERY BEING SENT TO LLM ===")
            print("System Prompt:")
            print(system_prompt)
            print("\nUser Query with Context:")
            print(augmented_query)
            print("=== END OF QUERY ===\n")
            # LLM call
            
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

            model = genai.GenerativeModel('gemini-1.5-flash')
            # Generate response using Gemini Flash with both text and images
            prompt = f"{system_prompt}\n\n{augmented_query}"
            
            if image_parts:
                # If images is present, use multimodal generation
                response = model.generate_content([prompt, *image_parts])
            else:
                # Text-only generation
                response = model.generate_content(prompt)
            
            print("Response successfully retrieved from Gemini Flash")
            return response.text
        
            llm_response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": augmented_query}
                    ]
                )

            # Extract raw response from groq
            response = llm_response.choices[0].message.content



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

