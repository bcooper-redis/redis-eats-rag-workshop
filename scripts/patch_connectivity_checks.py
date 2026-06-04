"""
patch_connectivity_checks.py

Replaces the thin Redis and OpenAI connectivity test cells in the notebook
with comprehensive diagnostic versions that check:

Redis:
  1. Basic TCP + TLS connectivity (r.ping())
  2. Redis server version
  3. Redis Search module is loaded (required for FT.CREATE / vector search)
  4. REDIS_URL is usable by RedisVL
  5. Specific error diagnosis: auth vs TLS vs network

OpenAI:
  1. API key authentication
  2. Embedding model availability + actual test call (catches quota issues)
  3. Chat model availability + actual test call (catches quota issues)
  4. Dimension sanity check on the test embedding

Run:
    python3 scripts/patch_connectivity_checks.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NOTEBOOK  = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"

# ---------------------------------------------------------------------------
# Replacement cell source strings
# ---------------------------------------------------------------------------

REDIS_CHECK = """\
# ---------------------------------------------------------------------------
# Section 1.2 — Redis Cloud Connectivity Check
#
# This cell runs four checks and must pass before you continue:
#   1. TCP + TLS connection to Redis Cloud
#   2. Redis server version (must be 7.x+ for Redis Query Engine)
#   3. Redis Search module loaded (required for FT.CREATE and vector search)
#   4. RedisVL can use the REDIS_URL (used for SearchIndex throughout the notebook)
# ---------------------------------------------------------------------------

import sys

_redis_ok = True   # Set to False on any failure so later cells can gate on this

# --- Check 1: TCP + TLS connection ---
print("Checking Redis Cloud connectivity...\\n")

try:
    r = redis_lib.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        ssl=True,                  # Redis Cloud always requires TLS
        decode_responses=True,
        socket_connect_timeout=10,
        socket_timeout=10,
    )
    r.ping()
    print("  ✅ TCP + TLS connection  OK")
except redis_lib.exceptions.AuthenticationError:
    print("  ❌ Authentication failed")
    print("     → Check your Redis username and password in the credentials cell above")
    _redis_ok = False
except redis_lib.exceptions.ConnectionError as e:
    err = str(e).lower()
    if "ssl" in err or "tls" in err or "certificate" in err:
        print(f"  ❌ TLS/SSL error: {e}")
        print("     → Make sure ssl=True is set. Redis Cloud requires rediss:// (TLS)")
    elif "timed out" in err or "timeout" in err:
        print(f"  ❌ Connection timed out")
        print("     → Check the host and port. Is the database in Active state?")
    else:
        print(f"  ❌ Connection error: {e}")
        print("     → Verify REDIS_HOST and REDIS_PORT are correct")
    _redis_ok = False
except Exception as e:
    print(f"  ❌ Unexpected error: {e}")
    _redis_ok = False

# --- Check 2: Redis server version ---
if _redis_ok:
    try:
        info = r.info("server")
        version = info.get("redis_version", "unknown")
        major   = int(version.split(".")[0]) if version != "unknown" else 0
        if major >= 7:
            print(f"  ✅ Redis version         {version}  (Redis Query Engine supported)")
        else:
            print(f"  ⚠️  Redis version         {version}  (recommend 7.x+ for this workshop)")
    except Exception as e:
        print(f"  ⚠️  Could not read server version: {e}")

# --- Check 3: Redis Search module ---
if _redis_ok:
    try:
        modules = r.execute_command("MODULE LIST")
        module_names = []
        for m in modules:
            # MODULE LIST returns a list of lists: [[b'name', b'search', ...], ...]
            if isinstance(m, list):
                for i, item in enumerate(m):
                    if item in (b"name", "name") and i + 1 < len(m):
                        module_names.append(str(m[i + 1]).lower())
        search_loaded = any("search" in n for n in module_names)
        if search_loaded:
            print(f"  ✅ Redis Search module   loaded  (FT.CREATE and vector search ready)")
        else:
            # Fallback: try FT._LIST directly — some Redis builds expose search without MODULE LIST
            try:
                r.execute_command("FT._LIST")
                print(f"  ✅ Redis Search module   available  (FT._LIST succeeded)")
            except Exception:
                print(f"  ❌ Redis Search module   NOT found")
                print(f"     → This workshop requires Redis Stack or Redis Cloud with Search enabled")
                print(f"     → Upgrade your Redis Cloud database to a plan that includes Search")
                _redis_ok = False
    except Exception:
        # Some managed Redis endpoints block MODULE LIST — try FT._LIST as fallback
        try:
            r.execute_command("FT._LIST")
            print(f"  ✅ Redis Search module   available  (FT._LIST succeeded)")
        except Exception as e2:
            print(f"  ❌ Redis Search module check failed: {e2}")
            print(f"     → Redis Cloud free tier includes Search. Re-check your database plan.")
            _redis_ok = False

# --- Check 4: RedisVL can use REDIS_URL ---
if _redis_ok:
    try:
        from redisvl.redis.connection import RedisConnectionFactory
        test_client = RedisConnectionFactory.get_redis_connection(url=REDIS_URL)
        test_client.ping()
        print(f"  ✅ RedisVL connection     OK  (REDIS_URL is valid for SearchIndex)")
    except Exception as e:
        print(f"  ❌ RedisVL connection failed: {e}")
        print(f"     → REDIS_URL = {REDIS_URL[:40]}...")
        print(f"     → Check that host, port, username, and password are all correct")
        _redis_ok = False

# --- Summary ---
print()
if _redis_ok:
    print("✅ All Redis checks passed — ready to continue")
    print(f"   Host    : {REDIS_HOST}:{REDIS_PORT}")
    print(f"   User    : {REDIS_USERNAME}")
else:
    print("❌ Redis setup has issues — fix the errors above before continuing")
    print("   Do NOT run the rest of the notebook until all checks pass.")
"""

OPENAI_CHECK = """\
# ---------------------------------------------------------------------------
# Section 1.3 — OpenAI Connectivity Check
#
# This cell runs three checks and must pass before you continue:
#   1. API key is valid (authentication)
#   2. Embedding model works + returns correct dimensions (catches quota issues)
#   3. Chat model responds (catches quota issues on the chat endpoint)
#
# A key that passes auth but has $0 credits will fail checks 2 and 3 —
# catching that early avoids a surprise failure during the batch embed step.
# ---------------------------------------------------------------------------

_openai_ok = True   # Gate flag used by later cells

print("Checking OpenAI connectivity...\\n")

# --- Check 1: Create client + authenticate ---
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    # A lightweight authenticated call — doesn't consume credits
    openai_client.models.list()
    print("  ✅ API key               valid")
except openai.AuthenticationError:
    print("  ❌ API key invalid")
    print("     → Check your key starts with sk- and hasn't been revoked")
    _openai_ok = False
except openai.PermissionDeniedError:
    print("  ❌ API key does not have permission")
    print("     → Make sure this is a paid OpenAI account key")
    _openai_ok = False
except Exception as e:
    print(f"  ❌ OpenAI connection error: {e}")
    _openai_ok = False

# --- Check 2: Embedding model ---
if _openai_ok:
    try:
        test_resp = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input="connectivity test",
        )
        dims = len(test_resp.data[0].embedding)
        if dims == 1536:
            print(f"  ✅ Embedding model       text-embedding-3-small  ({dims} dims)")
        else:
            print(f"  ⚠️  Embedding model       returned {dims} dims (expected 1536)")
            print(f"     → The RedisVL schema is set to 1536 dims. Check the model name.")
    except openai.RateLimitError:
        print("  ❌ Embedding model       rate limit hit or insufficient credits")
        print("     → Check your OpenAI account billing at platform.openai.com")
        _openai_ok = False
    except openai.NotFoundError:
        print("  ❌ Embedding model       text-embedding-3-small not accessible")
        print("     → Verify your account has access to this model")
        _openai_ok = False
    except Exception as e:
        print(f"  ❌ Embedding model error: {e}")
        _openai_ok = False

# --- Check 3: Chat model ---
if _openai_ok:
    try:
        chat_resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Reply with the single word: ready"}],
            max_tokens=5,
            temperature=0,
        )
        reply = chat_resp.choices[0].message.content.strip().lower()
        print(f"  ✅ Chat model            gpt-4o-mini  (test response: '{reply}')")
    except openai.RateLimitError:
        print("  ❌ Chat model            rate limit hit or insufficient credits")
        print("     → Check your OpenAI account billing at platform.openai.com")
        _openai_ok = False
    except openai.NotFoundError:
        print("  ❌ Chat model            gpt-4o-mini not accessible")
        print("     → Verify your account has access to this model")
        _openai_ok = False
    except Exception as e:
        print(f"  ❌ Chat model error: {e}")
        _openai_ok = False

# --- Summary ---
print()
if _openai_ok:
    print("✅ All OpenAI checks passed — ready to continue")
else:
    print("❌ OpenAI setup has issues — fix the errors above before continuing")
    print("   Common fixes:")
    print("   • Ensure your OpenAI account has a credit card and available balance")
    print("   • Check usage limits at: https://platform.openai.com/usage")
    print("   • Make sure the key was not copy/pasted with extra whitespace")
"""

# ---------------------------------------------------------------------------
# Patch the notebook
# ---------------------------------------------------------------------------

def find_cell_index(cells, marker_text):
    """Return the index of the first code cell whose source contains marker_text."""
    for i, cell in enumerate(cells):
        if cell["cell_type"] == "code" and marker_text in "".join(cell["source"]):
            return i
    return None


nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
cells = nb["cells"]

# --- Patch Redis check ---
idx_redis = find_cell_index(cells, "r.ping()")
if idx_redis is None:
    print("❌ Could not find Redis connectivity cell (looked for r.ping())")
else:
    cells[idx_redis]["source"] = [REDIS_CHECK]
    print(f"✅ Redis connectivity cell replaced (cell {idx_redis})")

# --- Patch OpenAI check ---
idx_openai = find_cell_index(cells, "models.list()")
if idx_openai is None:
    print("❌ Could not find OpenAI test cell (looked for models.list())")
else:
    cells[idx_openai]["source"] = [OPENAI_CHECK]
    print(f"✅ OpenAI connectivity cell replaced (cell {idx_openai})")

# --- Write back ---
NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\n✅ Notebook saved → {NOTEBOOK}")
print(f"   Total cells: {len(cells)}")
