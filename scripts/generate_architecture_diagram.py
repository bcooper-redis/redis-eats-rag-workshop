"""
generate_architecture_diagram.py

Creates the Redis Eats RAG Workshop architecture diagram PNG using matplotlib.

The diagram shows the full RAG request path:
  User Question
    → RedisVL SemanticRouter
      → [Out-of-domain] Refusal response
      → [In-domain] LangCache check
          → [Cache hit] Cached response
          → [Cache miss] RedisVL vector search over Redis Cloud
              → Retrieved policy chunks
              → OpenAI Chat Model
              → Final answer with citations

Usage:
    python scripts/generate_architecture_diagram.py
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — no display required
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = REPO_ROOT / "docs" / "architecture" / "redis-eats-rag-workshop-architecture.png"

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
REDIS_RED = "#DC1C1C"
REDIS_DARK = "#1A1A2E"
REDISVL_BLUE = "#1565C0"
OPENAI_GREEN = "#10A37F"
CACHE_PURPLE = "#6A0DAD"
BOX_BG = "#F5F5F5"
ARROW_GREY = "#555555"
REFUSAL_ORANGE = "#E65100"
WHITE = "#FFFFFF"
LIGHT_GREY = "#EEEEEE"


def rounded_box(ax, x, y, w, h, label, sublabel=None,
                facecolor=BOX_BG, edgecolor=REDIS_RED,
                fontsize=9, bold=False, text_color=REDIS_DARK):
    """
    Draw a rounded rectangle with a centred label (and optional sublabel).

    Args:
        ax: Matplotlib axes.
        x, y: Bottom-left corner of the box.
        w, h: Width and height.
        label: Primary label text.
        sublabel: Optional smaller text drawn below the label.
        facecolor: Box fill colour.
        edgecolor: Box border colour.
        fontsize: Primary label font size.
        bold: Whether the primary label is bold.
        text_color: Label text colour.
    """
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.5,
        zorder=3,
    )
    ax.add_patch(box)

    weight = "bold" if bold else "normal"
    cy = y + h / 2 + (0.07 if sublabel else 0)
    ax.text(x + w / 2, cy, label,
            ha="center", va="center",
            fontsize=fontsize, fontweight=weight,
            color=text_color, zorder=4)

    if sublabel:
        ax.text(x + w / 2, y + h / 2 - 0.12, sublabel,
                ha="center", va="center",
                fontsize=7, color="#666666", zorder=4,
                style="italic")


def arrow(ax, x1, y1, x2, y2, label=None, color=ARROW_GREY, label_color=ARROW_GREY):
    """
    Draw an annotated arrow between two points.

    Args:
        ax: Matplotlib axes.
        x1, y1: Start coordinates.
        x2, y2: End coordinates.
        label: Optional text drawn at the midpoint of the arrow.
        color: Arrow colour.
        label_color: Text colour for the optional label.
    """
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=1.5,
            mutation_scale=14,
        ),
        zorder=5,
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.04, my, label,
                fontsize=7, color=label_color,
                ha="left", va="center", zorder=6)


def main():
    """Render the architecture diagram and save to OUTPUT_PATH."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    # -----------------------------------------------------------------------
    # Title
    # -----------------------------------------------------------------------
    ax.text(6, 7.65, "Redis Eats RAG Workshop — Architecture",
            ha="center", va="center",
            fontsize=13, fontweight="bold", color=REDIS_DARK)
    ax.text(6, 7.35, "Don't Talk With Food In Your Mouth  |  Workshop 1: RAG Chatbot",
            ha="center", va="center",
            fontsize=8, color="#666666", style="italic")

    # -----------------------------------------------------------------------
    # Row positions (y centres)
    # -----------------------------------------------------------------------
    ROW1 = 6.5   # User question
    ROW2 = 5.2   # SemanticRouter
    ROW3 = 3.9   # Refusal  |  LangCache
    ROW4 = 2.6   # Redis Cloud (vector search)
    ROW5 = 1.3   # OpenAI
    ROW6 = 0.15  # Final answer

    BOX_H = 0.7
    BOX_W = 2.6

    # -----------------------------------------------------------------------
    # Node definitions: (cx, cy, label, sublabel, facecolor, edgecolor, bold)
    # -----------------------------------------------------------------------

    # 1 — User question
    rounded_box(ax, 4.7, ROW1 - BOX_H / 2, BOX_W, BOX_H,
                "User Question",
                facecolor=REDIS_DARK, edgecolor=REDIS_DARK,
                text_color=WHITE, bold=True)

    # 2 — SemanticRouter
    rounded_box(ax, 4.7, ROW2 - BOX_H / 2, BOX_W, BOX_H,
                "RedisVL SemanticRouter",
                sublabel="redis-eats:router",
                facecolor=REDISVL_BLUE, edgecolor=REDISVL_BLUE,
                text_color=WHITE, bold=True)

    # 3a — Refusal (left branch)
    rounded_box(ax, 1.4, ROW3 - BOX_H / 2, BOX_W, BOX_H,
                "Out-of-domain Refusal",
                sublabel='"I\'m a food delivery bot."',
                facecolor=REFUSAL_ORANGE, edgecolor=REFUSAL_ORANGE,
                text_color=WHITE)

    # 3b — LangCache (right branch)
    rounded_box(ax, 7.9, ROW3 - BOX_H / 2, BOX_W, BOX_H,
                "Redis LangCache",
                sublabel="Semantic cache check",
                facecolor=CACHE_PURPLE, edgecolor=CACHE_PURPLE,
                text_color=WHITE, bold=True)

    # Cache hit label (right side of LangCache box)
    ax.text(10.65, ROW3, "Cache\nhit →", ha="center", va="center",
            fontsize=7.5, color=CACHE_PURPLE, fontweight="bold")

    # Cache hit arrow back to answer (drawn later as a curved annotation)

    # 4 — Redis Cloud vector search
    rounded_box(ax, 4.7, ROW4 - BOX_H / 2, BOX_W, BOX_H,
                "Redis Cloud",
                sublabel="RedisVL SearchIndex  |  Vector search",
                facecolor=REDIS_RED, edgecolor=REDIS_RED,
                text_color=WHITE, bold=True)

    # 5 — OpenAI
    rounded_box(ax, 4.7, ROW5 - BOX_H / 2, BOX_W, BOX_H,
                "OpenAI Chat Model",
                sublabel="Retrieved chunks + prompt",
                facecolor=OPENAI_GREEN, edgecolor=OPENAI_GREEN,
                text_color=WHITE, bold=True)

    # 6 — Final answer
    rounded_box(ax, 4.7, ROW6 - BOX_H / 2 + 0.05, BOX_W, BOX_H,
                "Answer + Citations",
                facecolor=REDIS_DARK, edgecolor=REDIS_DARK,
                text_color=WHITE, bold=True)

    # -----------------------------------------------------------------------
    # Arrows — main flow
    # -----------------------------------------------------------------------
    cx = 6.0  # horizontal centre of main column

    # User → Router
    arrow(ax, cx, ROW1 - BOX_H / 2, cx, ROW2 + BOX_H / 2)

    # Router → Refusal (left diagonal)
    arrow(ax, 5.2, ROW2 - BOX_H / 2,
          2.7, ROW3 + BOX_H / 2,
          label="out-of-domain", color=REFUSAL_ORANGE, label_color=REFUSAL_ORANGE)

    # Router → LangCache (right diagonal)
    arrow(ax, 6.8, ROW2 - BOX_H / 2,
          9.2, ROW3 + BOX_H / 2,
          label="in-domain", color=CACHE_PURPLE, label_color=CACHE_PURPLE)

    # LangCache → Redis Cloud (cache miss — down)
    arrow(ax, cx, ROW3 - BOX_H / 2, cx, ROW4 + BOX_H / 2,
          label="cache miss", color=CACHE_PURPLE, label_color=CACHE_PURPLE)

    # Redis Cloud → OpenAI
    arrow(ax, cx, ROW4 - BOX_H / 2, cx, ROW5 + BOX_H / 2,
          label="chunks + metadata", color=REDIS_RED, label_color=REDIS_RED)

    # OpenAI → Answer
    arrow(ax, cx, ROW5 - BOX_H / 2, cx, ROW6 + BOX_H / 2 + 0.05)

    # Cache hit → Answer (curved right-side bypass arrow)
    ax.annotate(
        "", xy=(7.3, ROW6 + 0.2), xytext=(10.5, ROW3),
        arrowprops=dict(
            arrowstyle="-|>",
            color=CACHE_PURPLE,
            lw=1.5,
            mutation_scale=14,
            connectionstyle="arc3,rad=-0.35",
        ),
        zorder=5,
    )
    ax.text(10.7, 2.1, "cache\nhit", ha="center", va="center",
            fontsize=7, color=CACHE_PURPLE, fontweight="bold")

    # -----------------------------------------------------------------------
    # Legend
    # -----------------------------------------------------------------------
    legend_items = [
        mpatches.Patch(facecolor=REDISVL_BLUE, label="RedisVL"),
        mpatches.Patch(facecolor=REDIS_RED, label="Redis Cloud"),
        mpatches.Patch(facecolor=CACHE_PURPLE, label="LangCache"),
        mpatches.Patch(facecolor=OPENAI_GREEN, label="OpenAI"),
        mpatches.Patch(facecolor=REFUSAL_ORANGE, label="Out-of-domain refusal"),
    ]
    ax.legend(handles=legend_items, loc="lower left",
              fontsize=7.5, framealpha=0.9,
              bbox_to_anchor=(0.0, 0.0))

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(pad=0.5)
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight",
                facecolor=WHITE)
    plt.close(fig)
    print(f"Diagram saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
