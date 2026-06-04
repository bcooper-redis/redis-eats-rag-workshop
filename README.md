# Redis Eats RAG Workshop

> **Workshop 1 of 2** — Build a RAG chatbot on Redis Cloud using RedisVL, OpenAI, and LangCache.

Build a working food-delivery support chatbot called **_Don't Talk With Food In Your Mouth_** that retrieves answers from policy documents, refuses off-topic questions, and caches repeated inputs — all backed by Redis Cloud.

---

## What You Will Build

| Step | What Happens | Redis Role |
|---|---|---|
| Load PDFs | 10 food-delivery policy documents | — |
| Chunk + Embed | Split text, generate OpenAI vectors | — |
| Index | Store chunks, metadata, and vectors | **Redis Cloud** + RedisVL SearchIndex |
| Search | Find relevant chunks by meaning | **Redis Query Engine** vector search |
| Generate | Build grounded answers with citations | OpenAI (with Redis-retrieved context) |
| Route | Block off-topic questions before retrieval | **RedisVL SemanticRouter** |
| Cache | Skip repeated LLM calls | **Redis LangCache** |

---

## Target Audience

- Developers who know Redis as a cache and want to explore Redis as an AI application platform
- Redis customers evaluating Redis Cloud for AI/ML workloads
- Anyone building RAG applications and learning how Redis fits in

**Assumed experience:** Basic Python, some Redis familiarity. No prior RAG or LLM experience required.

---

## Prerequisites

Complete these **before** the workshop:

### 1 — Redis Cloud Database

- Sign up free at [redis.io/try-free](https://redis.io/try-free)
- Create a database (free tier is sufficient)
- Save your **host**, **port**, and **password** from the Redis Cloud console

### 2 — OpenAI API Key

- Create a paid account at [platform.openai.com](https://platform.openai.com)
- Generate an API key (`sk-...`) with available credits

### 3 — LangCache Instance *(for Section 10 only)*

- LangCache is available in preview on Redis Cloud
- See [LangCache documentation](https://redis.io/docs/latest/develop/ai/langcache/) for setup
- The notebook runs without LangCache — Section 10 degrades gracefully if credentials are not provided

No local Python installation is required if you use Google Colab.

---

## How to Run

### Option 1 — Google Colab *(recommended)*

1. Open the notebook in Colab:

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/testuser/redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb)

2. Run **cell 1** (the Colab setup cell) to clone the repo and make the data files available
3. Run cells top to bottom
4. Enter your credentials when prompted — nothing is stored to disk

### Option 2 — Local (VS Code or Jupyter)

```bash
git clone https://github.com/testuser/redis-eats-rag-workshop
cd redis-eats-rag-workshop
pip install -r requirements.txt
# Open notebooks/redis_eats_rag_workshop.ipynb in VS Code or Jupyter
```

---

## Expected Duration

**~2 hours** including exercises, checkpoints, and the final chatbot test.

---

## File Structure

```
redis-eats-rag-workshop/
├── README.md
├── requirements.txt                          # Python dependencies
├── .env.example                              # Credential template (optional for local runs)
│
├── notebooks/
│   └── redis_eats_rag_workshop.ipynb         # Main attendee notebook (76 cells)
│
├── data/
│   ├── pdfs/                                 # 10 generated policy PDFs (workshop input)
│   │   ├── refund_policy.pdf
│   │   ├── cancellation_policy.pdf
│   │   ├── delivery_delay_policy.pdf
│   │   ├── driver_support_procedures.pdf
│   │   ├── restaurant_onboarding.pdf
│   │   ├── food_safety_policy.pdf
│   │   ├── promo_code_policy.pdf
│   │   ├── account_login_help.pdf
│   │   ├── order_status_faq.pdf
│   │   └── customer_support_procedures.pdf
│   └── source_markdown/                      # Editable Markdown sources for the PDFs
│       └── *.md
│
├── docs/
│   ├── instructor_guide.md                   # ⚠️ Instructor-only — not for attendees
│   └── architecture/
│       └── redis-eats-rag-workshop-architecture.png
│
├── scripts/
│   ├── generate_policy_pdfs.py               # Regenerate PDFs from Markdown sources
│   ├── generate_architecture_diagram.py      # Regenerate the architecture PNG
│   ├── build_notebook.py                     # Notebook builder — sections 0–8
│   ├── build_notebook_phase4.py              # Notebook builder — sections 9–11
│   └── build_notebook_phase5.py              # Notebook builder — sections 12–13 + polish
│
└── tests/
    └── README.md
```

---

## Notebook Sections

| # | Section | What You Do |
|---|---|---|
| 0 | Welcome | Learn the scenario, architecture, and goals |
| 1 | Setup | Install packages, connect to Redis Cloud and OpenAI |
| 2 | Meet the Data | Load and preview the policy PDFs |
| 3 | Chunking | Split documents into searchable chunks (includes a fill-in exercise) |
| 4 | Embeddings | Generate vectors with `text-embedding-3-small` |
| 5 | Schema + Index | Create a RedisVL `SearchIndex` with a FLAT vector field |
| 6 | Load into Redis | Write chunks, metadata, and vectors to Redis Cloud |
| 7 | Vector Search | Run pure vector similarity search, try your own queries |
| 8 | RAG Answer | Retrieve + generate grounded answers with citations |
| 9 | Semantic Routing | Block off-topic questions with `SemanticRouter` |
| 10 | LangCache | Cache repeated questions to reduce LLM calls |
| 11 | Final Chatbot | Run the complete `ask_bot()` pipeline |
| 12 | Reset Lab | Delete all workshop data and indexes |
| 13 | What's Next | Preview of Workshop 2: context-aware agents |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `❌ Authentication failed` (Redis) | Wrong username or password — copy/paste directly from Redis Cloud console |
| `❌ TLS/SSL error` (Redis) | Ensure `ssl=True`; the URL uses `rediss://` (double-s) |
| `❌ Connection timed out` (Redis) | Wrong host or port, or database not in Active state |
| `❌ Redis Search module NOT found` | Upgrade your Redis Cloud database to a plan that includes the Search module (free tier includes it) |
| `❌ API key invalid` (OpenAI) | Key is wrong or revoked — check at platform.openai.com |
| `❌ rate limit hit or insufficient credits` (OpenAI) | Add billing credits at platform.openai.com/billing — free-tier keys do not work |
| `FileNotFoundError: data/pdfs` | In Colab: run cell 1 to clone the repo. Locally: run `python3 scripts/generate_policy_pdfs.py`. |
| `Index already exists` error | The schema uses `overwrite=True` — re-run the index creation cell. |
| No search results | Check `index.info()` shows `num_docs > 0`. Run Section 6 before Section 7. |
| Routing blocks legitimate questions | Lower `ROUTING_THRESHOLD` in Section 9.3 (try `0.6`). |
| LangCache credentials not available | Section 10 will skip gracefully. Follow the demo visually. |
| Slow embedding step | Normal — ~150 API calls. Takes 30–90 seconds depending on network speed. |

---

## Reset / Cleanup

**Section 12** of the notebook deletes all workshop data:

- Drops the `redis-eats-chunks` vector search index
- Deletes all `redis-eats:chunk:*` keys
- Deletes the `redis-eats-router` semantic router

Cleanup is scoped to the `redis-eats:` key prefix — it will not affect any other data in your database.

To regenerate the data, re-run the notebook from Section 6.

---

## Regenerating Workshop Assets

```bash
# Regenerate the 10 policy PDFs from Markdown sources
python3 scripts/generate_policy_pdfs.py

# Regenerate the architecture diagram PNG
python3 scripts/generate_architecture_diagram.py

# Rebuild the full notebook from source
python3 scripts/build_notebook.py
python3 scripts/build_notebook_phase4.py
python3 scripts/build_notebook_phase5.py
```

---

## What Is Covered in Workshop 1

- Redis Cloud connection and TLS
- PDF loading with `pypdf`
- Character-level chunking with overlap
- OpenAI embeddings (`text-embedding-3-small`, 1536 dims)
- RedisVL `SearchIndex` with FLAT/COSINE vector field
- Redis Query Engine pure vector search
- RAG answer generation with source citations
- Semantic routing with RedisVL `SemanticRouter`
- Semantic caching with Redis LangCache

## What Is Saved for Workshop 2

- Conversational memory
- Agentic workflows
- MCP tools generated by Context Retriever
- Redis Iris components
- Mocked RDI flows
- Context-aware responses (live order lookup, delivery status, account-specific actions)
- Restaurant search and operational workflows
- Function/tool calling

---

## About

This workshop is based on the **Redis Eats / Reddash** domain. It is a standalone learning exercise and does not depend on the live Redis Eats application.

Built with [RedisVL](https://www.redisvl.com) · [Redis Cloud](https://redis.io/try-free) · [OpenAI](https://platform.openai.com) · [LangCache](https://redis.io/docs/latest/develop/ai/langcache/)
