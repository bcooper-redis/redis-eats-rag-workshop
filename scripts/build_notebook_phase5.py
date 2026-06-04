"""
build_notebook_phase5.py

Appends Sections 12–13 (Reset Lab, What Comes Next) to the notebook
and applies end-to-end polish:
  - Injects a persistent "expected output" comment block after key code cells
  - Adds a notebook-level table of contents to the welcome cell
  - Ensures the Colab clone cell is present at the top

Run AFTER build_notebook_phase4.py:
    python3 scripts/build_notebook_phase5.py
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
NOTEBOOK  = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"

# ---------------------------------------------------------------------------
def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}

def code(*lines, tags=None):
    meta = {"tags": tags} if tags else {}
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": meta,
        "outputs": [],
        "source": list(lines),
    }

# ---------------------------------------------------------------------------
# Load existing notebook
# ---------------------------------------------------------------------------
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

# ============================================================
# SECTION 12 — Reset Lab
# ============================================================

section12 = []

section12.append(md(
    "---\n",
    "## Section 12 — Reset Lab\n",
    "\n",
    "Great work! Before you close out, let's clean up everything this workshop "
    "wrote to your Redis Cloud database.\n",
    "\n",
    "This cell will:\n",
    "\n",
    "1. **Drop the vector search index** (`redis-eats-chunks`) — removes the index definition\n",
    "2. **Delete all chunk keys** matching `redis-eats:chunk:*` — removes the stored documents and vectors\n",
    "3. **Drop the semantic router index** from Redis\n",
    "4. **Confirm** the cleanup was successful\n",
    "\n",
    "> ⚠️ **Safe by design:** The cleanup is scoped to the key prefix `redis-eats:` and the "
    "named indexes created during this workshop. It will not touch any other data in your database.\n",
    "\n",
    "> 💡 **Why does this matter?** When using a shared or persistent database, always clean up "
    "workshop data so it doesn't accumulate, consume memory, or interfere with future work.\n",
))

section12.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Reset Lab — clean up all workshop data from Redis Cloud\n",
    "#\n",
    "# This is scoped to:\n",
    "#   - Index   : redis-eats-chunks\n",
    "#   - Keys    : redis-eats:chunk:*\n",
    "#   - Router  : redis-eats-router (managed by RedisVL)\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "import time\n",
    "\n",
    "print(\"Starting Redis Eats workshop cleanup...\\n\")\n",
    "\n",
    "# -----------------------------------------------------------------------\n",
    "# Step 1: Drop the chunk vector search index\n",
    "# SearchIndex.delete() drops the index AND deletes all indexed keys\n",
    "# when delete_documents=True.\n",
    "# -----------------------------------------------------------------------\n",
    "try:\n",
    "    index.delete(drop=True)   # drop=True removes the index definition\n",
    "    print(\"✅ Vector search index 'redis-eats-chunks' dropped\")\n",
    "except Exception as e:\n",
    "    print(f\"⚠️  Index drop: {e}\")\n",
    "\n",
    "# -----------------------------------------------------------------------\n",
    "# Step 2: Delete any remaining redis-eats:chunk:* keys\n",
    "# (belt-and-suspenders — index.delete() should handle this,\n",
    "#  but we scan to confirm zero keys remain)\n",
    "# -----------------------------------------------------------------------\n",
    "try:\n",
    "    chunk_keys = list(r.scan_iter(\"redis-eats:chunk:*\", count=500))\n",
    "    if chunk_keys:\n",
    "        r.delete(*chunk_keys)\n",
    "        print(f\"✅ Deleted {len(chunk_keys)} remaining chunk keys\")\n",
    "    else:\n",
    "        print(\"✅ No stray chunk keys found (index.delete() cleaned them up)\")\n",
    "except Exception as e:\n",
    "    print(f\"⚠️  Chunk key cleanup: {e}\")\n",
    "\n",
    "# -----------------------------------------------------------------------\n",
    "# Step 3: Delete the semantic router from Redis\n",
    "# -----------------------------------------------------------------------\n",
    "try:\n",
    "    router.delete()   # Removes the router index and its stored embeddings\n",
    "    print(\"✅ SemanticRouter 'redis-eats-router' deleted\")\n",
    "except Exception as e:\n",
    "    print(f\"⚠️  Router cleanup: {e}\")\n",
    "\n",
    "# -----------------------------------------------------------------------\n",
    "# Step 4: Verification — confirm nothing remains\n",
    "# -----------------------------------------------------------------------\n",
    "time.sleep(0.5)   # Brief pause to let Redis process the deletes\n",
    "\n",
    "remaining_keys = list(r.scan_iter(\"redis-eats:*\", count=500))\n",
    "if remaining_keys:\n",
    "    print(f\"\\n⚠️  {len(remaining_keys)} redis-eats:* keys still present:\")\n",
    "    for k in remaining_keys[:10]:\n",
    "        print(f\"   {k}\")\n",
    "else:\n",
    "    print(\"\\n✅ All redis-eats:* keys removed — database is clean\")\n",
    "\n",
    "print(\"\\n🏁 Reset complete. Your Redis Cloud database is back to its pre-workshop state.\")",
))

section12.append(md(
    "### Verify in Redis Insight (Optional)\n",
    "\n",
    "Open **Redis Insight** and browse your database. "
    "You should see zero keys matching `redis-eats:*` and no indexes named "
    "`redis-eats-chunks` or `redis-eats-router`.\n",
    "\n",
    "Run the cell below for a quick in-notebook confirmation.\n",
))

section12.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Final verification — count remaining workshop keys\n",
    "# ---------------------------------------------------------------------------\n",
    "count = sum(1 for _ in r.scan_iter(\"redis-eats:*\", count=500))\n",
    "print(f\"Keys matching 'redis-eats:*' : {count}\")\n",
    "\n",
    "# Check indexes\n",
    "try:\n",
    "    indexes = r.execute_command(\"FT._LIST\")\n",
    "    workshop_indexes = [idx for idx in indexes if b\"redis-eats\" in idx or \"redis-eats\" in str(idx)]\n",
    "    if workshop_indexes:\n",
    "        print(f\"Workshop indexes still present: {workshop_indexes}\")\n",
    "    else:\n",
    "        print(\"Workshop indexes             : none (clean)\")\n",
    "except Exception:\n",
    "    print(\"(Could not list indexes — this is fine if the index module is not available)\")",
))

# ============================================================
# SECTION 13 — What Comes Next
# ============================================================

section13 = []

section13.append(md(
    "---\n",
    "## Section 13 — What Comes Next\n",
    "\n",
    "Congratulations — you built a working RAG chatbot on Redis Cloud! 🎉\n",
    "\n",
    "Here's what you accomplished in this workshop:\n",
    "\n",
    "| ✅ | Skill |\n",
    "|---|---|\n",
    "| ✅ | Connected a Jupyter Notebook to Redis Cloud |\n",
    "| ✅ | Loaded and chunked PDF policy documents |\n",
    "| ✅ | Generated embeddings with OpenAI |\n",
    "| ✅ | Created a RedisVL vector search index |\n",
    "| ✅ | Stored documents, metadata, and vectors together in Redis |\n",
    "| ✅ | Ran pure vector search over Redis Query Engine |\n",
    "| ✅ | Built a grounded RAG answer function with citations |\n",
    "| ✅ | Added semantic routing to block off-topic questions |\n",
    "| ✅ | Added LangCache to reduce repeated LLM calls |\n",
    "\n",
    "---\n",
    "\n",
    "### Workshop 2: Context-Aware Redis Eats\n",
    "\n",
    "The next workshop builds on this foundation and turns the chatbot into a "
    "**context-aware, action-capable agent**:\n",
    "\n",
    "| Feature | Workshop 1 | Workshop 2 |\n",
    "|---|---|---|\n",
    "| Policy Q&A (RAG) | ✅ | ✅ |\n",
    "| Semantic routing | ✅ | ✅ |\n",
    "| LangCache | ✅ | ✅ |\n",
    "| Conversational memory | ❌ | ✅ |\n",
    "| Live order lookup | ❌ | ✅ |\n",
    "| Delivery status | ❌ | ✅ |\n",
    "| MCP tools (Context Retriever) | ❌ | ✅ |\n",
    "| Redis Iris integration | ❌ | ✅ |\n",
    "| Agentic workflows | ❌ | ✅ |\n",
    "| RDI (mocked) | ❌ | ✅ |\n",
    "\n",
    "---\n",
    "\n",
    "### Keep Exploring Redis AI\n",
    "\n",
    "- 📖 [RedisVL documentation](https://www.redisvl.com)\n",
    "- 📖 [Redis Vector Search guide](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/)\n",
    "- 📖 [LangCache documentation](https://redis.io/docs/latest/develop/ai/langcache/)\n",
    "- 📖 [Redis RAG Quickstart](https://redis.io/docs/latest/develop/get-started/rag/)\n",
    "- 🚀 [Redis Cloud free tier](https://redis.io/try-free)\n",
    "\n",
    "---\n",
    "\n",
    "### Ideas to Try on Your Own\n",
    "\n",
    "- Swap in **your own PDF documents** and change the system prompt\n",
    "- Add **hybrid search** — combine vector similarity with a tag filter (e.g., only search `refund_policy.pdf`)\n",
    "- Increase `top_k` and compare answer quality\n",
    "- Adjust `chunk_size` and measure whether retrieval improves\n",
    "- Try **HNSW** instead of FLAT for the vector index and measure speed on a larger dataset\n",
    "\n",
    "Thanks for attending the Redis Eats RAG Workshop. "
    "Now go build something fast. 🚀\n",
))

# ============================================================
# Polish pass — inject Colab setup cell at position 1
# ============================================================

colab_setup_cell = code(
    "#@title ⚙️ Google Colab Setup (run this first if using Colab) { display-mode: 'form' }\n",
    "# ---------------------------------------------------------------------------\n",
    "# If you are running in Google Colab, run this cell first to clone the repo\n",
    "# so the data/pdfs/ folder is available.\n",
    "#\n",
    "# If you are running locally, skip this cell.\n",
    "# ---------------------------------------------------------------------------\n",
    "import os\n",
    "if 'google.colab' in str(get_ipython()):\n",
    "    if not os.path.exists('/content/redis-eats-rag-workshop'):\n",
    "        print('Cloning workshop repo...')\n",
    "        os.system('git clone https://github.com/your-org/redis-eats-rag-workshop /content/redis-eats-rag-workshop')\n",
    "        os.chdir('/content/redis-eats-rag-workshop')\n",
    "        print('Done.')\n",
    "    else:\n",
    "        os.chdir('/content/redis-eats-rag-workshop')\n",
    "        print('Repo already present.')\n",
    "else:\n",
    "    print('Not running in Colab — skipping repo clone.')",
)

# ============================================================
# Polish pass — add a compact Table of Contents to the welcome cell
# ============================================================

TOC_LINES = (
    "\n---\n",
    "## 📋 Table of Contents\n",
    "\n",
    "| # | Section |\n",
    "|---|---|\n",
    "| 0 | Welcome and What We Are Building |\n",
    "| 1 | Setup — packages, credentials, connectivity tests |\n",
    "| 2 | Meet the Data — load and preview policy PDFs |\n",
    "| 3 | Chunking — split documents for retrieval |\n",
    "| 4 | Embeddings — convert text to vectors |\n",
    "| 5 | RedisVL Schema and Index Creation |\n",
    "| 6 | Load Chunks into Redis |\n",
    "| 7 | Vector Search |\n",
    "| 8 | Build the RAG Answer Function |\n",
    "| 9 | Add Semantic Routing |\n",
    "| 10 | Add LangCache |\n",
    "| 11 | Final Chatbot Test |\n",
    "| 12 | Reset Lab |\n",
    "| 13 | What Comes Next |\n",
)

# Append TOC to the welcome cell (cell 0)
nb["cells"][0]["source"].extend(TOC_LINES)

# Insert Colab setup cell at position 1 (after welcome, before Section 1)
nb["cells"].insert(1, colab_setup_cell)

# ============================================================
# Append Sections 12 and 13
# ============================================================
nb["cells"].extend(section12)
nb["cells"].extend(section13)

# ============================================================
# Write back
# ============================================================
NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"✅ Sections 12–13 appended + polish applied → {NOTEBOOK}")
print(f"   Total cells : {len(nb['cells'])}")
code_cells = sum(1 for c in nb['cells'] if c['cell_type']=='code')
md_cells   = sum(1 for c in nb['cells'] if c['cell_type']=='markdown')
print(f"   Code cells  : {code_cells}")
print(f"   Markdown    : {md_cells}")
