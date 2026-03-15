# Codebase-RAG

A Streamlit app that lets you **chat with one or more GitHub codebases** using **RAG (Retrieval-Augmented Generation)**.

You can:
- **Add a repo** by pasting a GitHub URL (the app clones it locally)
- **Embed the repo’s code** into a **Pinecone** vector index (stored under a namespace equal to the repo URL)
- **Select multiple repos** and ask questions across all of them
- Optionally **upload images** and include them in the LLM request (Gemini multimodal)

---

## How it works (high level)

1. **Clone repo locally**
   - When you submit a GitHub URL, the app clones the repository into `./repositories/<repo_name>`.

2. **Read + preprocess files**
   - The app recursively scans the repo and collects supported source files (skipping directories like `node_modules`, `venv`, `.git`, etc.).
   - Supported extensions include: `.py, .js, .tsx, .jsx, .java, .ipynb, .cpp, .ts, .go, .rs, .vue, .swift, .c, .h`.
   - For Python files, it also generates an **AST representation** (stored as a pseudo-file with a `.astpy` suffix) and embeds that too.

3. **Embed into Pinecone**
   - Each file (or file chunk if it’s large) is embedded using **HuggingFace embeddings** and stored in the Pinecone index `codebase-rag`.
   - Documents are stored in Pinecone under a **namespace = repo_url** so different repos don’t mix.

4. **Ask questions (RAG)**
   - When you chat, your query is embedded and used to retrieve top matches from Pinecone for each selected repo namespace.
   - Retrieved snippets are assembled into a big “context” prompt.
   - The app then calls **Gemini (`gemini-1.5-flash`)** to generate the final answer.
   - (There is also a Groq/OpenAI-compatible client in the code, but the current flow returns from Gemini.)

---

## Project structure

- `app.py` — Streamlit UI + repo selection + chat loop
- `utils/git_utils.py` — clone a GitHub repo into `./repositories/`
- `utils/file_utils.py` — file crawling, extension filtering, and Python AST extraction helpers
- `utils/python_parser.py` — converts Python source into an AST string
- `utils/embeddings_utils.py` — chunks files (if needed) and writes embeddings into Pinecone
- `utils/rag_utils.py` — queries Pinecone + builds prompt + calls Gemini (optionally with images)
- `requirements.txt` — Python dependencies

---

## Requirements

- Python 3.10+ recommended
- Accounts/keys for:
  - **Pinecone** (vector DB)
  - **Google Gemini API** (for generation)
  - **Groq API** (present in code, may be optional depending on your usage)

---

## Setup

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Configure Streamlit secrets

Create `.streamlit/secrets.toml`:

```toml
PINECONE_API_KEY = "YOUR_PINECONE_KEY"
GOOGLE_API_KEY = "YOUR_GOOGLE_GEMINI_KEY"
GROQ_API_KEY = "YOUR_GROQ_KEY"
```

### 3) Make sure Pinecone index exists
This app expects a Pinecone index named:

- `codebase-rag`

Create it in your Pinecone dashboard if it doesn’t exist yet.

---

## Run the app

```bash
streamlit run app.py
```

---

## Usage

### Add a new repository to the knowledge base
1. Paste a GitHub URL in the input (example: `https://github.com/user/repo`)
2. Click **Submit**
3. The repo will be cloned into `./repositories/` and embedded into Pinecone

### Chat with repositories
1. Select one or more repos from the multi-select
2. Click **Chat with selected repositories**
3. Ask questions like:
   - “Where is authentication implemented?”
   - “Explain how embeddings are created.”
   - “Find the function that clones repos and describe its behavior.”
   - “Compare how repo A and repo B handle configuration.”

### Upload images (optional)
If you upload images while chatting, they will be included in the Gemini request (multimodal), which can help if you want to ask questions about screenshots/diagrams.

---

## Notes / Known quirks

- `utils/git_utils.py` sets `GIT_PYTHON_GIT_EXECUTABLE` to a Windows path by default. If you’re not on Windows, you may need to remove/change that line.
- Pinecone namespaces are based on the **repo URL**. The app keeps a mapping of local repo folder name → original URL in Streamlit session state.
- Some metadata fields in retrieval (like `text`) depend on what Pinecone stored—ensure your ingestion format matches what retrieval expects.

---

## Tech stack

- **Streamlit** for UI
- **LangChain + HuggingFace embeddings** for vectorization
- **Pinecone** for vector storage + retrieval
- **Google Generative AI (Gemini 1.5 Flash)** for answering questions (with optional images)
- (Optional/legacy) **Groq** OpenAI-compatible chat completions client

---

## Demo flow (quick)

1. Start app
2. Paste a GitHub repo URL → Submit (clones + embeds)
3. Select that repo → Chat
4. Ask: “Give me an overview of this codebase”
5. Get an LLM answer grounded in retrieved code snippets
