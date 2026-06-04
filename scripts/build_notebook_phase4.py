"""
build_notebook_phase4.py

Appends Sections 9–11 (Semantic Routing, LangCache, Final Chatbot Test)
to the existing notebook produced by build_notebook.py.

Run AFTER build_notebook.py:
    python3 scripts/build_notebook_phase4.py
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
NOTEBOOK  = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"

# ---------------------------------------------------------------------------
# Cell builders (same helpers as build_notebook.py)
# ---------------------------------------------------------------------------

def md(*lines):
    """Create a markdown cell."""
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}

def code(*lines, tags=None):
    """Create a code cell."""
    meta = {"tags": tags} if tags else {}
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": meta,
        "outputs": [],
        "source": list(lines),
    }

# ---------------------------------------------------------------------------
# New cells for Sections 9 – 11
# ---------------------------------------------------------------------------
new_cells = []

# ============================================================
# SECTION 9 — Semantic Routing
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 9 — Semantic Routing\n",
    "\n",
    "### Why Route Before Retrieval?\n",
    "\n",
    "Without a guard, users could ask our chatbot anything:\n",
    "\n",
    "> *\"Write me a poem about databases.\"*  \n",
    "> *\"Who won the Super Bowl?\"*  \n",
    "> *\"How do I invest in stocks?\"*\n",
    "\n",
    "The RAG pipeline would dutifully embed those questions, search Redis, find the "
    "least-irrelevant chunks, and spend money calling OpenAI — all to produce a "
    "confused or hallucinated answer.\n",
    "\n",
    "**Semantic routing** intercepts each question *before* retrieval and decides: "
    "*Is this question in-domain?* If not, return a refusal immediately — "
    "no embedding, no search, no LLM call.\n",
    "\n",
    "### RedisVL SemanticRouter\n",
    "\n",
    "RedisVL's `SemanticRouter` stores route definitions in Redis and uses vector "
    "similarity to match incoming questions. Routes are defined by **utterances** — "
    "example phrases that represent that category.\n",
    "\n",
    "Our routes:\n",
    "\n",
    "| Route | Covers |\n",
    "|---|---|\n",
    "| `food_delivery_support` | Refunds, delays, missing items, order issues |\n",
    "| `account_and_login` | Password reset, account settings, payment methods |\n",
    "| `restaurant_procedures` | Menu management, hours, onboarding, pausing orders |\n",
    "| `driver_procedures` | Driver pay, delivery issues, safety, pickups |\n",
    "| `out_of_domain` | Anything not food-delivery related → refused |\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Import RedisVL SemanticRouter components\n",
    "# ---------------------------------------------------------------------------\n",
    "from redisvl.extensions.router import SemanticRouter, Route\n",
    "\n",
    "print(\"✅ SemanticRouter imported\")",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Define semantic routes\n",
    "#\n",
    "# Each Route has a name and a list of utterances — representative phrases\n",
    "# that describe questions belonging to that route.\n",
    "#\n",
    "# More diverse utterances = better coverage of different phrasings.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "# Route 1: food delivery support and policy questions\n",
    "route_food_delivery = Route(\n",
    "    name=\"food_delivery_support\",\n",
    "    utterances=[\n",
    "        \"Can I get a refund for my order?\",\n",
    "        \"My food arrived cold, what can I do?\",\n",
    "        \"My order never arrived.\",\n",
    "        \"What happens if my delivery is late?\",\n",
    "        \"I want to cancel my order.\",\n",
    "        \"My delivery is taking too long.\",\n",
    "        \"Wrong items were delivered to me.\",\n",
    "        \"How do I report a missing item?\",\n",
    "        \"How do promo codes work?\",\n",
    "        \"My promo code is not working.\",\n",
    "        \"Is my food safe to eat?\",\n",
    "        \"The food was damaged when it arrived.\",\n",
    "    ],\n",
    ")\n",
    "\n",
    "# Route 2: account and login help\n",
    "route_account = Route(\n",
    "    name=\"account_and_login\",\n",
    "    utterances=[\n",
    "        \"How do I reset my password?\",\n",
    "        \"I can't log in to my account.\",\n",
    "        \"How do I update my email address?\",\n",
    "        \"How do I add a new payment method?\",\n",
    "        \"I want to delete my account.\",\n",
    "        \"How do I enable two-factor authentication?\",\n",
    "        \"My account has been locked.\",\n",
    "        \"How do I change my delivery address?\",\n",
    "    ],\n",
    ")\n",
    "\n",
    "# Route 3: restaurant and merchant procedures\n",
    "route_restaurant = Route(\n",
    "    name=\"restaurant_procedures\",\n",
    "    utterances=[\n",
    "        \"How do I pause orders on Redis Eats?\",\n",
    "        \"How do I update my restaurant menu?\",\n",
    "        \"How do I change my restaurant hours?\",\n",
    "        \"How does restaurant onboarding work?\",\n",
    "        \"When do restaurants get paid?\",\n",
    "        \"How do I become a Redis Eats restaurant partner?\",\n",
    "        \"What commission does Redis Eats charge restaurants?\",\n",
    "        \"How do I manage my menu on the platform?\",\n",
    "    ],\n",
    ")\n",
    "\n",
    "# Route 4: driver and delivery procedures\n",
    "route_driver = Route(\n",
    "    name=\"driver_procedures\",\n",
    "    utterances=[\n",
    "        \"How do I report a problem during a delivery?\",\n",
    "        \"What do I do if the restaurant isn't ready?\",\n",
    "        \"How does driver pay work?\",\n",
    "        \"How do I appeal a driver account suspension?\",\n",
    "        \"What do I do if the customer doesn't answer?\",\n",
    "        \"How do I contact driver support?\",\n",
    "        \"Is my delivery partner account active?\",\n",
    "        \"How do I report a safety incident as a driver?\",\n",
    "    ],\n",
    ")\n",
    "\n",
    "print(\"✅ Routes defined\")\n",
    "print(f\"   food_delivery_support : {len(route_food_delivery.utterances)} utterances\")\n",
    "print(f\"   account_and_login     : {len(route_account.utterances)} utterances\")\n",
    "print(f\"   restaurant_procedures : {len(route_restaurant.utterances)} utterances\")\n",
    "print(f\"   driver_procedures     : {len(route_driver.utterances)} utterances\")",
))

new_cells.append(md(
    "### 9.1 — Create the SemanticRouter\n",
    "\n",
    "RedisVL stores the route embeddings in Redis and performs vector similarity "
    "when a new question arrives. The router reuses the same Redis connection "
    "as our search index — Redis is the backend for both.\n",
    "\n",
    "The **threshold** controls how confident the router must be before assigning "
    "a route. We'll explore tuning this in the checkpoint below.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Create the SemanticRouter\n",
    "#\n",
    "# The router embeds each utterance and stores them in Redis.\n",
    "# At query time it embeds the incoming question and finds the closest route.\n",
    "#\n",
    "# routing_threshold: cosine distance threshold (0.0–1.0)\n",
    "#   Lower = stricter (fewer matches, more refusals)\n",
    "#   Higher = looser  (more matches, some false positives)\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "ROUTING_THRESHOLD = 0.5   # Starting point — we'll tune this below\n",
    "\n",
    "router = SemanticRouter(\n",
    "    name=\"redis-eats-router\",\n",
    "    routes=[route_food_delivery, route_account, route_restaurant, route_driver],\n",
    "    routing_threshold=ROUTING_THRESHOLD,\n",
    "    redis_url=REDIS_URL,\n",
    "    overwrite=True,   # Drop and recreate if already exists from a prior run\n",
    ")\n",
    "\n",
    "print(f\"✅ SemanticRouter 'redis-eats-router' created\")\n",
    "print(f\"   Routes           : {[r.name for r in router.routes]}\")\n",
    "print(f\"   Routing threshold: {ROUTING_THRESHOLD}\")",
))

new_cells.append(md(
    "### 9.2 — Test the Router\n",
    "\n",
    "Let's see the router classify both allowed and blocked questions.\n",
    "\n",
    "- **Matched route** → question is in-domain, proceed to RAG\n",
    "- **No match (None)** → question is out-of-domain, refuse immediately\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Test the router on a set of allowed and blocked questions\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "allowed_questions = [\n",
    "    \"Can I get a refund if my food arrived cold?\",\n",
    "    \"What happens if my delivery is late?\",\n",
    "    \"How do I reset my account password?\",\n",
    "    \"What should a restaurant do if they need to pause orders?\",\n",
    "    \"How does driver pay work?\",\n",
    "]\n",
    "\n",
    "blocked_questions = [\n",
    "    \"Who won the Super Bowl?\",\n",
    "    \"What is the weather in Chicago?\",\n",
    "    \"Write me a poem about databases.\",\n",
    "    \"How do I invest in stocks?\",\n",
    "    \"What is the capital of France?\",\n",
    "]\n",
    "\n",
    "REFUSAL_MESSAGE = \"I can't answer that question. I'm a food delivery bot.\"\n",
    "\n",
    "print(\"--- ALLOWED QUESTIONS ---\")\n",
    "for q in allowed_questions:\n",
    "    route_match = router(q)          # Returns a RouteMatch or None\n",
    "    name = route_match.name if route_match else None\n",
    "    status = f\"✅ routed → {name}\" if name else \"⚠️  no match (consider lowering threshold)\"\n",
    "    print(f\"  {status}\")\n",
    "    print(f\"  Q: {q}\")\n",
    "    print()\n",
    "\n",
    "print(\"--- BLOCKED QUESTIONS ---\")\n",
    "for q in blocked_questions:\n",
    "    route_match = router(q)\n",
    "    name = route_match.name if route_match else None\n",
    "    if name:\n",
    "        status = f\"⚠️  incorrectly matched → {name} (consider raising threshold)\"\n",
    "    else:\n",
    "        status = f\"✅ blocked → refusal sent\"\n",
    "    print(f\"  {status}\")\n",
    "    print(f\"  Q: {q}\")\n",
    "    print()",
))

new_cells.append(md(
    "### 9.3 — Threshold Tuning\n",
    "\n",
    "The `routing_threshold` controls the distance cutoff. Try different values below.\n",
    "\n",
    "| Threshold | Effect |\n",
    "|---|---|\n",
    "| `0.3` | Very strict — only very close matches are routed |\n",
    "| `0.5` | Balanced — good default for this workshop |\n",
    "| `0.7` | Lenient — more questions pass through, some false positives |\n",
    "\n",
    "> **Workshop default:** `0.5`\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Threshold tuning — change ROUTING_THRESHOLD and re-run this cell\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "ROUTING_THRESHOLD = 0.5   # Try 0.3, 0.5, 0.7 and observe the difference\n",
    "\n",
    "# Update the router's threshold without recreating it\n",
    "router.routing_threshold = ROUTING_THRESHOLD\n",
    "\n",
    "# Quick test on an edge-case question\n",
    "test_questions = [\n",
    "    \"My order is messed up\",          # Vague but in-domain\n",
    "    \"Tell me something interesting\",   # Vague and out-of-domain\n",
    "    \"help\",                            # Very short — should be out-of-domain\n",
    "]\n",
    "\n",
    "print(f\"Threshold = {ROUTING_THRESHOLD}\")\n",
    "print()\n",
    "for q in test_questions:\n",
    "    match = router(q)\n",
    "    result = match.name if match else \"→ REFUSED\"\n",
    "    print(f\"  '{q}'\")\n",
    "    print(f\"   {result}\\n\")",
))

new_cells.append(md(
    "### 9.4 — RAG With Routing\n",
    "\n",
    "Now we combine routing with the RAG pipeline from Section 8. "
    "Every question passes through the router first. "
    "Out-of-domain questions never reach Redis or OpenAI.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# RAG pipeline with semantic routing guard\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "def ask_with_routing(\n",
    "    question: str,\n",
    "    top_k: int = 5,\n",
    "    verbose: bool = True,\n",
    ") -> Dict[str, Any]:\n",
    "    \"\"\"\n",
    "    Answer a question using semantic routing + RAG.\n",
    "\n",
    "    Flow:\n",
    "      1. Route the question via SemanticRouter\n",
    "      2. If out-of-domain → refuse immediately (no Redis search, no LLM call)\n",
    "      3. If in-domain     → run the full RAG pipeline from Section 8\n",
    "\n",
    "    Args:\n",
    "        question: The user's question.\n",
    "        top_k:    Number of chunks to retrieve if in-domain.\n",
    "        verbose:  If True, print the result.\n",
    "\n",
    "    Returns:\n",
    "        Dict with 'answer', 'citations', and 'route' keys.\n",
    "    \"\"\"\n",
    "    # Step 1: Route the question\n",
    "    route_match = router(question)\n",
    "    route_name  = route_match.name if route_match else None\n",
    "\n",
    "    # Step 2: Refuse if out-of-domain\n",
    "    if route_name is None:\n",
    "        if verbose:\n",
    "            print(f\"Question : {question}\")\n",
    "            print(f\"Route    : [out-of-domain — refused]\")\n",
    "            print(f\"\\nAnswer   : {REFUSAL_MESSAGE}\")\n",
    "        return {\"answer\": REFUSAL_MESSAGE, \"citations\": [], \"route\": None}\n",
    "\n",
    "    # Step 3: In-domain — run the RAG pipeline\n",
    "    if verbose:\n",
    "        print(f\"Question : {question}\")\n",
    "        print(f\"Route    : {route_name}\")\n",
    "\n",
    "    result = ask_rag(question, top_k=top_k, verbose=verbose)\n",
    "    result[\"route\"] = route_name\n",
    "    return result\n",
    "\n",
    "\n",
    "# Test: in-domain question\n",
    "print(\"=\" * 60)\n",
    "ask_with_routing(\"Can I get a refund if my food arrived cold?\")\n",
    "print()\n",
    "\n",
    "# Test: out-of-domain question\n",
    "print(\"=\" * 60)\n",
    "ask_with_routing(\"Who won the Super Bowl?\")",
))

new_cells.append(md(
    "### ✅ Checkpoint — Routing in Action\n",
    "\n",
    "Run the cell below and try both an allowed and a blocked question. "
    "Notice that blocked questions get an immediate refusal — "
    "**no embedding, no Redis search, no OpenAI call**.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# YOUR TURN — try an allowed and a blocked question\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "print(\"=\" * 60)\n",
    "ask_with_routing(\"How do promo codes work?\")          # in-domain\n",
    "print()\n",
    "print(\"=\" * 60)\n",
    "ask_with_routing(\"What is the capital of France?\")    # out-of-domain",
))

# ============================================================
# SECTION 10 — LangCache
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 10 — LangCache: Semantic Caching\n",
    "\n",
    "### The Problem: Repeated LLM Calls\n",
    "\n",
    "Imagine a food delivery app where thousands of customers open the support "
    "chat every morning. Many of them type something like:\n",
    "\n",
    "- `good morning`\n",
    "- `Good morning!`\n",
    "- `hey, good morning`\n",
    "- `morning`\n",
    "\n",
    "These are semantically identical — but without caching, each one triggers a "
    "full round-trip: embed → route → search Redis → call OpenAI. "
    "A Redis customer reported **meaningful cost savings** after caching just this "
    "type of repeated low-value input.\n",
    "\n",
    "### What Is LangCache?\n",
    "\n",
    "**Redis LangCache** is a fully-managed semantic caching service built on Redis Cloud. "
    "Instead of rolling your own vector cache (which takes code, tuning, and maintenance), "
    "LangCache gives you a simple API:\n",
    "\n",
    "```\n",
    "1. Search the cache: is there a similar prompt already answered?\n",
    "2a. Cache HIT  → return the cached response instantly (no LLM call)\n",
    "2b. Cache MISS → call the LLM, then store the response in the cache\n",
    "```\n",
    "\n",
    "The similarity check is semantic, not exact — so `\"good morning\"` and "
    "`\"Good morning!\"` both hit the same cache entry.\n",
    "\n",
    "> **Note:** LangCache is currently in **preview** on Redis Cloud. "
    "Features and endpoints may evolve. See the "
    "[LangCache docs](https://redis.io/docs/latest/develop/ai/langcache/) for the latest.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# LangCache credentials\n",
    "#\n",
    "# You need a LangCache instance provisioned on Redis Cloud.\n",
    "# Find your URL, Cache ID, and API key in the Redis Cloud console.\n",
    "#\n",
    "# If you do not have a LangCache instance yet, you can still follow along —\n",
    "# the cell below will skip gracefully if credentials are not provided.\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "LANGCACHE_URL      = input(\"LangCache URL (https://...): \").strip()\n",
    "LANGCACHE_CACHE_ID = input(\"LangCache Cache ID: \").strip()\n",
    "LANGCACHE_API_KEY  = getpass.getpass(\"LangCache API Key: \")\n",
    "\n",
    "LANGCACHE_AVAILABLE = bool(LANGCACHE_URL and LANGCACHE_CACHE_ID and LANGCACHE_API_KEY)\n",
    "\n",
    "if LANGCACHE_AVAILABLE:\n",
    "    print(\"✅ LangCache credentials collected\")\n",
    "else:\n",
    "    print(\"⚠️  LangCache credentials not provided — skipping live demo.\")\n",
    "    print(\"   You can still follow the code and understand how LangCache works.\")",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Initialise LangCache client\n",
    "# ---------------------------------------------------------------------------\n",
    "lang_cache = None\n",
    "\n",
    "if LANGCACHE_AVAILABLE:\n",
    "    try:\n",
    "        from langcache import LangCache\n",
    "        lang_cache = LangCache(\n",
    "            server_url=LANGCACHE_URL,\n",
    "            cache_id=LANGCACHE_CACHE_ID,\n",
    "            api_key=LANGCACHE_API_KEY,\n",
    "        )\n",
    "        print(\"✅ LangCache client initialised\")\n",
    "    except Exception as e:\n",
    "        print(f\"❌ LangCache init failed: {e}\")\n",
    "        LANGCACHE_AVAILABLE = False",
))

new_cells.append(md(
    "### 10.1 — Cache Miss and Cache Hit\n",
    "\n",
    "We'll use the `\"good morning\"` family of inputs to demonstrate semantic caching.\n",
    "\n",
    "**First call:** cache miss — LangCache has no entry yet, so we call the LLM and store the response.  \n",
    "**Subsequent calls:** cache hit — semantically similar prompts return the cached answer instantly.\n",
    "\n",
    "The similarity threshold controls how similar two prompts must be to share a cache entry. "
    "We start at `0.9` (very similar) — a good default for production semantic caching.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Helper: call LLM for a simple greeting response\n",
    "# (This is a standalone demo — not part of the RAG pipeline)\n",
    "# ---------------------------------------------------------------------------\n",
    "def call_llm_for_greeting(prompt: str) -> str:\n",
    "    \"\"\"\n",
    "    Generate a short greeting response from the LLM.\n",
    "    Used only for the LangCache demonstration.\n",
    "\n",
    "    Args:\n",
    "        prompt: The user's greeting text.\n",
    "\n",
    "    Returns:\n",
    "        A friendly response string.\n",
    "    \"\"\"\n",
    "    response = openai_client.chat.completions.create(\n",
    "        model=CHAT_MODEL,\n",
    "        messages=[\n",
    "            {\"role\": \"system\", \"content\": \"You are a friendly food delivery support assistant. \"\n",
    "                                           \"Reply to greetings warmly and briefly.\"},\n",
    "            {\"role\": \"user\",   \"content\": prompt},\n",
    "        ],\n",
    "        temperature=0.7,\n",
    "        max_tokens=60,\n",
    "    )\n",
    "    return response.choices[0].message.content\n",
    "\n",
    "\n",
    "# ---------------------------------------------------------------------------\n",
    "# LangCache wrapper: search → hit or miss → store\n",
    "# ---------------------------------------------------------------------------\n",
    "def ask_with_cache(prompt: str, similarity_threshold: float = 0.9) -> str:\n",
    "    \"\"\"\n",
    "    Answer a prompt using LangCache semantic caching.\n",
    "\n",
    "    Flow:\n",
    "      1. Search LangCache for a semantically similar cached response\n",
    "      2a. Cache HIT  → return cached response (no LLM call)\n",
    "      2b. Cache MISS → call LLM, store response in cache, return response\n",
    "\n",
    "    Args:\n",
    "        prompt:               The user's input.\n",
    "        similarity_threshold: How similar two prompts must be to share a cache entry.\n",
    "                              0.9 = very similar (recommended); 0.8 = looser matching.\n",
    "\n",
    "    Returns:\n",
    "        The response string (from cache or freshly generated).\n",
    "    \"\"\"\n",
    "    if not LANGCACHE_AVAILABLE or lang_cache is None:\n",
    "        print(f\"[LangCache unavailable — calling LLM directly]\")\n",
    "        return call_llm_for_greeting(prompt)\n",
    "\n",
    "    # Step 1: Search the cache\n",
    "    cached = lang_cache.search(\n",
    "        prompt=prompt,\n",
    "        similarity_threshold=similarity_threshold,\n",
    "    )\n",
    "\n",
    "    if cached:\n",
    "        # Cache HIT — return immediately without calling the LLM\n",
    "        response = cached[0][\"response\"]\n",
    "        print(f\"  📦 CACHE HIT  | '{prompt}'\")\n",
    "        print(f\"     Response   : {response}\")\n",
    "        return response\n",
    "\n",
    "    # Cache MISS — call the LLM and store the result\n",
    "    print(f\"  🔄 CACHE MISS | '{prompt}' — calling LLM...\")\n",
    "    response = call_llm_for_greeting(prompt)\n",
    "\n",
    "    # Store in LangCache for future semantically-similar queries\n",
    "    lang_cache.set(prompt=prompt, response=response)\n",
    "\n",
    "    print(f\"     Response   : {response}\")\n",
    "    print(f\"     Stored in cache ✅\")\n",
    "    return response\n",
    "\n",
    "\n",
    "print(\"✅ LangCache helper functions defined\")",
))

new_cells.append(md(
    "### 10.2 — Demonstration: 'Good Morning' Variants\n",
    "\n",
    "Watch what happens as we send the same semantic intent with different wording. "
    "The first call will be a cache miss (LLM call). "
    "Subsequent similar inputs should be cache hits.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Good morning demo — run each variant and observe cache behaviour\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "import time\n",
    "\n",
    "greeting_variants = [\n",
    "    \"good morning\",\n",
    "    \"Good morning!\",\n",
    "    \"hey, good morning\",\n",
    "    \"morning\",\n",
    "]\n",
    "\n",
    "CACHE_THRESHOLD = 0.85   # Tune this to see more or fewer cache hits\n",
    "\n",
    "print(f\"Similarity threshold: {CACHE_THRESHOLD}\")\n",
    "print(\"=\" * 55)\n",
    "\n",
    "for variant in greeting_variants:\n",
    "    start = time.time()\n",
    "    ask_with_cache(variant, similarity_threshold=CACHE_THRESHOLD)\n",
    "    elapsed = time.time() - start\n",
    "    print(f\"     Latency    : {elapsed:.2f}s\")\n",
    "    print()",
))

new_cells.append(md(
    "### 10.3 — Why LangCache vs Roll Your Own?\n",
    "\n",
    "You *could* build semantic caching yourself using Redis vector search directly. "
    "But LangCache gives you:\n",
    "\n",
    "| Feature | Roll Your Own | LangCache |\n",
    "|---|---|---|\n",
    "| Setup | Schema + index + code | One SDK call |\n",
    "| Embedding | You manage the model | Managed by Redis Cloud |\n",
    "| TTL / expiry | You implement | Configurable in the console |\n",
    "| Monitoring | You build | Built-in cache hit metrics |\n",
    "| Updates | You maintain | Managed service |\n",
    "\n",
    "For customer-facing AI applications, LangCache is the recommended path "
    "— less code to maintain, fewer edge cases to handle, and it stays in Redis Cloud "
    "alongside your vector index and router.\n",
))

# ============================================================
# SECTION 11 — Final Chatbot Test
# ============================================================

new_cells.append(md(
    "---\n",
    "## Section 11 — Final Chatbot Test\n",
    "\n",
    "Time to bring it all together. The full pipeline is:\n",
    "\n",
    "```\n",
    "User question\n",
    "  → SemanticRouter (RedisVL)        ← refuse if out-of-domain\n",
    "  → LangCache search                ← return cached answer if hit\n",
    "  → Vector search (Redis Cloud)     ← retrieve relevant policy chunks\n",
    "  → OpenAI chat model               ← generate grounded answer\n",
    "  → Answer + Citations              ← with source document references\n",
    "  → LangCache store                 ← cache the response for next time\n",
    "```\n",
    "\n",
    "This is the **Don't Talk With Food In Your Mouth** Redis Eats support bot.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Full chatbot function — routing + caching + RAG\n",
    "#\n",
    "# This is the production-shaped version that combines all three layers:\n",
    "#   1. SemanticRouter  — guard against out-of-domain questions\n",
    "#   2. LangCache       — return cached answers for repeated questions\n",
    "#   3. RAG pipeline    — retrieve from Redis + generate via OpenAI\n",
    "# ---------------------------------------------------------------------------\n",
    "\n",
    "def ask_bot(\n",
    "    question: str,\n",
    "    top_k: int = 5,\n",
    "    cache_threshold: float = 0.9,\n",
    "    verbose: bool = True,\n",
    ") -> Dict[str, Any]:\n",
    "    \"\"\"\n",
    "    Don't Talk With Food In Your Mouth — Redis Eats Support Bot.\n",
    "\n",
    "    Full pipeline:\n",
    "      1. Route    : reject out-of-domain questions immediately\n",
    "      2. Cache    : return cached responses for similar recent questions\n",
    "      3. Retrieve : find relevant policy chunks via Redis vector search\n",
    "      4. Generate : produce a grounded answer via OpenAI\n",
    "      5. Store    : cache the new response in LangCache\n",
    "\n",
    "    Args:\n",
    "        question:        The user's question.\n",
    "        top_k:           Number of chunks to retrieve.\n",
    "        cache_threshold: Semantic similarity threshold for cache lookup.\n",
    "        verbose:         Print results to the console.\n",
    "\n",
    "    Returns:\n",
    "        Dict with 'answer', 'citations', 'route', and 'cache_hit' keys.\n",
    "    \"\"\"\n",
    "    if verbose:\n",
    "        print(f\"\\n🤖 Don't Talk With Food In Your Mouth\")\n",
    "        print(f\"   Q: {question}\")\n",
    "        print()\n",
    "\n",
    "    # -----------------------------------------------------------------------\n",
    "    # Step 1: Semantic routing\n",
    "    # -----------------------------------------------------------------------\n",
    "    route_match = router(question)\n",
    "    route_name  = route_match.name if route_match else None\n",
    "\n",
    "    if route_name is None:\n",
    "        # Out-of-domain — refuse without touching Redis search or OpenAI\n",
    "        if verbose:\n",
    "            print(f\"   [router] out-of-domain → refused\")\n",
    "            print(f\"\\n   A: {REFUSAL_MESSAGE}\")\n",
    "        return {\n",
    "            \"answer\":    REFUSAL_MESSAGE,\n",
    "            \"citations\": [],\n",
    "            \"route\":     None,\n",
    "            \"cache_hit\": False,\n",
    "        }\n",
    "\n",
    "    if verbose:\n",
    "        print(f\"   [router] route → {route_name}\")\n",
    "\n",
    "    # -----------------------------------------------------------------------\n",
    "    # Step 2: LangCache lookup\n",
    "    # -----------------------------------------------------------------------\n",
    "    if LANGCACHE_AVAILABLE and lang_cache is not None:\n",
    "        cached = lang_cache.search(\n",
    "            prompt=question,\n",
    "            similarity_threshold=cache_threshold,\n",
    "        )\n",
    "        if cached:\n",
    "            cached_answer = cached[0][\"response\"]\n",
    "            if verbose:\n",
    "                print(f\"   [cache]  HIT — returning cached response\")\n",
    "                print(f\"\\n   A: {cached_answer}\")\n",
    "                print(f\"\\n   Sources: (from cache)\")\n",
    "            return {\n",
    "                \"answer\":    cached_answer,\n",
    "                \"citations\": [],\n",
    "                \"route\":     route_name,\n",
    "                \"cache_hit\": True,\n",
    "            }\n",
    "        if verbose:\n",
    "            print(f\"   [cache]  MISS — proceeding to retrieval\")\n",
    "\n",
    "    # -----------------------------------------------------------------------\n",
    "    # Step 3: RAG pipeline\n",
    "    # -----------------------------------------------------------------------\n",
    "    rag_result = ask_rag(question, top_k=top_k, verbose=verbose)\n",
    "\n",
    "    # -----------------------------------------------------------------------\n",
    "    # Step 4: Store in LangCache for next time\n",
    "    # -----------------------------------------------------------------------\n",
    "    if LANGCACHE_AVAILABLE and lang_cache is not None:\n",
    "        lang_cache.set(prompt=question, response=rag_result[\"answer\"])\n",
    "        if verbose:\n",
    "            print(f\"   [cache]  response stored for future similar questions\")\n",
    "\n",
    "    rag_result[\"route\"]     = route_name\n",
    "    rag_result[\"cache_hit\"] = False\n",
    "    return rag_result\n",
    "\n",
    "\n",
    "print(\"✅ ask_bot() is ready\")",
))

new_cells.append(md(
    "### 11.1 — Successful RAG Questions\n",
    "\n",
    "These should all be routed correctly, miss the cache (first run), "
    "retrieve from Redis, and return a grounded answer with citations.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Run all workshop success-path example questions\n",
    "# ---------------------------------------------------------------------------\n",
    "success_questions = [\n",
    "    \"Can I get a refund if my food arrived cold?\",\n",
    "    \"What happens if my delivery is late?\",\n",
    "    \"How do promo codes work?\",\n",
    "    \"What should a restaurant do if they need to pause orders?\",\n",
    "    \"How do I reset my account password?\",\n",
    "]\n",
    "\n",
    "for q in success_questions:\n",
    "    ask_bot(q)\n",
    "    print(\"-\" * 60)",
))

new_cells.append(md(
    "### 11.2 — Out-of-Domain Refusals\n",
    "\n",
    "These should all be intercepted by the router and refused "
    "without any Redis search or LLM call.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Run all workshop out-of-domain examples\n",
    "# ---------------------------------------------------------------------------\n",
    "blocked = [\n",
    "    \"Who won the Super Bowl?\",\n",
    "    \"What is the weather in Chicago?\",\n",
    "    \"Write me a poem about databases.\",\n",
    "    \"How do I invest in stocks?\",\n",
    "    \"What is the capital of France?\",\n",
    "]\n",
    "\n",
    "for q in blocked:\n",
    "    ask_bot(q)\n",
    "    print(\"-\" * 60)",
))

new_cells.append(md(
    "### 11.3 — LangCache Demonstration\n",
    "\n",
    "Run this cell twice (or run the cell, then change the wording slightly and run again). "
    "The second pass should show cache hits for semantically similar inputs.\n",
))

new_cells.append(code(
    "# ---------------------------------------------------------------------------\n",
    "# Ask the same question twice — observe cache miss then cache hit\n",
    "# ---------------------------------------------------------------------------\n",
    "repeat_question = \"Can I get a refund if my food arrived cold?\"\n",
    "\n",
    "print(\"First call (expect MISS):\")\n",
    "ask_bot(repeat_question)\n",
    "\n",
    "print(\"\\nSecond call — semantically similar phrasing (expect HIT):\")\n",
    "ask_bot(\"My food was cold when it arrived. Am I entitled to a refund?\")",
))

# ---------------------------------------------------------------------------
# Load existing notebook and append new cells
# ---------------------------------------------------------------------------
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
nb["cells"].extend(new_cells)
NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")

print(f"✅ Sections 9–11 appended → {NOTEBOOK}")
print(f"   Total cells: {len(nb['cells'])}")
