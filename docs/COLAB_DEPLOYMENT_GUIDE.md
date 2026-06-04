# Deploying the Redis Eats RAG Workshop to Google Colab

**Who this guide is for:** Someone who has never published a Jupyter notebook to GitHub or Colab before. Every step is explained from scratch.

**What you will end up with:**
- A GitHub repository anyone can browse
- A single Colab link you can share with workshop attendees
- Attendees click the link, the notebook opens in Colab, and they run it — no installs needed on their machine

**Time to complete:** About 30 minutes.

---

## How It Works (Big Picture)

Google Colab can open any Jupyter notebook that lives in a public GitHub repository. The flow is:

```
Your laptop
  → git push → GitHub repository (public)
                    ↑
                    Google Colab reads the notebook directly from GitHub
                    and runs it in a cloud environment
```

Attendees never need to clone the repo or install Python. They just click a link.

---

## What You Need Before You Start

- A **GitHub account** — free at [github.com](https://github.com)
- **Git** installed on your laptop
  - Mac: open Terminal and run `git --version`. If not installed, macOS will prompt you to install it.
  - Windows: download from [git-scm.com](https://git-scm.com/download/win)
- The workshop repo on your laptop at:
  `/Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-rag-workshop`

---

## Step 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in.
2. Click the **+** button in the top-right corner and choose **New repository**.
3. Fill in the form:

   | Field | Value |
   |---|---|
   | Repository name | `redis-eats-rag-workshop` |
   | Description | Redis Eats RAG Workshop — Workshop 1 |
   | Visibility | **Public** ← Colab requires this |
   | Initialize this repository | **Leave all checkboxes unchecked** |

4. Click **Create repository**.

5. GitHub will show you a page with setup instructions. **Copy the repository URL** — it will look like:
   ```
   https://github.com/YOUR-USERNAME/redis-eats-rag-workshop.git
   ```
   Keep this tab open. You will need this URL in Step 3.

> **Why public?** Google Colab can only open notebooks from public repositories without extra authentication. If your organisation requires a private repo, see the "Private Repo Alternative" section at the bottom of this guide.

---

## Step 2 — Update the Notebook With Your GitHub URL

The notebook has a setup cell that clones the repo when running in Colab. You need to update it with your actual GitHub URL before pushing.

1. Open Terminal and navigate to the workshop folder:
   ```bash
   cd /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-rag-workshop
   ```

2. Run this command, replacing `YOUR-USERNAME` with your actual GitHub username:
   ```bash
   python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-rag-workshop
   ```

   > **What this does:** Updates the `git clone` URL inside the notebook and the Colab badge in the README so they point to your repository.

   > If you prefer to do this manually, open `notebooks/redis_eats_rag_workshop.ipynb` in a text editor, search for `your-org`, and replace every occurrence with your GitHub username.

---

## Step 3 — Push the Workshop to GitHub

Open Terminal. Run these commands one by one. Each command is explained below.

```bash
# 1. Navigate to the workshop folder
cd /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-rag-workshop

# 2. Tell Git this folder is a Git repository
git init

# 3. Tell Git to track all files
git add .

# 4. Create the first commit (a saved snapshot)
git commit -m "Initial commit: Redis Eats RAG Workshop"

# 5. Set the main branch name (GitHub default)
git branch -M main

# 6. Connect your local folder to GitHub
#    Replace YOUR-USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR-USERNAME/redis-eats-rag-workshop.git

# 7. Push everything to GitHub
git push -u origin main
```

**When you run step 7**, Git will ask for your GitHub credentials:
- Username: your GitHub username
- Password: this is **not** your GitHub password — it is a **Personal Access Token**

### Creating a Personal Access Token (first time only)

GitHub no longer accepts your account password for `git push`. You need a token:

1. On GitHub, click your profile picture (top-right) → **Settings**
2. Scroll to the bottom of the left sidebar → **Developer settings**
3. Click **Personal access tokens** → **Tokens (classic)**
4. Click **Generate new token (classic)**
5. Give it a name like `workshop-push`
6. Set expiration to **90 days** (or longer)
7. Under **Select scopes**, tick **repo** (the top checkbox)
8. Click **Generate token** at the bottom
9. **Copy the token immediately** — GitHub will never show it again. Paste it somewhere safe (like Notes) for now.

When Git prompts for a password during `git push`, paste this token.

---

## Step 4 — Verify the Push

1. Go back to your GitHub repository page and refresh it.
2. You should see all the workshop files listed: `README.md`, `notebooks/`, `data/`, `docs/`, etc.
3. Click `notebooks/redis_eats_rag_workshop.ipynb` — GitHub will show a rendered preview of the notebook.

If you see the files, the push worked. ✅

---

## Step 5 — Get the Colab Link

Google Colab uses a predictable URL format to open any notebook from GitHub:

```
https://colab.research.google.com/github/YOUR-USERNAME/redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb
```

Replace `YOUR-USERNAME` with your GitHub username and open this URL in your browser to test it.

You should see the notebook open in Colab with a **Connect** button in the top-right corner.

### Quick way to get the link from GitHub

1. On GitHub, navigate to `notebooks/redis_eats_rag_workshop.ipynb`
2. In your browser address bar, the URL will look like:
   ```
   https://github.com/YOUR-USERNAME/redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb
   ```
3. Change `github.com` to `colab.research.google.com/github` — that's your Colab link.

---

## Step 6 — Test the Full Colab Flow

Before sharing with attendees, test the complete experience yourself:

1. **Open the Colab link** in an Incognito/Private browser window (simulates a fresh attendee)
2. Click **Connect** in the top-right to start a runtime
3. Run **cell 1** (the Colab Setup cell) — it should clone the repo and print `Done.`
4. Run **cell 3** (pip install) — takes about 60 seconds
5. Run **cell 4** (imports) — should print `✅ Imports complete`
6. Run **cell 6** (credentials) — enter your Redis Cloud and OpenAI credentials when prompted
7. Run **cell 8** (Redis check) — verify you see `✅ All Redis checks passed` with all 4 sub-checks green
8. Run **cell 10** (OpenAI check) — verify you see `✅ All OpenAI checks passed` with all 3 sub-checks green
9. Stop here — you've confirmed the full setup flow works

> **Why 4 sub-checks for Redis?** The connectivity cell now verifies: TCP+TLS connection, Redis version (7.x+), Redis Search module loaded, and RedisVL URL format — so any setup problem surfaces immediately with a specific fix hint rather than a cryptic error later.

> **Tip:** Keep a working Colab session open as your instructor fallback during the live workshop.

---

## Step 7 — Share With Attendees

You now have two things to share:

### The Colab link
```
https://colab.research.google.com/github/YOUR-USERNAME/redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb
```

Share this in your workshop invite email, Slack channel, or slide deck.

### The GitHub repo (optional)
```
https://github.com/YOUR-USERNAME/redis-eats-rag-workshop
```

Attendees can browse the source files, read the README, and reference it after the workshop.

---

## Step 8 — What Attendees Do

When attendees arrive, their steps are:

1. Click the Colab link you shared
2. Sign in to Google (if not already signed in)
3. Click **Connect** in the top-right corner
4. Run **cell 1** (Colab Setup) — clones the repo to get the PDFs
5. Run the rest of the cells top to bottom

They need no local software. The only things they need to have ready are:
- Redis Cloud credentials (host, port, password)
- OpenAI API key

---

## Updating the Workshop After It Is Live

When you make changes to the notebook on your laptop and want attendees to see the latest version:

```bash
cd /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-rag-workshop

# Stage your changes
git add notebooks/redis_eats_rag_workshop.ipynb

# Or stage everything if you changed multiple files
git add .

# Commit with a description of what changed
git commit -m "Fix Section 7 example query"

# Push to GitHub
git push
```

Colab always fetches the latest version from GitHub when an attendee opens the link, so your changes go live immediately after `git push`.

> **Note:** If an attendee already has the notebook open in Colab, they need to reopen the link to get the updated version.

---

## The `update_repo_url.py` Script

The guide references this script in Step 2. Create it now by running:

```bash
cat > /Users/brian.cooper/Documents/ClaudeApps/handsOnWorkshop/redis-eats-rag-workshop/scripts/update_repo_url.py << 'EOF'
"""
update_repo_url.py

Updates all occurrences of the placeholder GitHub URL in the notebook
and README with the real repository URL.

Usage:
    python3 scripts/update_repo_url.py https://github.com/your-username/redis-eats-rag-workshop
"""
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLACEHOLDER = "your-org"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-rag-workshop")
        sys.exit(1)

    new_url = sys.argv[1].rstrip("/")
    # Extract username from URL: https://github.com/USERNAME/repo
    parts = new_url.split("/")
    if len(parts) < 5 or "github.com" not in parts:
        print(f"ERROR: Expected a GitHub URL like https://github.com/username/repo, got: {new_url}")
        sys.exit(1)
    new_username = parts[3]

    # --- Update notebook ---
    nb_path = REPO_ROOT / "notebooks" / "redis_eats_rag_workshop.ipynb"
    nb_text = nb_path.read_text(encoding="utf-8")
    nb_text_updated = nb_text.replace(f"your-org", new_username)
    nb_path.write_text(nb_text_updated, encoding="utf-8")
    print(f"✅ Notebook updated  → replaced 'your-org' with '{new_username}'")

    # --- Update README ---
    readme_path = REPO_ROOT / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    readme_updated = readme_text.replace("your-org", new_username)
    readme_path.write_text(readme_updated, encoding="utf-8")
    print(f"✅ README updated    → replaced 'your-org' with '{new_username}'")

    print(f"\nColab link:")
    print(f"  https://colab.research.google.com/github/{new_username}/redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb")

if __name__ == "__main__":
    main()
EOF
```

Or you can create the file manually — see the full script content in `scripts/update_repo_url.py` after running the command above.

---

## Checklist Before the Live Workshop

Run through this the day before the session:

- [ ] GitHub repo is public and all files are visible
- [ ] Colab link opens the notebook without errors
- [ ] Cell 1 (Colab Setup) runs and prints `Done.`
- [ ] Cell 3 (pip install) completes without errors
- [ ] Cell 4 (imports) prints `✅ Imports complete`
- [ ] Cell 8 (Redis check) shows `✅ All Redis checks passed` — all 4 sub-checks green
- [ ] Cell 10 (OpenAI check) shows `✅ All OpenAI checks passed` — all 3 sub-checks green
- [ ] Your instructor Redis Cloud credentials are ready and tested
- [ ] Your instructor OpenAI API key has sufficient credits
- [ ] The Colab link is in your slide deck / invite email
- [ ] You have a backup Colab tab open and connected as instructor fallback

---

## Troubleshooting Colab-Specific Issues

### "Repository not found" when cloning in cell 1

The repo URL in the notebook is still the placeholder. Run `scripts/update_repo_url.py` with your GitHub username (Step 2) and push again.

### "File not found: data/pdfs" after cell 1 runs

The clone succeeded but the working directory is wrong. Check that cell 1 includes `os.chdir('/content/redis-eats-rag-workshop')` after the clone. Re-run cell 1.

### Colab disconnects during the embedding step

Colab free tier has an inactivity timeout. If Colab disconnects mid-embedding:
1. Reconnect (click **Reconnect** in the top-right)
2. Re-run cells 3–4 (imports + credentials)
3. Re-run the embedding cell from the top — embeddings are regenerated each session

> **Tip:** Keep your mouse moving or interact with the notebook every few minutes during the embedding step to prevent the idle timeout.

### Attendee sees "You have reached your usage limit" from OpenAI

Their OpenAI account is on the free tier or has run out of credits. They need a paid API key. This must be resolved before the workshop — there is no workaround.

### "Package not found: langcache" during pip install

LangCache is in preview. If the pip package is temporarily unavailable, run:
```python
%pip install redis redisvl openai pypdf tqdm python-dotenv --quiet
```
(Omit `langcache` — Section 10 will degrade gracefully.)

### Slow notebook performance in Colab

Colab free tier uses shared CPU resources. The embedding step may take 2–3 minutes instead of 60 seconds. This is normal. Instruct attendees to let it run.

For faster performance, attendees can upgrade to **Colab Pro** (paid) or run locally.

---

## Private Repo Alternative

If you must use a private GitHub repo:

1. Attendees will need to **authenticate with GitHub** to open the notebook in Colab.
2. When they open the Colab link, Colab will prompt them to connect their GitHub account.
3. Alternatively, distribute the `.ipynb` file directly (email, Slack, Google Drive) and have attendees upload it to Colab manually via **File → Upload notebook**.

For a public workshop, a public repo is strongly recommended — it removes friction and requires no GitHub account on the attendee side.

---

## Quick Reference

| Thing | Where to find it |
|---|---|
| Your Colab link | `https://colab.research.google.com/github/YOUR-USERNAME/redis-eats-rag-workshop/blob/main/notebooks/redis_eats_rag_workshop.ipynb` |
| Your GitHub repo | `https://github.com/YOUR-USERNAME/redis-eats-rag-workshop` |
| Update repo URL | `python3 scripts/update_repo_url.py https://github.com/YOUR-USERNAME/redis-eats-rag-workshop` |
| Push changes | `git add . && git commit -m "message" && git push` |
| Rebuild notebook | `python3 scripts/build_notebook.py && python3 scripts/build_notebook_phase4.py && python3 scripts/build_notebook_phase5.py` |
| Regenerate PDFs | `python3 scripts/generate_policy_pdfs.py` |

---

*That's it. Once `git push` succeeds and the Colab link opens cleanly, the workshop is live.*
