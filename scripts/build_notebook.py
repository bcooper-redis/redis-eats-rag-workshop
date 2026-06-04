"""
build_notebook.py

Assembles the Redis Eats RAG Workshop Jupyter Notebook from cell definitions
and writes it to notebooks/redis_eats_rag_workshop.ipynb.

Run:
    python3 scripts/build_notebook.py
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
OUTPUT = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Cell builders
# ---------------------------------------------------------------------------

def md(*lines):
    """Create a markdown cell from one or more strings."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": list(lines),
    }

def code(*lines, tags=None):
    """Create a code cell from one or more strings."""
    meta = {}
    if tags:
        meta["tags"] = tags
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": meta,
        "outputs": [],
        "source": list(lines),
    }

# ---------------------------------------------------------------------------
# Notebook cells
# ---------------------------------------------------------------------------

cells = []

# ============================================================
# SECTION 0 — Welcome and What We Are Building
# ============================================================

cells.append(md(
    "# 🍕 Redis Eats RAG Workshop\n",
    "## *Don't Talk With Food In Your Mouth*\n",
    "\n",
    "Welcome! In this workshop you will build a **Retrieval-Augmented Generation (RAG) chatbot** "
    "for Redis Eats — a food delivery platform — using:\n",
    "\n",
    "| Component | Role |\n",
    "|---|---|\n",
    "| **Redis Cloud** | Vector database, semantic cache, and router store |\n",
    "| **RedisVL** | Python library for Redis AI application patterns |\n",
    "| **Redis Query Engine** | High-performance vector similarity search |\n",
    "| **Redis LangCache** | Semantic caching for LLM responses |\n",
    "| **OpenAI** | Embeddings (`text-embedding-3-small`) and chat completions |\n",
    "\n",
    "---\n",
    "\n",
    "## What You Will Build\n",
    "\n",
    "A working support chatbot called **Don't Talk With Food In Your Mouth** that:\n",
    "\n",
    "- Reads food-delivery **policy PDFs** and stores them in Redis as vectors\n",
    "- Answers questions by **retrieving relevant chunks** and calling an LLM\n",
    "- Returns **source citations** alongside every answer\n",
    "- **Refuses off-topic questions** before they ever hit the database\n",
    "- **Caches repeated questions** to avoid unnecessary LLM calls\n",
    "\n",
    "---\n",
    "\n",
    "## Architecture\n",
    "\n",
    "![Architecture](../docs/architecture/redis-eats-rag-workshop-architecture.png)\n",
    "\n",
    "---\n",
    "\n",
    "## What This Workshop Covers (Workshop 1)\n",
    "\n",
    "- Redis Cloud connection via RedisVL\n",
    "- PDF loading and chunking\n",
    "- OpenAI embeddings\n",
    "- RedisVL `SearchIndex` + Redis Query Engine vector search\n",
    "- RAG answer generation with citations\n",
    "- Semantic routing with RedisVL `SemanticRouter`\n",
    "- Semantic caching with Redis LangCache\n",
    "\n",
    "## What Is Saved for Workshop 2\n",
    "\n",
    "Conversational memory, agentic workflows, MCP tools, Redis Iris, live order lookup, and context-aware responses.\n",
    "\n",
    "---\n",
    "\n",
    "**Estimated time:** ~2 hours  \n",
    "**Difficulty:** Beginner–Intermediate\n",
))

# ============================================================
# SECTION 1 — Setup
# ============================================================

cells.append(md(
    "---\n",
    "## Section 1 — Setup\n",
    "\n",
    "First, install the required Python packages. This cell is safe to re-run.\n",
))

cells.append(code(
    "# Install required packages\n",
    "# This works in Google Colab and local Jupyter environments.\n",
    "%pip install redis redisvl openai pypdf langcache tqdm python-dotenv --quiet",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Imports\n",
    "# ---------------------------------------------------------------------------\n",
    "import os\n",
    "import uuid\n",
    "import json\n",
    "import getpass\n",
    "from pathlib import Path\n",
    "from typing import List, Dict, Any\n",
    "\n",
    "import redis as redis_lib\n",
    "from redisvl.index import SearchIndex\n",
    "from redisvl.schema import IndexSchema\n",
    "from redisvl.query import VectorQuery\n",
    "\n",
    "import openai\n",
    "from openai import OpenAI\n",
    "\n",
    "import pypdf\n",
    "from tqdm import tqdm\n",
    "\n",
    "print(\"✅ Imports complete\")",
))

cells.append(md(
    "### 1.1 — Credentials\n",
    "\n",
    "Enter your **Redis Cloud** and **OpenAI** credentials below. "
    "They are stored only in this notebook session — nothing is written to disk.\n",
    "\n",
    "> **Redis Cloud:** You need the host, port, and password for your database.  \n",
    "> **OpenAI:** A paid API key starting with `sk-`.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Collect credentials interactively\n",
    "# getpass hides sensitive values so they don't appear in notebook output.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "REDIS_HOST = input(\"Redis Cloud host (e.g. redis-12345.c1.us-east-1-2.ec2.redns.redis-cloud.com): \").strip()\n",
    "REDIS_PORT = int(input(\"Redis port [6379]: \").strip() or \"6379\")\n",
    "REDIS_USERNAME = input(\"Redis username [default]: \").strip() or \"default\"\n",
    "REDIS_PASSWORD = getpass.getpass(\"Redis password: \")\n",
    "\n",
    "OPENAI_API_KEY = getpass.getpass(\"OpenAI API key: \")\n",
    "\n",
    "# Build the Redis URL used by RedisVL throughout this workshop\n",
    "REDIS_URL = f\"rediss://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}\"\n",
    "\n",
    "print(\"✅ Credentials collected\")",
))

cells.append(md(
    "### 1.2 — Test Redis Connectivity\n",
    "\n",
    "RedisVL will connect to Redis Cloud over TLS (`rediss://`). "
    "Let's verify the connection before doing any real work.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Test Redis connection using redis-py directly\n",
    "# We ping the server and print the Redis server version.\n",
    "# ---------------------------------------------------------------------------\n",
    "try:\n",
    "    r = redis_lib.Redis(\n",
    "        host=REDIS_HOST,\n",
    "        port=REDIS_PORT,\n",
    "        username=REDIS_USERNAME,\n",
    "        password=REDIS_PASSWORD,\n",
    "        ssl=True,           # Redis Cloud requires TLS\n",
    "        decode_responses=True,\n",
    "        socket_connect_timeout=5,\n",
    "    )\n",
    "    pong = r.ping()\n",
    "    info = r.info(\"server\")\n",
    "    print(f\"✅ Connected to Redis Cloud\")\n",
    "    print(f\"   Redis version : {info['redis_version']}\")\n",
    "    print(f\"   Host          : {REDIS_HOST}:{REDIS_PORT}\")\n",
    "except Exception as e:\n",
    "    print(f\"❌ Redis connection failed: {e}\")\n",
    "    print()\n",
    "    print(\"Troubleshooting:\")\n",
    "    print(\"  • Double-check your host, port, and password\")\n",
    "    print(\"  • Make sure your database is in Active state in Redis Cloud\")\n",
    "    print(\"  • Confirm TLS is enabled (rediss:// URL requires ssl=True)\")",
))

cells.append(md(
    "### 1.3 — Test OpenAI Connectivity\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Test OpenAI API key by listing available models\n",
    "# ---------------------------------------------------------------------------\n",
    "try:\n",
    "    openai_client = OpenAI(api_key=OPENAI_API_KEY)\n",
    "    models = openai_client.models.list()\n",
    "    print(\"✅ OpenAI API key is valid\")\n",
    "except openai.AuthenticationError:\n",
    "    print(\"❌ OpenAI authentication failed — check your API key\")\n",
    "except Exception as e:\n",
    "    print(f\"❌ OpenAI error: {e}\")",
))

# ============================================================
# SECTION 2 — Meet the Data
# ============================================================

cells.append(md(
    "---\n",
    "## Section 2 — Meet the Data\n",
    "\n",
    "The bot will answer questions from **10 Redis Eats policy and procedure documents**. "
    "These PDFs cover refunds, cancellations, delivery delays, driver procedures, "
    "restaurant onboarding, food safety, promo codes, account help, order status, and customer support.\n",
    "\n",
    "Let's load and inspect them.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Locate PDF files\n",
    "# Supports running from Google Colab (repo cloned) or locally.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "# Try paths relative to common notebook launch locations\n",
    "CANDIDATE_DIRS = [\n",
    "    Path(\"../data/pdfs\"),       # local: launched from notebooks/\n",
    "    Path(\"data/pdfs\"),          # local: launched from repo root\n",
    "    Path(\"/content/redis-eats-rag-workshop/data/pdfs\"),  # Colab\n",
    "]\n",
    "\n",
    "PDF_DIR = None\n",
    "for candidate in CANDIDATE_DIRS:\n",
    "    if candidate.exists() and list(candidate.glob(\"*.pdf\")):\n",
    "        PDF_DIR = candidate\n",
    "        break\n",
    "\n",
    "if PDF_DIR is None:\n",
    "    raise FileNotFoundError(\n",
    "        \"Could not find data/pdfs/. \"\n",
    "        \"Clone the repo and make sure the PDFs are present, \"\n",
    "        \"or run scripts/generate_policy_pdfs.py to generate them.\"\n",
    "    )\n",
    "\n",
    "pdf_files = sorted(PDF_DIR.glob(\"*.pdf\"))\n",
    "print(f\"Found {len(pdf_files)} PDFs in {PDF_DIR}\\n\")\n",
    "for f in pdf_files:\n",
    "    print(f\"  📄 {f.name}\")",
))

cells.append(md(
    "### 2.1 — Preview a Document\n",
    "\n",
    "Let's look at the first page of the refund policy so we know what the bot will be answering from.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Preview the first page of one policy document\n",
    "# ---------------------------------------------------------------------------\n",
    "preview_path = PDF_DIR / \"refund_policy.pdf\"\n",
    "\n",
    "with open(preview_path, \"rb\") as f:\n",
    "    reader = pypdf.PdfReader(f)\n",
    "    first_page_text = reader.pages[0].extract_text()\n",
    "\n",
    "print(f\"--- {preview_path.name} (page 1) ---\\n\")\n",
    "print(first_page_text[:1500])  # Show first 1500 characters",
))

# ============================================================
# SECTION 3 — Chunking
# ============================================================

cells.append(md(
    "---\n",
    "## Section 3 — Chunking\n",
    "\n",
    "### Why Do We Chunk?\n",
    "\n",
    "When we store documents in a vector database, we store them as **chunks** — small overlapping "
    "pieces of text rather than entire pages or files. This matters for two reasons:\n",
    "\n",
    "1. **Retrieval precision.** Embedding models compress text into a fixed-size vector. "
    "A short, focused chunk produces a more accurate embedding than a long, multi-topic page.\n",
    "2. **LLM context limits.** We pass retrieved text directly into a prompt. "
    "Smaller chunks let us pack more relevant content without hitting token limits.\n",
    "\n",
    "### Chunk Parameters\n",
    "\n",
    "| Parameter | What It Does |\n",
    "|---|---|\n",
    "| `chunk_size` | Maximum number of characters per chunk |\n",
    "| `chunk_overlap` | Characters shared between adjacent chunks (preserves context at boundaries) |\n",
    "\n",
    "We'll use **character-level chunking** here — simple and easy to reason about.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Extract all text from a PDF file, page by page\n",
    "# ---------------------------------------------------------------------------\n",
    "def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:\n",
    "    \"\"\"\n",
    "    Extract text from every page of a PDF.\n",
    "\n",
    "    Returns a list of dicts, one per page, each containing:\n",
    "      - text        : the extracted page text\n",
    "      - source      : PDF filename (without path)\n",
    "      - page_number : 1-based page number\n",
    "    \"\"\"\n",
    "    pages = []\n",
    "    with open(pdf_path, \"rb\") as f:\n",
    "        reader = pypdf.PdfReader(f)\n",
    "        for page_num, page in enumerate(reader.pages, start=1):\n",
    "            text = page.extract_text() or \"\"\n",
    "            text = text.strip()\n",
    "            if text:  # Skip blank pages\n",
    "                pages.append({\n",
    "                    \"text\": text,\n",
    "                    \"source\": pdf_path.name,\n",
    "                    \"page_number\": page_num,\n",
    "                })\n",
    "    return pages\n",
    "\n",
    "\n",
    "# Test on one file\n",
    "sample_pages = extract_text_from_pdf(PDF_DIR / \"refund_policy.pdf\")\n",
    "print(f\"refund_policy.pdf → {len(sample_pages)} page(s) extracted\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Chunk a single page of text into overlapping segments\n",
    "# ---------------------------------------------------------------------------\n",
    "def chunk_text(\n",
    "    text: str,\n",
    "    source: str,\n",
    "    page_number: int,\n",
    "    chunk_size: int = 500,\n",
    "    chunk_overlap: int = 50,\n",
    ") -> List[Dict[str, Any]]:\n",
    "    \"\"\"\n",
    "    Split text into overlapping character-level chunks.\n",
    "\n",
    "    Each chunk dict contains:\n",
    "      - chunk_id    : unique identifier for this chunk\n",
    "      - text        : the chunk text\n",
    "      - source      : source PDF filename\n",
    "      - page_number : page the chunk came from\n",
    "      - chunk_index : position of this chunk within the source page\n",
    "    \"\"\"\n",
    "    chunks = []\n",
    "    start = 0\n",
    "    chunk_index = 0\n",
    "\n",
    "    while start < len(text):\n",
    "        end = start + chunk_size\n",
    "        chunk_text_str = text[start:end]\n",
    "\n",
    "        chunks.append({\n",
    "            \"chunk_id\": str(uuid.uuid4()),\n",
    "            \"text\": chunk_text_str,\n",
    "            \"source\": source,\n",
    "            \"page_number\": page_number,\n",
    "            \"chunk_index\": chunk_index,\n",
    "        })\n",
    "\n",
    "        # Advance by chunk_size minus overlap so adjacent chunks share context\n",
    "        start += chunk_size - chunk_overlap\n",
    "        chunk_index += 1\n",
    "\n",
    "    return chunks\n",
    "\n",
    "\n",
    "# Quick test: chunk the first page of the refund policy\n",
    "sample_chunks = chunk_text(\n",
    "    text=sample_pages[0][\"text\"],\n",
    "    source=sample_pages[0][\"source\"],\n",
    "    page_number=sample_pages[0][\"page_number\"],\n",
    ")\n",
    "print(f\"First page split into {len(sample_chunks)} chunk(s)\")\n",
    "print(f\"\\nChunk 0 ({len(sample_chunks[0]['text'])} chars):\")\n",
    "print(sample_chunks[0][\"text\"][:300], \"...\")",
))

cells.append(md(
    "### 🏋️ Exercise 3.1 — Adjust Chunk Settings\n",
    "\n",
    "The default settings are `chunk_size=500, chunk_overlap=50`. "
    "Try changing them and observe the effect on chunk count and content.\n",
    "\n",
    "**Fill in the values below** and re-run the cell:\n",
    "\n",
    "- What happens if you make `chunk_size` much smaller (e.g. 200)?\n",
    "- What happens if you set `chunk_overlap` to 0?\n",
    "- What value feels right for a few sentences of policy text?\n",
    "\n",
    "> 💡 **Hint:** Good chunk sizes for RAG over short policy documents are usually 300–800 characters "
    "with 50–100 characters of overlap.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Exercise: Fill in YOUR chunk settings and observe the result\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "MY_CHUNK_SIZE    = 500   # TODO: change this and re-run\n",
    "MY_CHUNK_OVERLAP = 50    # TODO: change this and re-run\n",
    "\n",
    "exercise_chunks = chunk_text(\n",
    "    text=sample_pages[0][\"text\"],\n",
    "    source=sample_pages[0][\"source\"],\n",
    "    page_number=sample_pages[0][\"page_number\"],\n",
    "    chunk_size=MY_CHUNK_SIZE,\n",
    "    chunk_overlap=MY_CHUNK_OVERLAP,\n",
    ")\n",
    "\n",
    "print(f\"chunk_size={MY_CHUNK_SIZE}, chunk_overlap={MY_CHUNK_OVERLAP}\")\n",
    "print(f\"→ {len(exercise_chunks)} chunks from first page\")\n",
    "for i, c in enumerate(exercise_chunks[:3]):\n",
    "    print(f\"  Chunk {i}: {len(c['text'])} chars — {c['text'][:80]!r}...\")",
))

cells.append(code(
    "#@title ✅ Solution — Recommended Chunk Settings { display-mode: 'form' }\n",
    "\n",
    "# Recommended values for this workshop:\n",
    "#\n",
    "#   chunk_size=500    — captures a full policy paragraph in most cases\n",
    "#   chunk_overlap=50  — preserves a sentence of context at chunk boundaries\n",
    "#\n",
    "# These are the defaults already used in chunk_text().\n",
    "# For your own projects, experiment with 300–800 and measure retrieval quality.\n",
    "\n",
    "CHUNK_SIZE = 500\n",
    "CHUNK_OVERLAP = 50\n",
    "print(f\"Using chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Process all 10 PDFs into chunks\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "# Use the recommended settings\n",
    "CHUNK_SIZE = 500\n",
    "CHUNK_OVERLAP = 50\n",
    "\n",
    "all_chunks: List[Dict[str, Any]] = []\n",
    "\n",
    "for pdf_path in tqdm(pdf_files, desc=\"Processing PDFs\"):\n",
    "    pages = extract_text_from_pdf(pdf_path)\n",
    "    for page in pages:\n",
    "        chunks = chunk_text(\n",
    "            text=page[\"text\"],\n",
    "            source=page[\"source\"],\n",
    "            page_number=page[\"page_number\"],\n",
    "            chunk_size=CHUNK_SIZE,\n",
    "            chunk_overlap=CHUNK_OVERLAP,\n",
    "        )\n",
    "        all_chunks.extend(chunks)\n",
    "\n",
    "print(f\"\\n✅ Total chunks: {len(all_chunks)}\")\n",
    "print(f\"   Average chunk length: {sum(len(c['text']) for c in all_chunks) // len(all_chunks)} chars\")\n",
    "\n",
    "# Show a sample chunk\n",
    "sample = all_chunks[5]\n",
    "print(f\"\\nSample chunk from '{sample['source']}' (page {sample['page_number']}):\")\n",
    "print(sample[\"text\"])",
))

# ============================================================
# SECTION 4 — Embeddings
# ============================================================

cells.append(md(
    "---\n",
    "## Section 4 — Embeddings\n",
    "\n",
    "### What Is an Embedding?\n",
    "\n",
    "An **embedding** is a list of numbers (a vector) that represents the *meaning* of a piece of text. "
    "Two pieces of text with similar meaning will produce vectors that are close together in vector space — "
    "even if they use completely different words.\n",
    "\n",
    "This is what makes **semantic search** possible. Instead of matching exact keywords, "
    "Redis finds chunks whose *meaning* is closest to the user's question.\n",
    "\n",
    "We'll use OpenAI's `text-embedding-3-small` model, which produces **1536-dimensional** vectors.\n",
    "\n",
    "```\n",
    "\"Can I get a refund?\"  →  [0.012, -0.043, 0.891, ...]  (1536 numbers)\n",
    "\"Refund policy\"        →  [0.015, -0.039, 0.887, ...]  (very close!)\n",
    "\"Football scores\"      →  [-0.234, 0.512, -0.103, ...]  (far away)\n",
    "```\n",
    "\n",
    "Redis stores these vectors alongside each chunk and finds the nearest ones at query time.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Embedding model configuration\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "EMBEDDING_MODEL = \"text-embedding-3-small\"  # OpenAI model\n",
    "EMBEDDING_DIMS  = 1536                       # Dimensions produced by this model\n",
    "\n",
    "def get_embedding(text: str) -> List[float]:\n",
    "    \"\"\"\n",
    "    Generate a single embedding vector for the given text using OpenAI.\n",
    "\n",
    "    Args:\n",
    "        text: The input string to embed.\n",
    "\n",
    "    Returns:\n",
    "        A list of 1536 floats.\n",
    "    \"\"\"\n",
    "    response = openai_client.embeddings.create(\n",
    "        model=EMBEDDING_MODEL,\n",
    "        input=text,\n",
    "    )\n",
    "    return response.data[0].embedding\n",
    "\n",
    "\n",
    "# Test: embed one sentence and check the output shape\n",
    "test_vec = get_embedding(\"Can I get a refund if my food arrived cold?\")\n",
    "print(f\"✅ Embedding generated\")\n",
    "print(f\"   Dimensions : {len(test_vec)}\")\n",
    "print(f\"   First 5 values: {[round(v, 4) for v in test_vec[:5]]}\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Generate embeddings for all chunks\n",
    "# This will make one OpenAI API call per chunk.\n",
    "# With ~100–200 chunks it typically takes under 60 seconds.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "print(f\"Generating embeddings for {len(all_chunks)} chunks...\")\n",
    "\n",
    "for chunk in tqdm(all_chunks, desc=\"Embedding\"):\n",
    "    chunk[\"embedding\"] = get_embedding(chunk[\"text\"])\n",
    "\n",
    "print(f\"\\n✅ All embeddings generated\")\n",
    "print(f\"   Each vector: {len(all_chunks[0]['embedding'])} dimensions\")",
))

# ============================================================
# SECTION 5 — RedisVL Schema and Index Creation
# ============================================================

cells.append(md(
    "---\n",
    "## Section 5 — RedisVL Schema and Index Creation\n",
    "\n",
    "### Redis as a Vector Database\n",
    "\n",
    "If you've used Redis as a cache, you're probably familiar with simple key-value operations. "
    "Redis Cloud also includes the **Redis Query Engine**, which lets you define *indexes* over "
    "your data and run sophisticated queries — including **vector similarity search**.\n",
    "\n",
    "An **index** tells Redis which fields to index and how to index them. "
    "Once the index is created, Redis maintains it automatically as data is written.\n",
    "\n",
    "### RedisVL Schema\n",
    "\n",
    "**RedisVL** is a Python library that makes it easy to define schemas, create indexes, "
    "load data, and run queries — all with clean, readable code.\n",
    "\n",
    "Our schema has five fields:\n",
    "\n",
    "| Field | Type | Purpose |\n",
    "|---|---|---|\n",
    "| `text` | `text` | The chunk content — full-text searchable |\n",
    "| `source` | `tag` | PDF filename — filterable |\n",
    "| `page_number` | `numeric` | Page number — filterable |\n",
    "| `chunk_index` | `numeric` | Position within page |\n",
    "| `embedding` | `vector` | 1536-dim COSINE vector for similarity search |\n",
    "\n",
    "We use the **FLAT** algorithm — exact brute-force search, which is ideal for small datasets "
    "like this workshop where 100% recall matters and speed is not a bottleneck.\n",
    "\n",
    "> For production datasets with millions of vectors, use **HNSW** (approximate nearest neighbor) "
    "for much faster queries. Redis supports both.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Define the RedisVL schema for our chunk index\n",
    "#\n",
    "# Key prefix: redis-eats:chunk:\n",
    "#   Each chunk will be stored as a Redis Hash at a key like:\n",
    "#   redis-eats:chunk:3f2a1b9c-...\n",
    "#\n",
    "# Vector algorithm: FLAT\n",
    "#   Exact nearest-neighbor search — best for small datasets and workshops\n",
    "#   where we want guaranteed accuracy with no approximation.\n",
    "#\n",
    "# Distance metric: COSINE\n",
    "#   Measures the angle between vectors (ignores magnitude).\n",
    "#   text-embedding-3-small produces cosine-compatible embeddings.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "INDEX_NAME   = \"redis-eats-chunks\"       # Name of the Redis search index\n",
    "KEY_PREFIX   = \"redis-eats:chunk:\"       # All chunk keys share this prefix\n",
    "\n",
    "schema_dict = {\n",
    "    \"index\": {\n",
    "        \"name\": INDEX_NAME,\n",
    "        \"prefix\": KEY_PREFIX,\n",
    "        \"storage_type\": \"hash\",          # Store each chunk as a Redis Hash\n",
    "    },\n",
    "    \"fields\": [\n",
    "        {\"name\": \"text\",        \"type\": \"text\"},\n",
    "        {\"name\": \"source\",      \"type\": \"tag\"},\n",
    "        {\"name\": \"page_number\", \"type\": \"numeric\"},\n",
    "        {\"name\": \"chunk_index\", \"type\": \"numeric\"},\n",
    "        {\n",
    "            \"name\": \"embedding\",\n",
    "            \"type\": \"vector\",\n",
    "            \"attrs\": {\n",
    "                \"dims\":            EMBEDDING_DIMS,\n",
    "                \"algorithm\":       \"FLAT\",    # Exact search — good for ~100–1000 vectors\n",
    "                \"distance_metric\": \"COSINE\",\n",
    "                \"datatype\":        \"FLOAT32\",\n",
    "            },\n",
    "        },\n",
    "    ],\n",
    "}\n",
    "\n",
    "schema = IndexSchema.from_dict(schema_dict)\n",
    "print(\"✅ Schema defined\")\n",
    "print(f\"   Index name : {INDEX_NAME}\")\n",
    "print(f\"   Key prefix : {KEY_PREFIX}\")\n",
    "print(f\"   Fields     : {[f.name for f in schema.fields.values()]}\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Create the RedisVL SearchIndex\n",
    "#\n",
    "# SearchIndex wraps the schema and provides load(), search(), and delete()\n",
    "# methods. We pass the Redis URL so RedisVL manages the connection pool.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "index = SearchIndex(schema, redis_url=REDIS_URL)\n",
    "\n",
    "# Create the index on Redis Cloud.\n",
    "# overwrite=True means if the index already exists from a previous run,\n",
    "# it will be dropped and recreated cleanly.\n",
    "index.create(overwrite=True)\n",
    "\n",
    "print(f\"✅ Index '{INDEX_NAME}' created on Redis Cloud\")\n",
    "\n",
    "# Verify the index exists by fetching its info\n",
    "info = index.info()\n",
    "print(f\"   Num docs indexed : {info.get('num_docs', 0)}\")\n",
    "print(f\"   Index state      : {info.get('index_definition', {}).get('key_type', 'HASH')}\")",
))

# ============================================================
# SECTION 6 — Load Chunks into Redis
# ============================================================

cells.append(md(
    "---\n",
    "## Section 6 — Load Chunks into Redis\n",
    "\n",
    "Now we write all our chunks — text, metadata, and embedding vectors — into Redis Cloud. "
    "RedisVL's `index.load()` handles batching and serialization for us.\n",
    "\n",
    "Each chunk is stored as a **Redis Hash** at a key like `redis-eats:chunk:<uuid>`. "
    "The embedding vector is stored as a binary field alongside the text and metadata. "
    "Redis maintains the vector index automatically as data is written.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Prepare records for RedisVL\n",
    "#\n",
    "# Each record is a flat dict matching the schema fields.\n",
    "# The chunk_id becomes the unique part of the Redis key:\n",
    "#   redis-eats:chunk:<chunk_id>\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "def prepare_records(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:\n",
    "    \"\"\"\n",
    "    Convert internal chunk dicts to the flat format RedisVL expects.\n",
    "    The 'id' field is used as the unique key suffix.\n",
    "    \"\"\"\n",
    "    records = []\n",
    "    for chunk in chunks:\n",
    "        records.append({\n",
    "            \"id\":          chunk[\"chunk_id\"],\n",
    "            \"text\":        chunk[\"text\"],\n",
    "            \"source\":      chunk[\"source\"],\n",
    "            \"page_number\": chunk[\"page_number\"],\n",
    "            \"chunk_index\": chunk[\"chunk_index\"],\n",
    "            \"embedding\":   chunk[\"embedding\"],  # RedisVL serializes this as FLOAT32 bytes\n",
    "        })\n",
    "    return records\n",
    "\n",
    "\n",
    "records = prepare_records(all_chunks)\n",
    "print(f\"Prepared {len(records)} records for loading\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Load all records into Redis using RedisVL's batch loader\n",
    "#\n",
    "# index.load() writes all records in one efficient operation.\n",
    "# Redis stores each as a Hash, and the vector index is updated automatically.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "keys = index.load(records, id_field=\"id\")\n",
    "\n",
    "print(f\"✅ Loaded {len(keys)} chunks into Redis Cloud\")\n",
    "print(f\"   Sample key: {keys[0]}\")\n",
    "\n",
    "# Verify the count via index info\n",
    "info = index.info()\n",
    "print(f\"\\n   Index reports {info.get('num_docs', '?')} documents indexed\")",
))

cells.append(md(
    "### ✅ Checkpoint — Data is in Redis\n",
    "\n",
    "Your chunks, metadata, and embedding vectors are now stored in Redis Cloud. "
    "You can verify this in **Redis Insight** by browsing keys matching `redis-eats:chunk:*`.\n",
    "\n",
    "Run the cell below to spot-check one record directly.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Spot-check: fetch one chunk directly from Redis\n",
    "# ---------------------------------------------------------------------------\n",
    "sample_key = keys[0]\n",
    "raw = r.hgetall(sample_key)\n",
    "\n",
    "print(f\"Key     : {sample_key}\")\n",
    "print(f\"source  : {raw.get('source')}\")\n",
    "print(f\"page    : {raw.get('page_number')}\")\n",
    "print(f\"text    : {raw.get('text', '')[:200]}...\")\n",
    "print(f\"embedding bytes: {len(raw.get('embedding', b''))} bytes \"\n",
    "      f\"(= {len(raw.get('embedding', b'')) // 4} float32 values)\")",
))

# ============================================================
# SECTION 7 — Vector Search
# ============================================================

cells.append(md(
    "---\n",
    "## Section 7 — Vector Search\n",
    "\n",
    "Now comes the core of RAG: **finding the chunks most relevant to a user's question**.\n",
    "\n",
    "The process is:\n",
    "1. Embed the user's question with the same model used to embed the chunks\n",
    "2. Ask Redis to find the `k` chunks whose embeddings are closest (by cosine similarity)\n",
    "3. Return those chunks as context for the LLM\n",
    "\n",
    "Redis returns a **similarity score** with each result. For COSINE distance, "
    "a score of `0.0` means identical, `1.0` means completely unrelated — "
    "so lower scores = more relevant.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Vector search function\n",
    "#\n",
    "# Embeds the query, runs VectorQuery against Redis, returns top-k results.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "def search_chunks(\n",
    "    query: str,\n",
    "    top_k: int = 5,\n",
    ") -> List[Dict[str, Any]]:\n",
    "    \"\"\"\n",
    "    Find the top_k most semantically similar chunks for the given query.\n",
    "\n",
    "    Args:\n",
    "        query: The user's question or search string.\n",
    "        top_k: Number of results to return.\n",
    "\n",
    "    Returns:\n",
    "        List of result dicts with text, source, page_number, and score.\n",
    "    \"\"\"\n",
    "    # Embed the query using the same model used for the chunks\n",
    "    query_vector = get_embedding(query)\n",
    "\n",
    "    # Build a RedisVL VectorQuery\n",
    "    q = VectorQuery(\n",
    "        vector=query_vector,\n",
    "        vector_field_name=\"embedding\",\n",
    "        return_fields=[\"text\", \"source\", \"page_number\", \"chunk_index\"],\n",
    "        num_results=top_k,\n",
    "    )\n",
    "\n",
    "    # Execute the search\n",
    "    results = index.query(q)\n",
    "\n",
    "    return results\n",
    "\n",
    "\n",
    "# Test search\n",
    "results = search_chunks(\"Can I get a refund if my food arrived cold?\", top_k=3)\n",
    "\n",
    "print(f\"Top 3 results for 'Can I get a refund if my food arrived cold?'\\n\")\n",
    "for i, r_item in enumerate(results, 1):\n",
    "    score = float(r_item.get('vector_distance', 0))\n",
    "    print(f\"  [{i}] source={r_item['source']}  page={r_item['page_number']}  score={score:.4f}\")\n",
    "    print(f\"      {r_item['text'][:200]}...\")\n",
    "    print()",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Try a few more example searches to see retrieval in action\n",
    "# ---------------------------------------------------------------------------\n",
    "example_queries = [\n",
    "    \"What happens if my delivery is late?\",\n",
    "    \"How do promo codes work?\",\n",
    "    \"How do I reset my account password?\",\n",
    "]\n",
    "\n",
    "for query in example_queries:\n",
    "    results = search_chunks(query, top_k=1)\n",
    "    if results:\n",
    "        best = results[0]\n",
    "        score = float(best.get('vector_distance', 0))\n",
    "        print(f\"Q: {query}\")\n",
    "        print(f\"   → {best['source']} (score={score:.4f})\")\n",
    "        print(f\"   → {best['text'][:150]}...\")\n",
    "        print()",
))

cells.append(md(
    "### ✅ Checkpoint — Try Your Own Question\n",
    "\n",
    "Edit the query in the cell below and run it. "
    "Try questions about food safety, restaurant onboarding, driver procedures, or cancellations.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# YOUR TURN — try your own food-delivery question\n",
    "# ---------------------------------------------------------------------------\n",
    "my_question = \"What should a restaurant do if they need to pause orders?\"\n",
    "\n",
    "my_results = search_chunks(my_question, top_k=3)\n",
    "print(f\"Results for: '{my_question}'\\n\")\n",
    "for i, r_item in enumerate(my_results, 1):\n",
    "    score = float(r_item.get('vector_distance', 0))\n",
    "    print(f\"[{i}] {r_item['source']}  page={r_item['page_number']}  score={score:.4f}\")\n",
    "    print(f\"    {r_item['text'][:200]}...\")\n",
    "    print()",
))

# ============================================================
# SECTION 8 — Build the RAG Answer Function
# ============================================================

cells.append(md(
    "---\n",
    "## Section 8 — Build the RAG Answer Function\n",
    "\n",
    "### How RAG Works\n",
    "\n",
    "Retrieval-Augmented Generation combines search and generation:\n",
    "\n",
    "```\n",
    "1. User asks a question\n",
    "2. We embed the question and search Redis for relevant chunks\n",
    "3. We build a prompt: system message + retrieved chunks + user question\n",
    "4. We send the prompt to the LLM\n",
    "5. The LLM answers using only the provided context (no hallucination from training data)\n",
    "6. We return the answer + citations so the user knows where it came from\n",
    "```\n",
    "\n",
    "The key insight: Redis **grounds** the LLM. Without retrieval, the LLM would guess. "
    "With retrieval, it answers from your actual policy documents.\n",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Build a RAG prompt from retrieved chunks\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "SYSTEM_PROMPT = \"\"\"You are Don't Talk With Food In Your Mouth, the Redis Eats customer support assistant.\n",
    "Answer the customer's question using ONLY the policy information provided in the context below.\n",
    "If the context does not contain enough information to answer the question, say so honestly.\n",
    "Do not make up information or use knowledge outside of the provided context.\n",
    "Be concise, friendly, and helpful.\"\"\"\n",
    "\n",
    "\n",
    "def build_prompt(question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:\n",
    "    \"\"\"\n",
    "    Build the user-turn content for the LLM from retrieved chunks and the question.\n",
    "\n",
    "    Format:\n",
    "        CONTEXT:\n",
    "        [Source: <filename>, Page: <n>]\n",
    "        <chunk text>\n",
    "        ...\n",
    "\n",
    "        QUESTION:\n",
    "        <user question>\n",
    "\n",
    "    Args:\n",
    "        question: The user's question string.\n",
    "        retrieved_chunks: List of chunk dicts returned by search_chunks().\n",
    "\n",
    "    Returns:\n",
    "        A formatted string to use as the user message content.\n",
    "    \"\"\"\n",
    "    context_parts = []\n",
    "    for chunk in retrieved_chunks:\n",
    "        source = chunk.get(\"source\", \"unknown\")\n",
    "        page   = chunk.get(\"page_number\", \"?\")\n",
    "        text   = chunk.get(\"text\", \"\")\n",
    "        context_parts.append(f\"[Source: {source}, Page: {page}]\\n{text}\")\n",
    "\n",
    "    context_str = \"\\n\\n\".join(context_parts)\n",
    "\n",
    "    return f\"CONTEXT:\\n{context_str}\\n\\nQUESTION:\\n{question}\"\n",
    "\n",
    "\n",
    "# Test the prompt builder\n",
    "test_results = search_chunks(\"Can I get a refund if my food arrived cold?\", top_k=3)\n",
    "test_prompt = build_prompt(\"Can I get a refund if my food arrived cold?\", test_results)\n",
    "print(test_prompt[:800], \"...\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Core RAG answer function\n",
    "#\n",
    "# Retrieves relevant chunks, builds prompt, calls OpenAI, returns answer + citations.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "CHAT_MODEL = \"gpt-4o-mini\"   # Affordable, fast, and capable for this workshop\n",
    "\n",
    "\n",
    "def ask_rag(\n",
    "    question: str,\n",
    "    top_k: int = 5,\n",
    "    verbose: bool = True,\n",
    ") -> Dict[str, Any]:\n",
    "    \"\"\"\n",
    "    Answer a question using the Redis Eats RAG pipeline.\n",
    "\n",
    "    Steps:\n",
    "      1. Search Redis for the top_k most relevant chunks\n",
    "      2. Build a grounded prompt\n",
    "      3. Call OpenAI for an answer\n",
    "      4. Return answer + source citations\n",
    "\n",
    "    Args:\n",
    "        question: The user's question.\n",
    "        top_k:    Number of chunks to retrieve.\n",
    "        verbose:  If True, print the result to the console.\n",
    "\n",
    "    Returns:\n",
    "        Dict with 'answer' and 'citations' keys.\n",
    "    \"\"\"\n",
    "    # Step 1: Retrieve relevant chunks from Redis\n",
    "    chunks = search_chunks(question, top_k=top_k)\n",
    "\n",
    "    # Step 2: Build the grounded prompt\n",
    "    user_message = build_prompt(question, chunks)\n",
    "\n",
    "    # Step 3: Call the OpenAI chat model\n",
    "    response = openai_client.chat.completions.create(\n",
    "        model=CHAT_MODEL,\n",
    "        messages=[\n",
    "            {\"role\": \"system\", \"content\": SYSTEM_PROMPT},\n",
    "            {\"role\": \"user\",   \"content\": user_message},\n",
    "        ],\n",
    "        temperature=0.2,  # Low temperature for factual, consistent answers\n",
    "    )\n",
    "    answer = response.choices[0].message.content\n",
    "\n",
    "    # Step 4: Compile citations from retrieved chunks\n",
    "    seen = set()\n",
    "    citations = []\n",
    "    for chunk in chunks:\n",
    "        citation = f\"{chunk['source']} (page {chunk['page_number']})\"\n",
    "        if citation not in seen:\n",
    "            citations.append(citation)\n",
    "            seen.add(citation)\n",
    "\n",
    "    if verbose:\n",
    "        print(f\"Question : {question}\")\n",
    "        print(f\"\\nAnswer   :\\n{answer}\")\n",
    "        print(f\"\\nSources  : {', '.join(citations)}\")\n",
    "\n",
    "    return {\"answer\": answer, \"citations\": citations}\n",
    "\n",
    "\n",
    "# Test the RAG pipeline\n",
    "result = ask_rag(\"Can I get a refund if my food arrived cold?\")",
))

cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Run the full set of workshop example questions\n",
    "# ---------------------------------------------------------------------------\n",
    "workshop_questions = [\n",
    "    \"What happens if my delivery is late?\",\n",
    "    \"How do promo codes work?\",\n",
    "    \"What should a restaurant do if they need to pause orders?\",\n",
    "    \"How do I reset my account password?\",\n",
    "]\n",
    "\n",
    "for q in workshop_questions:\n",
    "    print(\"=\" * 60)\n",
    "    ask_rag(q)\n",
    "    print()",
))

# ============================================================
# Write notebook to disk
# ============================================================

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0",
        },
        "colab": {
            "provenance": [],
            "collapsed_sections": [],
        },
    },
    "cells": cells,
}

OUTPUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False))
print(f"✅ Notebook written → {OUTPUT}")
print(f"   Cells: {len(cells)}")
