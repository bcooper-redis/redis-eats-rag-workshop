"""
update_repo_url.py

Updates all occurrences of the placeholder GitHub username ('your-org')
in the notebook and README with the real GitHub username/org.

Run this BEFORE your first git push so the Colab setup cell and badge
point to your actual repository.

Usage:
    python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-rag-workshop

Example:
    python3 scripts/update_repo_url.py https://github.com/redis/redis-eats-rag-workshop
"""

import sys
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT   = Path(__file__).parent.parent
NOTEBOOK    = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"
README      = REPO_ROOT / "README.md"
PLACEHOLDER = "your-org"   # The string to replace throughout the repo


def main():
    """Parse the new GitHub URL and apply it to all relevant files."""

    # -----------------------------------------------------------------------
    # Parse arguments
    # -----------------------------------------------------------------------
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-rag-workshop")
        sys.exit(1)

    new_url = sys.argv[1].rstrip("/")

    # Validate it looks like a GitHub URL
    parts = new_url.split("/")
    if len(parts) < 5 or "github.com" not in new_url:
        print(f"ERROR: Expected a GitHub URL like https://github.com/username/repo")
        print(f"       Got: {new_url}")
        sys.exit(1)

    # Extract the username/org from the URL
    # https://github.com/USERNAME/repo → parts[3] = USERNAME
    new_username = parts[3]

    print(f"Updating repository references:")
    print(f"  Old username : {PLACEHOLDER}")
    print(f"  New username : {new_username}")
    print()

    # -----------------------------------------------------------------------
    # Update the notebook
    # -----------------------------------------------------------------------
    if not NOTEBOOK.exists():
        print(f"❌ Notebook not found at {NOTEBOOK}")
        sys.exit(1)

    nb_text = NOTEBOOK.read_text(encoding="utf-8")
    count_nb = nb_text.count(PLACEHOLDER)
    nb_text_updated = nb_text.replace(PLACEHOLDER, new_username)
    NOTEBOOK.write_text(nb_text_updated, encoding="utf-8")
    print(f"✅ Notebook updated  ({count_nb} replacement(s))")

    # -----------------------------------------------------------------------
    # Update the README
    # -----------------------------------------------------------------------
    if README.exists():
        readme_text = README.read_text(encoding="utf-8")
        count_readme = readme_text.count(PLACEHOLDER)
        readme_updated = readme_text.replace(PLACEHOLDER, new_username)
        README.write_text(readme_updated, encoding="utf-8")
        print(f"✅ README updated    ({count_readme} replacement(s))")
    else:
        print(f"⚠️  README not found — skipping")

    # -----------------------------------------------------------------------
    # Print the live Colab link
    # -----------------------------------------------------------------------
    colab_link = (
        f"https://colab.research.google.com/github/{new_username}/"
        f"redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb"
    )

    print()
    print("─" * 60)
    print("Your Colab link:")
    print(f"  {colab_link}")
    print()
    print("Your GitHub repo:")
    print(f"  https://github.com/{new_username}/redis-eats-rag-workshop")
    print("─" * 60)
    print()
    print("Next steps:")
    print("  1. git add .")
    print("  2. git commit -m 'Update repo URL for deployment'")
    print("  3. git push")
    print("  4. Open the Colab link above and test it")


if __name__ == "__main__":
    main()
