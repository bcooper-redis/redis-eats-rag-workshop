# Redis Eats RAG Workshop — Instructor Guide

> **⚠️ Not for attendees.** This document is for instructors only.
> Keep it out of the public repo or move it to a private branch before sharing.

---

## 1. Workshop Overview

### Session Goal

Teach developers and Redis customers how to build a Retrieval-Augmented Generation (RAG) chatbot using Redis Cloud, RedisVL, OpenAI, and LangCache — in about two hours.

By the end, every attendee should have a working RAG pipeline running against their own Redis Cloud database.

### Target Audience

- Developers who know Redis as a cache and are new to Redis as an AI application platform
- Redis customers exploring the Redis Query Engine and AI workloads
- Developers with some Python experience; Jupyter/RAG experience is helpful but not required

### Expected Attendee Background

| Assumption | Detail |
|---|---|
| Redis caching | Know `SET`, `GET`, TTL, basic key-value patterns |
| Python | Comfortable reading and running Python in a notebook |
| RAG/LLMs | No prior knowledge required — explain from scratch |
| Jupyter/Colab | Basic familiarity; some may be new to notebooks |

### Required Prerequisites (Attendees Set Up Before the Session)

1. **Redis Cloud account** with an active database (free tier is fine)
   - Host, port, and password on hand
2. **OpenAI API key** — paid account with available credits
3. **Python 3.10+** (only for local runs; Colab handles this automatically)
4. **LangCache instance** on Redis Cloud — for Section 10 only (preview feature)

### What Attendees Will Build

A food-delivery support chatbot called *Don't Talk With Food In Your Mouth* that:
- Reads 10 Redis Eats policy PDFs and indexes them in Redis Cloud
- Answers policy questions via vector search + OpenAI
- Returns source citations
- Refuses off-topic questions via semantic routing
- Caches repeated questions via LangCache

### What Is Explicitly Out of Scope

- Conversational memory
- Agentic workflows or function/tool calling
- MCP tools, Context Retriever, Redis Iris
- RDI (mocked or live)
- Web/UI (Streamlit, Gradio)
- Hybrid search (mention briefly as a next step)

---

## 2. Timing Plan

Total target: **2 hours**

| Section | Content | Time |
|---|---|---|
| Pre-start | Confirm Colab/local env, Redis Cloud credentials, OpenAI key | Before session |
| **0 — Welcome** | Scenario intro, architecture diagram, what is RAG | 5 min |
| **1 — Setup** | pip install, imports, credential prompts, connectivity tests | 10 min |
| **2 — Meet the Data** | PDF file list, document preview | 5 min |
| **3 — Chunking** | Extract text, chunk_text(), exercise + solution | 15 min |
| **4 — Embeddings** | get_embedding(), batch all chunks | 10 min |
| **5 — Schema + Index** | IndexSchema, SearchIndex.create() | 10 min |
| **6 — Load into Redis** | index.load(), spot-check a key | 5 min |
| **7 — Vector Search** | VectorQuery, example queries, attendee checkpoint | 15 min |
| **8 — RAG Answer** | build_prompt(), ask_rag(), example battery | 20 min |
| **9 — Semantic Routing** | Routes, SemanticRouter, threshold tuning, checkpoint | 15 min |
| **10 — LangCache** | Cache miss/hit demo, good morning variants | 10 min |
| **11 — Final Chatbot** | ask_bot(), full pipeline test | 5 min |
| **12 — Reset Lab** | index.delete(), router.delete(), verify clean | 5 min |
| **13 — What's Next** | Workshop 2 preview, resources | 5 min |
| **Buffer / Q&A** | Questions, stuck attendees, open discussion | 10 min |
| **Total** | | **~2 hours** |

> **Tip:** The embedding step (Section 4) and PDF loading can run while you talk — don't wait silently.

---

## 3. Instructor Talk Track

### Section 0 — Welcome (5 min)

**Say:**
> "Today we're building the support chatbot for Redis Eats — a fictional food delivery app. The bot's job is to answer customer questions from a set of policy documents. You've probably seen Redis used as a cache. By the end of this workshop you'll see it as a full AI application platform."

**Show** the architecture diagram. Walk through each component:
- "The user asks a question."
- "The SemanticRouter decides: is this question even about food delivery? If not, refuse immediately — no LLM call needed."
- "If it's in-domain, we check LangCache. Have we answered something like this recently? If yes, return it instantly."
- "If cache miss: embed the question, search Redis Cloud for relevant policy chunks, pass them to OpenAI, return the answer with citations."
- "Redis is at the center of every step — routing store, vector database, and cache are all Redis."

**Avoid:** Going deep into LLM theory or embedding math here. Save that for Section 4.

---

### Section 1 — Setup (10 min)

**Say:**
> "Run the pip install cell first — it will take 30–60 seconds. While it runs, find your Redis Cloud credentials in the console."

**Where to pause:**
- After the Redis connectivity cell — make sure every attendee sees `✅ All Redis checks passed` before moving on. The cell runs four sub-checks; if any fail, the specific error message will tell the attendee exactly what to fix.
- After the OpenAI connectivity cell — make sure every attendee sees `✅ All OpenAI checks passed`. This cell tests the embedding model and chat model with real calls, not just the API key — so a zero-credit account will fail here rather than mid-workshop.

**Common mistake:** Attendees enter their host with `https://` or a trailing slash. The host field should be just `redis-xxxxx.c1.us-east-1-2.ec2.redns.redis-cloud.com` — no prefix, no slash.

**Redis positioning:**
> "Notice we're connecting with `rediss://` — that's Redis over TLS. Redis Cloud requires TLS for all external connections. Security is built in."

---

### Section 2 — Meet the Data (5 min)

**Say:**
> "We have 10 policy documents — refunds, cancellations, delivery delays, and so on. These are the documents the chatbot will answer from. Nothing is hard-coded into the bot — all answers come from retrieval. If the answer isn't in the documents, the bot should say so."

**Show** the document preview cell output. Point out the structure: headers, sections, policy language.

**Avoid:** Reading the documents aloud. Just show the preview and move on.

---

### Section 3 — Chunking (15 min)

**Say:**
> "We can't store a whole PDF as one vector. Embedding models compress text into a fixed number of dimensions — the longer and more varied the text, the less precise that compression is. We split each document into overlapping chunks so each chunk has one focused idea."

**Emphasize:**
- Overlap preserves context at chunk boundaries — "imagine a sentence that spans two chunks without overlap. You'd lose half the sentence from each vector."
- Chunk size is a tunable hyperparameter, not a fixed rule.

**Exercise:** Give attendees 3–4 minutes to try different `chunk_size` values in the exercise cell. Then walk through the collapsible solution.

**Expected questions:**
- *"What's the right chunk size?"* → "There's no universal answer. For short policy docs like these, 400–600 characters works well. For dense technical docs, you might go larger. Always measure retrieval quality."
- *"Why characters, not tokens?"* → "Token-based chunking is more precise but adds complexity. Character chunking is easier to reason about and works fine for a workshop. In production you'd likely use token-based chunking."

---

### Section 4 — Embeddings (10 min)

**Say:**
> "An embedding is a list of numbers — 1536 numbers for the model we're using — that represents the meaning of a piece of text. Texts that mean similar things will produce similar vectors. This is what makes semantic search work: we're not matching keywords, we're matching meaning."

**Show** the test embedding output. Point out:
- "1536 dimensions — that's `text-embedding-3-small`. Every chunk and every query will be in this same 1536-dimensional space."

**While the batch embedding runs:**
> "This is calling the OpenAI API once per chunk — about 150 calls for our dataset. In a production system you'd batch these. While this runs, let me explain what's happening inside Redis next..."

**Redis positioning:**
> "OpenAI gives us the vectors. Redis stores them. The two work together — but Redis is your data layer. You own the vectors, the metadata, and the search index."

---

### Section 5 — RedisVL Schema and Index (10 min)

**Say:**
> "If you've used Redis as a cache, you've probably never needed a schema or an index. That's because a cache is a simple key-value lookup. What we're building here is different — we need to query by semantic similarity across thousands of documents. For that, Redis needs an index."

**Walk through the schema dict on screen:**
- "`text` — the chunk content, full-text indexed"
- "`source` — which PDF did this come from, stored as a tag"
- "`page_number` and `chunk_index` — metadata for citations"
- "`embedding` — the vector field. FLAT algorithm means exact nearest-neighbor search. COSINE distance. 1536 dimensions to match our OpenAI model."

**Emphasize FLAT vs HNSW:**
> "We're using FLAT — exact brute force search. For ~150 vectors this is instant. In production with millions of vectors you'd switch to HNSW for approximate but much faster search. Redis supports both."

**Expected questions:**
- *"Why not just search all the keys?"* → "Redis Query Engine indexes the vectors at write time so search is sub-millisecond, not a full scan."
- *"Can I filter by source document?"* → "Yes — that's hybrid search. We're keeping it pure vector today, but adding a tag filter is one line of code. Workshop 2 will cover this."

---

### Section 6 — Load into Redis (5 min)

**Say:**
> "Now we write everything to Redis Cloud in one shot. Each chunk becomes a Redis Hash at a key like `redis-eats:chunk:<uuid>`. The hash stores the text, metadata, and the embedding vector together. One data structure, one place."

**Redis positioning:**
> "This is the Redis advantage for AI apps: content, metadata, and vectors live in the same store. You're not maintaining a separate vector database and a separate metadata store. Redis keeps it unified."

**Show** the spot-check cell output. Point out the embedding bytes: "768 bytes = 192 float32 values... wait, 1536 dimensions × 4 bytes per float32 = 6144 bytes. That's the full vector stored inline in the hash."

---

### Section 7 — Vector Search (15 min)

**Say:**
> "Here's the payoff. We embed a question — same model, same space — and ask Redis to find the most similar chunks. The score you see is cosine distance: lower means more similar. Zero would be identical."

**Walk through example results:**
- Show the source filenames in the results — "notice it's pulling from `refund_policy.pdf` for a refund question. The retrieval is already working."

**Attendee checkpoint:** Give 3–5 minutes for attendees to type their own food-delivery question.

**Watch for:** Attendees asking questions like "who is the CEO of Redis?" — they'll get a result (some chunk will be the nearest neighbor) but it won't be relevant. That's the problem semantic routing solves in Section 9.

---

### Section 8 — RAG Answer Function (20 min)

**Say:**
> "Vector search gives us the most relevant chunks. Now we turn those chunks into an answer. The key idea: we put the chunks into the prompt as context, and we tell the LLM to answer *only from that context*. This is what grounds the model — it can't make things up because we're telling it to use only what we retrieved."

**Walk through the system prompt:**
> "The system prompt is the personality and constraints of the bot. 'Answer only from the policy information provided' — this is important. Without that instruction, the LLM would happily answer from its training data and potentially hallucinate."

**Show `build_prompt()` output:**
- Point out the `[Source: refund_policy.pdf, Page: 1]` annotations in the context.
- "These come back as citations. The user sees where every answer came from."

**Run the full example battery.** Let it run and read through a couple of answers aloud.

**Redis positioning:**
> "OpenAI is generating the words. But Redis is doing the retrieval — finding exactly the right policy content from 150 chunks in milliseconds. The answer quality depends on the retrieval quality, and retrieval quality depends on Redis."

---

### Section 9 — Semantic Routing (15 min)

**Say:**
> "The RAG pipeline works great for food delivery questions. But what happens when someone asks 'Who won the Super Bowl?' Without a guard, the bot would still embed that question, search Redis, find the *least irrelevant* chunks, and make up an answer. That's wasteful and could confuse customers."

**Show the blocked question test first** — walk through "Who won the Super Bowl?" hitting `None` from the router.

**Explain the routing mechanism:**
> "The SemanticRouter stores the utterances we defined — representative examples of each route — as vectors in Redis. When a new question arrives, it embeds the question and finds the closest route. If nothing is close enough, it returns None and we refuse immediately. No retrieval. No LLM call."

**Emphasize threshold tuning:**
> "The threshold is a dial, not a switch. Too strict and you'll block legitimate questions. Too loose and you'll let irrelevant things through. Start at 0.5, measure how it behaves with your real traffic, and adjust."

**Expected questions:**
- *"What if a legitimate question doesn't match any route?"* → "That's the risk with strict thresholds. Add more utterances to your routes, or lower the threshold. Routing is a living configuration."
- *"Can routes overlap?"* → "Yes, and that's fine — the router picks the closest one."

---

### Section 10 — LangCache (10 min)

**Say:**
> "Even with routing, we can still burn LLM calls on repeated questions. A Redis customer noticed that a huge fraction of their support traffic was just people typing 'good morning' in the chat widget. Every single one triggered an LLM call. LangCache solves this with semantic caching."

**Walk through the good morning demo:**
- "First call — cache miss. We call OpenAI, store the response."
- "Second call, slightly different phrasing — cache hit. Returned instantly, no LLM call."
- "Point at the latency numbers — notice the cache hit is significantly faster."

**LangCache vs roll your own:**
> "You could build this yourself with RedisVL — define a schema, create an index, write the search and store logic. But LangCache is already built, already tuned, and it lives in Redis Cloud alongside everything else. Less code, less maintenance."

**If LangCache is not available:** Walk through the code conceptually. The pattern is identical to the RAG retrieval pattern — embed, search, store — just applied to prompt/response pairs instead of document chunks.

---

### Section 11 — Final Chatbot Test (5 min)

**Say:**
> "Now we put it all together. `ask_bot()` is the complete pipeline — route, cache, retrieve, generate, store. Run the success questions, then run the blocked ones."

Let the cells run. Read one answer aloud and point out the citations.

> "This is what your Redis Cloud database just did: routed the question semantically, checked the cache semantically, retrieved the context by vector similarity, and served the grounded answer — all in Redis."

---

### Section 12 — Reset Lab (5 min)

**Say:**
> "Before we close, let's clean up. Every key we wrote — the chunk hashes, the router embeddings — gets deleted. The index gets dropped. Your Redis Cloud database goes back to its pre-workshop state."

**Why this matters:**
> "In a shared environment or if you're using a database you'll keep, it's good hygiene to scope your workshop data and clean it up. We scoped every key with `redis-eats:` so the cleanup is surgical."

---

### Section 13 — What Comes Next (5 min)

See Section 7 of this guide for the Workshop 2 transition talk track.

---

## 4. Redis Positioning Points

Use these talking points throughout the session. Return to them whenever attendees might anchor on OpenAI or "the LLM" as the hero.

| Positioning Point | When to Use |
|---|---|
| "Redis is not just a cache" | Section 0, Section 5 (index creation) |
| "Redis Cloud is the required database" | Section 1 (connection test) |
| "RedisVL makes AI app development easier" | Section 5, Section 9 |
| "Content, metadata, and vectors together in one store" | Section 6 |
| "Redis Query Engine enables vector similarity search" | Section 7 |
| "OpenAI provides the vectors and the words — Redis stores and finds" | Section 4, Section 8 |
| "Semantic routing controls what the bot should and shouldn't answer" | Section 9 |
| "LangCache is the recommended semantic caching approach, not roll-your-own" | Section 10 |
| "Workshop 2 adds context-aware and agentic behavior on top of this foundation" | Section 13 |

**Avoid:**
- Positioning OpenAI or any non-Redis vendor as strategic parts of the story
- Saying things like "this is basically a ChatGPT wrapper"
- Spending more than 2 minutes on LLM theory

---

## 5. Common Attendee Issues

### Redis Connection Failures

The Redis connectivity cell now runs four sub-checks and prints a specific error message for each type of failure. Use the table below to diagnose quickly.

| Symptom in notebook | Cause | Fix |
|---|---|---|
| `❌ Authentication failed` | Wrong username or password | Copy/paste password directly from Redis Cloud console |
| `❌ TLS/SSL error` | TLS not configured correctly | Confirm `ssl=True`; URL must use `rediss://` (double-s) |
| `❌ Connection timed out` | Wrong host or port, or DB not Active | Check host has no `https://` prefix; verify DB is Active in console |
| `❌ Redis Search module NOT found` | Database plan doesn't include Search | Upgrade to a Redis Cloud plan that includes the Search module (free tier includes it) |
| `❌ RedisVL connection failed` | REDIS_URL format is wrong | Usually caused by a space in the host or password — re-enter credentials |

**Instructor fallback:** If one attendee is blocked, have them watch your screen while you proceed. Resolve credential issues during the exercise breaks.

---

### OpenAI API Key Issues

The OpenAI connectivity cell tests the API key, the embedding model, and the chat model with real calls. Symptoms now distinguish auth failures from quota/credit failures.

| Symptom in notebook | Cause | Fix |
|---|---|---|
| `❌ API key invalid` | Key is wrong or revoked | Check key on platform.openai.com — regenerate if needed |
| `❌ API key does not have permission` | Free-tier or restricted key | A paid account key is required |
| `❌ Embedding model — rate limit hit or insufficient credits` | Zero account balance | Add credits at platform.openai.com/billing |
| `❌ Chat model — rate limit hit or insufficient credits` | Zero account balance | Same as above |
| `⚠️ Embedding model returned N dims (expected 1536)` | Wrong model name | Should not happen with the defaults; verify `EMBEDDING_MODEL` is `text-embedding-3-small` |

**Common cause of silent failures in the old check:** A key with $0 credits passed `models.list()` but then failed when the batch embedding started. The new check catches this early with a real embedding call.

---

### Missing Packages in Colab

**Symptom:** `ModuleNotFoundError` for `redisvl`, `langcache`, etc.

**Resolution:** The `%pip install` cell at the top of the notebook installs all dependencies. Make sure attendees ran it. If they got an error during install, re-run the cell. If the problem persists, check for internet connectivity in Colab (some corporate environments restrict this).

---

### PDF Files Not Found

**Symptom:** `FileNotFoundError: Could not find data/pdfs/`.

**Colab:** Remind attendees to run the Colab setup cell (cell 1) which clones the repo. Without this, the data folder is missing.

**Local:** The attendee needs to run `python3 scripts/generate_policy_pdfs.py` from the repo root, or ensure they cloned the full repo (not just the notebook).

---

### Empty Chunks

**Symptom:** `all_chunks` has 0 or very few entries; chunk text is empty or whitespace.

**Cause:** `pypdf` extraction failed for one or more PDFs — usually a malformed or image-only PDF.

**Resolution:** Re-run `scripts/generate_policy_pdfs.py` to regenerate the PDFs from the Markdown sources. The generated PDFs are text-based and parse cleanly.

---

### Index Already Exists

**Symptom:** Error during index creation mentioning the index already exists.

**Resolution:** The schema creation call uses `overwrite=True` which should handle this automatically. If the error persists, the attendee can manually drop the index:
```python
r.execute_command("FT.DROPINDEX", "redis-eats-chunks", "DD")
```

---

### No Search Results

**Symptom:** `search_chunks()` returns an empty list.

**Causes:**
1. Data was not loaded — check `index.info()` shows `num_docs > 0`
2. The index was just created but data hasn't synced yet — wait 1–2 seconds and retry
3. `top_k` is larger than the number of indexed documents — reduce it
4. Query vector has wrong dimensions — check `len(query_vector) == 1536`

---

### Semantic Routing — Too Strict (Blocking Legitimate Questions)

**Symptom:** In-domain food delivery questions return `None` from the router.

**Resolution:** Lower `ROUTING_THRESHOLD` in the threshold tuning cell (Section 9.3). Try `0.6` or `0.65`. The threshold is cosine distance — lower values are more permissive.

---

### Semantic Routing — Too Permissive (Passing Irrelevant Questions)

**Symptom:** "Who won the Super Bowl?" returns a route match.

**Resolution:** Raise `ROUTING_THRESHOLD`. Try `0.4` or `0.35`. Alternatively, add more specific utterances to the in-domain routes so the router better understands the shape of legitimate questions.

---

### LangCache Not Available

**Symptom:** Attendee does not have a LangCache instance provisioned.

**This is expected for some attendees.** The notebook handles this gracefully — `LANGCACHE_AVAILABLE` is set to `False` and the demo falls back to direct LLM calls with a printed notice.

Walk through the LangCache cells conceptually. The pattern is identical to vector search — embed, find nearest, store. The only difference is that you're caching prompt/response pairs instead of document chunks.

---

## 6. Expected Outputs

Use these as reference during the session.

### Section 1 — Redis Connectivity Test
```
Checking Redis Cloud connectivity...

  ✅ TCP + TLS connection  OK
  ✅ Redis version         7.4.0  (Redis Query Engine supported)
  ✅ Redis Search module   loaded  (FT.CREATE and vector search ready)
  ✅ RedisVL connection    OK  (REDIS_URL is valid for SearchIndex)

✅ All Redis checks passed — ready to continue
   Host    : redis-xxxxx.c1.us-east-1-2.ec2.redns.redis-cloud.com:6379
   User    : default
```

### Section 1 — OpenAI Connectivity Test
```
Checking OpenAI connectivity...

  ✅ API key               valid
  ✅ Embedding model       text-embedding-3-small  (1536 dims)
  ✅ Chat model            gpt-4o-mini  (test response: 'ready')

✅ All OpenAI checks passed — ready to continue
```

### Section 2 — PDF File List
```
Found 10 PDFs in ../data/pdfs

  📄 account_login_help.pdf
  📄 cancellation_policy.pdf
  📄 customer_support_procedures.pdf
  📄 delivery_delay_policy.pdf
  📄 driver_support_procedures.pdf
  📄 food_safety_policy.pdf
  📄 order_status_faq.pdf
  📄 promo_code_policy.pdf
  📄 refund_policy.pdf
  📄 restaurant_onboarding.pdf
```

### Section 3 — Chunking
```
Total chunks: ~150–200
Average chunk length: ~450 chars

Sample chunk from 'refund_policy.pdf' (page 1):
Redis Eats is committed to ensuring every customer has a great experience...
```

### Section 4 — Embedding Test
```
✅ Embedding generated
   Dimensions : 1536
   First 5 values: [0.0121, -0.0432, 0.0891, ...]
```

### Section 5 — Index Creation
```
✅ Index 'redis-eats-chunks' created on Redis Cloud
   Num docs indexed : 0
```
*(Docs are zero until Section 6 loads them.)*

### Section 6 — Load into Redis
```
✅ Loaded 163 chunks into Redis Cloud
   Sample key: redis-eats:chunk:3f2a1b9c-...
   Index reports 163 documents indexed
```
*(Exact count depends on PDF content and chunk settings.)*

### Section 7 — Vector Search
```
Top 3 results for 'Can I get a refund if my food arrived cold?'

  [1] source=refund_policy.pdf  page=1  score=0.0821
      You may be eligible for a full or partial refund in the following situations...

  [2] source=refund_policy.pdf  page=1  score=0.1203
      Approved refunds are issued in one of two ways...

  [3] source=customer_support_procedures.pdf  page=1  score=0.2105
      When you contact support...
```
*(Scores are cosine distance — lower = more relevant.)*

### Section 8 — RAG Answer
```
Question : Can I get a refund if my food arrived cold?

Answer   :
Yes, you may be eligible for a refund if your food arrived cold. According to
the Redis Eats Refund Policy, food quality issues — including food that arrived
cold — are listed as a qualifying reason for a refund. You should submit your
request within 48 hours of delivery through the app under Order History >
Report a Problem.

Sources  : refund_policy.pdf (page 1), customer_support_procedures.pdf (page 1)
```

### Section 9 — Routing
```
--- ALLOWED QUESTIONS ---
  ✅ routed → food_delivery_support
  Q: Can I get a refund if my food arrived cold?
  ...

--- BLOCKED QUESTIONS ---
  ✅ blocked → refusal sent
  Q: Who won the Super Bowl?
  ...
```

### Section 9 — Refusal
```
Question : Who won the Super Bowl?
Route    : [out-of-domain — refused]

Answer   : I can't answer that question. I'm a food delivery bot.
```

### Section 10 — LangCache Demo
```
Similarity threshold: 0.85
=======================================================
  🔄 CACHE MISS | 'good morning' — calling LLM...
     Response   : Good morning! Welcome to Redis Eats support...
     Stored in cache ✅
     Latency    : 1.23s

  📦 CACHE HIT  | 'Good morning!'
     Response   : Good morning! Welcome to Redis Eats support...
     Latency    : 0.08s

  📦 CACHE HIT  | 'hey, good morning'
     Response   : Good morning! Welcome to Redis Eats support...
     Latency    : 0.07s
```

### Section 12 — Reset Lab
```
Starting Redis Eats workshop cleanup...

✅ Vector search index 'redis-eats-chunks' dropped
✅ No stray chunk keys found (index.delete() cleaned them up)
✅ SemanticRouter 'redis-eats-router' deleted

✅ All redis-eats:* keys removed — database is clean

🏁 Reset complete. Your Redis Cloud database is back to its pre-workshop state.
```

---

## 7. Workshop 1 to Workshop 2 Transition

### Talk Track

Use this at the end of Section 13 or during closing Q&A.

> "What you built today is a solid foundation. The bot answers questions correctly, it refuses things it shouldn't answer, and it avoids redundant LLM calls. But it has real limitations."
>
> "It doesn't know who you are. Every question starts from zero — no memory of the previous exchange, no knowledge of your order history, no idea which restaurant you ordered from."
>
> "It doesn't take action. It can tell you what the refund policy says, but it can't actually issue you a refund."
>
> "Workshop 2 changes that. We'll add Context Retriever to generate MCP tools from live Redis data — tools the agent can call to look up your actual order, check delivery status, or trigger a support workflow. We'll add Redis Iris for context-aware memory. We'll add mocked RDI flows so the agent can simulate operational actions. The RAG chatbot becomes an agent."
>
> "The foundation you built today — the vector index, the router, the LangCache layer — all of that carries forward. Workshop 2 builds on top of it. Nothing gets thrown away."

### Key Points to Emphasize

- Workshop 1 = **grounded retrieval** — answers from documents
- Workshop 2 = **context-aware action** — answers from live data + the ability to act
- The Redis stack grows: vector search → routing → caching → memory → tools → agents
- Redis Cloud is the persistent layer throughout both workshops

---

## 8. Delivery Guidance

### Keep the Session Moving

- Do not debug individual setup issues live for more than 2 minutes. If an attendee is stuck, move on and offer to help during an exercise break.
- The embedding step (Section 4) and PDF loading can run in the background while you talk. Do not wait in silence.
- Have your own Redis Cloud database and OpenAI key ready as instructor fallback. If something breaks on your demo machine, you can switch to the attendee view.

### Instructor Fallback Setup

Before the session, pre-run Sections 1–6 on your own machine or Colab instance:
- Verify all 10 PDFs load
- Verify all chunks are indexed
- Verify `ask_rag()` works on at least 3 example questions
- Note your chunk count (typically 150–200)

Keep a terminal open with `redis-cli -u $REDIS_URL ping` so you can verify connectivity instantly if needed.

### Avoid Making This an OpenAI Tutorial

Attendees may gravitate toward questions about prompt engineering, GPT model comparisons, or fine-tuning. Acknowledge the question briefly and redirect:

> "Great question about prompting — that's important for quality, and we can explore it after. For now I want to make sure we understand the *retrieval* side, which is where Redis lives."

### Happy Path as Source of Truth

If anything goes wrong, return to the happy path. The notebook is designed to run top-to-bottom cleanly on the happy path. Trust it.

Do not improvise by changing models, chunk sizes, or index configurations mid-session unless it directly unblocks a broken attendee.

### One More Tip

At the end of the vector search section (Section 7), pause and ask:

> "How many of you expected Redis to do this?"

The answer is almost always "none of us." That moment — when attendees realize Redis is running the semantic search — is the workshop's inflection point. Let it land.

---

*Guide version: Workshop 1 — Redis Eats RAG Chatbot*
*Companion workshop: Redis Eats Agentic (Workshop 2) — context-aware, tool-using agent*
