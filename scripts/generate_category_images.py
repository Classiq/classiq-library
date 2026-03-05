#!/usr/bin/env python3
"""
Generate a representative quantum-themed image for each notebook category.
Requires: matplotlib (pip install matplotlib)
Output: REPO_ROOT/category_images/<Category.name>.png
"""

import sys
from pathlib import Path

import matplotlib.patches as mpatches

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "category_images"

# Reuse Category enum from build_notebook_categories for single source of truth
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from build_notebook_categories import Category


def draw_chemistry(ax, w, h):
    """Molecular / lattice motif."""
    ax.set_facecolor("#0d1f2d")
    n = 5
    for i in range(n):
        for j in range(n):
            x, y = 0.2 + 0.6 * i / (n - 1), 0.2 + 0.6 * j / (n - 1)
            ax.add_patch(
                mpatches.Circle(
                    (x, y),
                    0.04,
                    facecolor="#2dd4bf",
                    edgecolor="#14b8a6",
                    linewidth=1.5,
                )
            )
    for i in range(n - 1):
        for j in range(n):
            ax.plot(
                [0.2 + 0.6 * i / (n - 1), 0.2 + 0.6 * (i + 1) / (n - 1)],
                [0.2 + 0.6 * j / (n - 1)] * 2,
                color="#5eead4",
                alpha=0.6,
                linewidth=1.5,
            )
            if j < n - 1:
                ax.plot(
                    [0.2 + 0.6 * (i + 0.5) / (n - 1)] * 2,
                    [0.2 + 0.6 * j / (n - 1), 0.2 + 0.6 * (j + 1) / (n - 1)],
                    color="#5eead4",
                    alpha=0.5,
                    linewidth=1,
                )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_qml(ax, w, h):
    """Neural nodes + qubit line."""
    ax.set_facecolor("#1e1b4b")
    # Qubit line
    ax.plot([0.1, 0.9], [0.5, 0.5], color="#a78bfa", linewidth=3, alpha=0.9)
    # Nodes (circles)
    for x in [0.25, 0.5, 0.75]:
        for y in [0.25, 0.5, 0.75]:
            ax.add_patch(
                mpatches.Circle(
                    (x, y),
                    0.06,
                    facecolor="#8b5cf6",
                    edgecolor="#c4b5fd",
                    linewidth=1.5,
                )
            )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_finance(ax, w, h):
    """Chart-like curve + grid."""
    ax.set_facecolor("#0f172a")
    import numpy as np

    x = np.linspace(0.1, 0.9, 50)
    y = 0.3 + 0.4 * np.exp(-((x - 0.5) ** 2) / 0.08) + 0.1 * np.sin(12 * x)
    ax.plot(x, y, color="#fbbf24", linewidth=2.5, alpha=0.95)
    ax.fill_between(x, 0.25, y, color="#fbbf24", alpha=0.2)
    for i in range(1, 5):
        ax.axhline(0.2 + 0.2 * i, color="#334155", linewidth=0.5, alpha=0.5)
        ax.axvline(0.2 + 0.2 * i, color="#334155", linewidth=0.5, alpha=0.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.2, 0.9)
    ax.axis("off")


def draw_search_amplitude(ax, w, h):
    """Amplitude bars / Grover-style."""
    ax.set_facecolor("#431407")
    import numpy as np

    n = 8
    x = np.linspace(0.15, 0.85, n)
    heights = 0.1 + 0.5 * np.exp(-((x - 0.5) ** 2) / 0.05)
    heights[3] = 0.75
    colors = ["#fb923c" if i == 3 else "#fdba74" for i in range(n)]
    ax.bar(x, heights, width=0.06, color=colors, edgecolor="#ea580c", linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.9)
    ax.axis("off")


def draw_linear_algebra(ax, w, h):
    """Matrix grid + circuit line."""
    ax.set_facecolor("#0c4a6e")
    import numpy as np

    n = 4
    for i in range(n):
        for j in range(n):
            val = (i + j) % 2
            ax.add_patch(
                mpatches.Rectangle(
                    (0.15 + 0.2 * j, 0.15 + 0.2 * (n - 1 - i)),
                    0.18,
                    0.18,
                    facecolor="#0ea5e9" if val else "#38bdf8",
                    edgecolor="#7dd3fc",
                    linewidth=1,
                    alpha=0.8,
                )
            )
    ax.plot([0.05, 0.95], [0.5, 0.5], color="#f0f9ff", linewidth=2, alpha=0.9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_foundational(ax, w, h):
    """Simple circuit: qubit line + gates."""
    ax.set_facecolor("#1c1917")
    ax.plot([0.1, 0.9], [0.5, 0.5], color="#e7e5e4", linewidth=2)
    for x in [0.25, 0.5, 0.75]:
        ax.add_patch(
            mpatches.Rectangle(
                (x - 0.05, 0.4),
                0.1,
                0.2,
                facecolor="#a8a29e",
                edgecolor="#d6d3d1",
                linewidth=1.5,
            )
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_combinatorial(ax, w, h):
    """Graph nodes + edges (optimization)."""
    ax.set_facecolor("#450a0a")
    import numpy as np

    np.random.seed(42)
    n = 6
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    cx, cy = 0.5, 0.5
    r = 0.35
    xs = cx + r * np.cos(theta)
    ys = cy + r * np.sin(theta)
    for i in range(n):
        for j in range(i + 1, n):
            if (i - j) % n in (1, 2):
                ax.plot(
                    [xs[i], xs[j]],
                    [ys[i], ys[j]],
                    color="#f87171",
                    linewidth=1.5,
                    alpha=0.7,
                )
    for i in range(n):
        ax.add_patch(
            mpatches.Circle(
                (xs[i], ys[i]),
                0.06,
                facecolor="#dc2626",
                edgecolor="#fca5a5",
                linewidth=1.5,
            )
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_physics_simulation(ax, w, h):
    """Wave / Hamiltonian evolution."""
    ax.set_facecolor("#172554")
    import numpy as np

    x = np.linspace(0.05, 0.95, 100)
    y = 0.5 + 0.35 * np.sin(8 * np.pi * x) * np.exp(-2 * (x - 0.5) ** 2)
    ax.plot(x, y, color="#93c5fd", linewidth=2.5, alpha=0.95)
    ax.fill_between(x, 0.5, y, color="#60a5fa", alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.1, 0.9)
    ax.axis("off")


def draw_quantum_walks(ax, w, h):
    """Path / tree of nodes."""
    ax.set_facecolor("#042f2e")
    import numpy as np

    # Simple path
    path_x = [0.2, 0.35, 0.5, 0.65, 0.8]
    path_y = [0.5, 0.65, 0.5, 0.35, 0.5]
    ax.plot(
        path_x,
        path_y,
        color="#5eead4",
        linewidth=2,
        alpha=0.8,
        marker="o",
        markersize=10,
        markerfacecolor="#2dd4bf",
        markeredgecolor="#14b8a6",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0.2, 0.8)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_tutorials(ax, w, h):
    """Play / book + circuit."""
    ax.set_facecolor("#1e3a5f")
    ax.plot([0.2, 0.8], [0.5, 0.5], color="#bae6fd", linewidth=2, alpha=0.9)
    # Triangle (play)
    ax.add_patch(
        mpatches.Polygon(
            [[0.45, 0.35], [0.45, 0.65], [0.7, 0.5]],
            facecolor="#38bdf8",
            edgecolor="#7dd3fc",
            linewidth=1.5,
        )
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_other(ax, w, h):
    """Generic quantum (superposition symbol)."""
    ax.set_facecolor("#27272a")
    import numpy as np

    theta = np.linspace(0, 2 * np.pi, 80)
    ax.plot(
        0.5 + 0.25 * np.cos(theta),
        0.5 + 0.25 * np.sin(theta),
        color="#a1a1aa",
        linewidth=2,
        alpha=0.9,
    )
    ax.plot([0.35, 0.65], [0.5, 0.5], color="#d4d4d8", linewidth=2, alpha=0.9)
    ax.plot([0.5, 0.5], [0.35, 0.65], color="#d4d4d8", linewidth=2, alpha=0.9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")


DRAWERS = {
    Category.CHEMISTRY: draw_chemistry,
    Category.QML: draw_qml,
    Category.FINANCE: draw_finance,
    Category.SEARCH_AMPLITUDE: draw_search_amplitude,
    Category.LINEAR_ALGEBRA: draw_linear_algebra,
    Category.FOUNDATIONAL: draw_foundational,
    Category.COMBINATORIAL_OPTIMIZATION: draw_combinatorial,
    Category.PHYSICS_SIMULATION: draw_physics_simulation,
    Category.QUANTUM_WALKS: draw_quantum_walks,
    Category.TUTORIALS: draw_tutorials,
    Category.OTHER: draw_other,
}


def generate_image(category: Category, size=(512, 512), dpi=100):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    w, h = size[0] / dpi, size[1] / dpi
    fig, ax = plt.subplots(1, 1, figsize=(w, h), dpi=dpi)
    drawer = DRAWERS.get(category, draw_other)
    drawer(ax, w, h)
    ax.set_title(category.value, fontsize=14, color="white", pad=12, fontweight="bold")
    fig.tight_layout()
    out_path = OUTPUT_DIR / f"{category.name}.png"
    fig.savefig(
        out_path,
        dpi=dpi,
        bbox_inches="tight",
        facecolor=ax.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    return out_path


def main():
    try:
        import matplotlib
    except ImportError:
        print("Error: matplotlib is required. Install with: pip install matplotlib")
        raise SystemExit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for cat in Category:
        path = generate_image(cat)
        print(f"  {cat.name}.png")
    print(f"\nGenerated {len(Category)} images in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
