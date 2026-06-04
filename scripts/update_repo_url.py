"""
update_repo_url.py

Updates the GitHub username/org in the notebook and README so Colab's git
clone and all badge links point to your actual repository.

Safe to run multiple times. Detects whatever username is currently in the
files and replaces it — works whether the files contain the original
placeholder ('your-org'), a test value, or a previously set username.

Usage:
    python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-rag-workshop

Example:
    python3 scripts/update_repo_url.py https://github.com/redis/redis-eats-rag-workshop
"""

import re
import sys
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
NOTEBOOK  = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"
README    = REPO_ROOT / "README.md"

# The fixed repo name — only the username/org changes
REPO_NAME = "redis-eats-rag-workshop"

# Pattern that matches any GitHub URL for this repo
# Captures the current username so we know what to replace
GITHUB_PATTERN = re.compile(
    rf'(github\.com/)([^/"\'`\\\s\)]+)(/{re.escape(REPO_NAME)})',
    re.IGNORECASE,
)


def find_current_username(text: str) -> str | None:
    """
    Scan text for github.com/<username>/redis-eats-rag-workshop and return
    the username currently in the file, or None if no match is found.
    """
    match = GITHUB_PATTERN.search(text)
    return match.group(2) if match else None


def replace_username(text: str, new_username: str) -> tuple[str, int]:
    """
    Replace every github.com/<any-username>/redis-eats-rag-workshop
    with github.com/<new_username>/redis-eats-rag-workshop.

    Returns (updated_text, number_of_replacements).
    """
    count = [0]

    def replacer(m):
        count[0] += 1
        return f"{m.group(1)}{new_username}{m.group(3)}"

    updated = GITHUB_PATTERN.sub(replacer, text)
    return updated, count[0]


def main():
    # -----------------------------------------------------------------------
    # Parse and validate the new GitHub URL
    # -----------------------------------------------------------------------
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/{REPO_NAME}")
        sys.exit(1)

    new_url = sys.argv[1].rstrip("/")
    parts   = new_url.split("/")

    if "github.com" not in new_url or len(parts) < 5:
        print(f"ERROR: Expected https://github.com/username/{REPO_NAME}")
        print(f"       Got: {new_url}")
        sys.exit(1)

    new_username = parts[3]

    # -----------------------------------------------------------------------
    # Update the notebook
    # -----------------------------------------------------------------------
    if not NOTEBOOK.exists():
        print(f"ERROR: Notebook not found at {NOTEBOOK}")
        sys.exit(1)

    nb_text          = NOTEBOOK.read_text(encoding="utf-8")
    current_nb_user  = find_current_username(nb_text)
    nb_updated, n_nb = replace_username(nb_text, new_username)

    if n_nb > 0:
        NOTEBOOK.write_text(nb_updated, encoding="utf-8")
        print(f"✅ Notebook  {current_nb_user or '?'!r:>15}  →  {new_username!r}  ({n_nb} replacement(s))")
    else:
        print(f"✅ Notebook  already set to {new_username!r} — no changes needed")

    # -----------------------------------------------------------------------
    # Update the README
    # -----------------------------------------------------------------------
    if README.exists():
        readme_text          = README.read_text(encoding="utf-8")
        current_readme_user  = find_current_username(readme_text)
        readme_updated, n_rm = replace_username(readme_text, new_username)

        if n_rm > 0:
            README.write_text(readme_updated, encoding="utf-8")
            print(f"✅ README    {current_readme_user or '?'!r:>15}  →  {new_username!r}  ({n_rm} replacement(s))")
        else:
            print(f"✅ README    already set to {new_username!r} — no changes needed")
    else:
        print("⚠️  README not found — skipping")

    # -----------------------------------------------------------------------
    # Print results
    # -----------------------------------------------------------------------
    colab_link = (
        f"https://colab.research.google.com/github/{new_username}/"
        f"{REPO_NAME}/blob/main/notebooks/redis_eats_rag_workshop.ipynb"
    )

    print()
    print("─" * 62)
    print("Colab link:")
    print(f"  {colab_link}")
    print()
    print("GitHub repo:")
    print(f"  https://github.com/{new_username}/{REPO_NAME}")
    print("─" * 62)
    print()
    print("Next steps:")
    print("  1. git add .")
    print("  2. git commit -m 'Set GitHub username for deployment'")
    print("  3. git push")
    print("  4. Open the Colab link above and test it")


if __name__ == "__main__":
    main()
