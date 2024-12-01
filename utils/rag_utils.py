import streamlit as st
import google.generativeai as genai
from utils.embeddings_utils import get_huggingface_embeddings
from pinecone import Pinecone
import time
from collections import defaultdict
from PIL import Image

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Pinecone with the API key
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])


pinecone_index = pc.Index("codebase-rag")

def perform_rag(query, repositories, images=None):
    try:
        # Process images if provided
        image_parts = []
        if images:
            for image_path in images:
                try:
                    image = Image.open(image_path)
                    image_parts.append(image)
                except Exception as img_error:
                    print(f"Error processing image {image_path}: {img_error}")

        raw_query_embedding = get_huggingface_embeddings(query)

        print("\n=== DEBUG: QUERY INFO ===")
        print(f"Repositories to search: {repositories}")
        print(f"Query: {query}")
        print(f"Number of images: {len(image_parts) if image_parts else 0}")
        print("=== END QUERY INFO ===\n")

        top_matches = {}
        for repo in repositories:
            matches = pinecone_index.query(
                vector=raw_query_embedding.tolist(), 
                top_k=20, 
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

        contexts = {}
        for repo_key in top_matches.keys():
            contexts[repo_key] = [item.metadata.get('page_content', '') for item in top_matches[repo_key]['matches']]

        augmented_query = ""
        for repo_key, repo_contexts in contexts.items():
            augmented_query += f"<CONTEXT for {repo_key}>\n"
            for context in repo_contexts[:10]:
                augmented_query += f"Content:\n{context}\n-------\n"
            augmented_query += f"</CONTEXT for {repo_key}>\n\n"

        augmented_query += f"MY QUESTION:\n{query}"

        system_prompt = """You are a Senior Software Engineer analyzing codebases.
        You will be provided with code context and possibly images of code or documentation.
        
        When analyzing the codebase:
        1. If images are provided, analyze their content in relation to the code context
        2. Identify key components, patterns, and potential improvements
        3. Provide specific examples from the codebase to support your analysis
        
        Format your response as follows:
        1. Code Context Analysis
           - Key components identified
           - Patterns observed
           - Relevant code examples
        
        2. Image Analysis (if images provided)
           - Description of code/documentation shown
           - Relation to the codebase
           - Any insights gained
        
        3. Recommendations
           - Potential improvements
           - Best practices to implement
           - Specific suggestions with examples
        
        Be specific, technical, and reference actual code when possible."""

        print("\n=== QUERY BEING SENT TO LLM ===")
        print("System Prompt:")
        print(system_prompt)
        print("\nUser Query with Context:")
        print(augmented_query)
        print("=== END OF QUERY ===\n")

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

    except Exception as e:
        error_message = str(e)
        print(f"Error occurred with Gemini Flash: {error_message}")
        raise Exception(f"Failed to generate response with Gemini Flash: {error_message}")