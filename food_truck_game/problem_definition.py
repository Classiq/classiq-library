"""
Food Truck Placement Optimization — Problem Definition
======================================================

Optimization Problem
--------------------
Given N candidate locations in a city, decide which to place food trucks (x_i ∈ {0,1}).

Revenue model:
    R(x) = Σ_i (t_i − C) · x_i  −  α · Σ_{(i,j)∈E} x_i · x_j

    t_i  : foot traffic density at position i  (0–10 scale)
    C    : fixed daily truck cost               (in traffic units)
    α    : cannibalization penalty              (adjacent trucks steal each other's customers)
    E    : set of pairs of adjacent positions   (4-connected grid)

QUBO form (for minimization):
    H = Σ_i (C − t_i) · x_i  +  α · Σ_{(i,j)∈E} x_i · x_j

Display scale: 1 traffic unit ≈ $1 000/day  |  truck cost C=3 → $3 000/day
"""

from itertools import product
import json
import numpy as np

# ─── Core functions ───────────────────────────────────────────────────────────

def compute_revenue(placement, traffic, truck_cost, alpha, edges):
    """Revenue for a binary placement vector."""
    rev = sum((traffic[i] - truck_cost) * placement[i] for i in range(len(placement)))
    rev -= alpha * sum(placement[i] * placement[j] for i, j in edges)
    return rev


def brute_force_optimal(traffic, truck_cost, alpha, edges):
    """Exhaustive search over all 2^N placements."""
    n = len(traffic)
    best_rev, best_x = float("-inf"), None
    for x in product([0, 1], repeat=n):
        r = compute_revenue(x, traffic, truck_cost, alpha, edges)
        if r > best_rev:
            best_rev, best_x = r, list(x)
    return best_x, best_rev


def greedy_placement(traffic, truck_cost, alpha, edges):
    """
    Simple greedy: sort by net traffic, add each truck if it improves current revenue.
    Represents a 'reasonable human' strategy, not provably optimal.
    """
    n = len(traffic)
    current = [0] * n
    order = sorted(range(n), key=lambda i: traffic[i] - truck_cost, reverse=True)
    for pos in order:
        trial = current[:]
        trial[pos] = 1
        if compute_revenue(trial, traffic, truck_cost, alpha, edges) > \
           compute_revenue(current, traffic, truck_cost, alpha, edges):
            current = trial
    return current, compute_revenue(current, traffic, truck_cost, alpha, edges)


def build_edges(positions):
    """4-connected adjacency from a list of (row, col) positions."""
    pos_index = {p: i for i, p in enumerate(positions)}
    edges = []
    for i, (r, c) in enumerate(positions):
        for dr, dc in [(0, 1), (1, 0)]:
            nb = (r + dr, c + dc)
            if nb in pos_index:
                edges.append((i, pos_index[nb]))
    return edges


def make_qubo(traffic, truck_cost, alpha, edges):
    """Return upper-triangular QUBO matrix Q such that min x^T Q x."""
    n = len(traffic)
    Q = np.zeros((n, n))
    for i in range(n):
        Q[i, i] = truck_cost - traffic[i]
    for i, j in edges:
        Q[i, j] += alpha
    return Q


# ─── Scenario definitions ─────────────────────────────────────────────────────
#
# Layout key:
#   0 = empty street / background
#   1 = building (no truck allowed)
#   2 = candidate truck location
#
# Positions list gives (row, col) for each candidate, in the order that maps
# to qubit indices 0 … N−1.

RAW_SCENARIOS = [
    # ── Scenario 1: Street Fair (Easy, 8 locations) ──────────────────────────
    #
    # 3×4 visual grid.  High-traffic center row + moderate corners.
    # The "trap": greedily placing the two high-traffic centre spots (3 & 4)
    # activates heavy cannibalization and blocks four surrounding profitable spots.
    # Optimal skips position 4 (traffic=8) to unlock a non-adjacent ring of 4.
    #
    #  grid:  [ B ][ 0 ][ 1 ][ B ]
    #         [ 2 ][ 3 ][ 4 ][ 5 ]
    #         [ B ][ 6 ][ 7 ][ B ]
    {
        "id": 1,
        "name": "Street Fair",
        "difficulty": "Easy",
        "description": (
            "A weekend street fair. Two high-traffic centre spots look tempting, "
            "but placing trucks too close together cannibalizes revenue."
        ),
        "grid_rows": 3,
        "grid_cols": 4,
        "layout": [
            [1, 2, 2, 1],
            [2, 2, 2, 2],
            [1, 2, 2, 1],
        ],
        "positions": [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2)],
        "traffic":   [    7,      5,      4,      9,      8,      6,      3,      7],
        "truck_cost": 3.0,
        "alpha": 4.5,
    },

    # ── Scenario 2: Business District (Medium, 12 locations) ─────────────────
    #
    # 3×4 full grid.  Three vertical "hot corridors" that compete with each other.
    # Greedy loads up the middle column (best individual traffic), but the optimal
    # solution alternates columns to avoid all horizontal adjacency penalties.
    #
    #  grid:  [ 0 ][ 1 ][ 2 ][ 3 ]
    #         [ 4 ][ 5 ][ 6 ][ 7 ]
    #         [ 8 ][ 9 ][10 ][11 ]
    {
        "id": 2,
        "name": "Business District",
        "difficulty": "Medium",
        "description": (
            "Dense office blocks generate strong foot traffic, but every street is "
            "packed—trucks placed too close pull the same lunch crowd."
        ),
        "grid_rows": 3,
        "grid_cols": 4,
        "layout": [
            [2, 2, 2, 2],
            [2, 2, 2, 2],
            [2, 2, 2, 2],
        ],
        "positions": [(r, c) for r in range(3) for c in range(4)],
        "traffic":   [4, 8, 7, 3,
                      6, 9, 9, 5,
                      3, 7, 8, 4],
        "truck_cost": 3.0,
        "alpha": 3.5,
    },

    # ── Scenario 3: Festival Grounds (Hard, 16 locations) ────────────────────
    #
    # Full 4×4 grid.  Four diagonal "hotspot clusters" each containing a 9 and 8.
    # Players must decide which clusters to commit to and which to sacrifice.
    # Tight budget: truck_cost=4 makes marginal positions cost-negative, so
    # over-placing is heavily penalized.
    #
    #  grid:  [ 0 ][ 1 ][ 2 ][ 3 ]
    #         [ 4 ][ 5 ][ 6 ][ 7 ]
    #         [ 8 ][ 9 ][10 ][11 ]
    #         [12 ][13 ][14 ][15 ]
    {
        "id": 3,
        "name": "Festival Grounds",
        "difficulty": "Hard",
        "description": (
            "A multi-stage festival with four intense crowd clusters. "
            "Tighter margins and a larger grid mean small mistakes compound fast."
        ),
        "grid_rows": 4,
        "grid_cols": 4,
        "layout": [
            [2, 2, 2, 2],
            [2, 2, 2, 2],
            [2, 2, 2, 2],
            [2, 2, 2, 2],
        ],
        "positions": [(r, c) for r in range(4) for c in range(4)],
        # Four t=9 center spots dominate greedy's attention, but each one
        # blocks four neighbors worth 5 each.  The optimal solution skips
        # two center spots and collects an 8-truck non-adjacent ring instead.
        "traffic":   [3, 8, 3, 7,
                      8, 9, 9, 4,
                      4, 9, 9, 8,
                      7, 3, 8, 3],
        "truck_cost": 3.0,
        "alpha": 5.0,
    },
]


# ─── Solve all scenarios ──────────────────────────────────────────────────────

def solve_scenario(s):
    positions = [tuple(p) for p in s["positions"]]
    edges     = build_edges(positions)
    traffic   = s["traffic"]
    C         = s["truck_cost"]
    alpha     = s["alpha"]

    opt_x,    opt_rev    = brute_force_optimal(traffic, C, alpha, edges)
    greedy_x, greedy_rev = greedy_placement(traffic, C, alpha, edges)

    qubo = make_qubo(traffic, C, alpha, edges)

    # Score a random placement to show breadth of possible scores
    rng = np.random.default_rng(42)
    random_x = list(rng.integers(0, 2, len(traffic)))
    random_rev = compute_revenue(random_x, traffic, C, alpha, edges)

    return {
        **s,
        "positions": positions,
        "edges": edges,
        "n_qubits": len(positions),
        "optimal_placement": opt_x,
        "optimal_revenue": float(opt_rev),
        "greedy_placement": greedy_x,
        "greedy_revenue": float(greedy_rev),
        "random_revenue": float(random_rev),
        "qubo": qubo.tolist(),
        "is_nontrivial": opt_x != greedy_x,
        "greedy_gap": float(opt_rev - greedy_rev),
        "greedy_score_pct": round(greedy_rev / opt_rev * 100, 1) if opt_rev > 0 else None,
    }


def print_scenario_summary(s):
    n = s["n_qubits"]
    net = [round(s["traffic"][i] - s["truck_cost"], 1) for i in range(n)]
    print(f"\n{'─'*60}")
    print(f"Scenario {s['id']}: {s['name']}  [{s['difficulty']}]  — {n} qubits")
    print(f"{'─'*60}")
    print(f"  Traffic values : {s['traffic']}")
    print(f"  Net values     : {net}")
    print(f"  Truck cost C   : {s['truck_cost']}   Cannibalization α: {s['alpha']}")
    print(f"  Edges          : {s['edges']}")
    print()
    placed_opt    = [i for i, x in enumerate(s['optimal_placement'])  if x]
    placed_greedy = [i for i, x in enumerate(s['greedy_placement'])   if x]
    print(f"  Optimal   placement: {placed_opt} → revenue {s['optimal_revenue']:.1f}")
    print(f"  Greedy    placement: {placed_greedy} → revenue {s['greedy_revenue']:.1f}")
    print(f"  Non-trivial        : {s['is_nontrivial']}")
    if s['is_nontrivial']:
        print(f"  Greedy gap         : {s['greedy_gap']:.1f} units "
              f"({s['greedy_score_pct']:.1f}% of optimal)")
    else:
        print(f"  ⚠  Greedy matches optimal — consider adjusting alpha.")
    print()
    # Show QUBO diagonal (linear terms) to verify sign direction
    diag = [round(s['qubo'][i][i], 2) for i in range(n)]
    print(f"  QUBO diagonal (C−t): {diag}")


if __name__ == "__main__":
    print("Food Truck Game — Problem Definition & Scenario Validation")
    print("=" * 60)

    solved = []
    all_nontrivial = True

    for raw in RAW_SCENARIOS:
        s = solve_scenario(raw)
        print_scenario_summary(s)
        solved.append(s)
        if not s["is_nontrivial"]:
            all_nontrivial = False

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for s in solved:
        status = "✓ non-trivial" if s["is_nontrivial"] else "✗ TRIVIAL"
        print(f"  Scenario {s['id']} ({s['difficulty']:6s}): "
              f"N={s['n_qubits']:2d} qubits | "
              f"opt={s['optimal_revenue']:.1f} | "
              f"greedy={s['greedy_revenue']:.1f} ({s['greedy_score_pct']}%) | "
              f"{status}")

    if all_nontrivial:
        print("\n✓ All scenarios are non-trivial — greedy never finds optimal.")
    else:
        print("\n✗ Some scenarios are trivial. Adjust traffic or alpha values.")

    # Export clean JSON for use in game HTML
    export = []
    for s in solved:
        export.append({
            "id":               s["id"],
            "name":             s["name"],
            "difficulty":       s["difficulty"],
            "description":      s["description"],
            "grid_rows":        s["grid_rows"],
            "grid_cols":        s["grid_cols"],
            "layout":           s["layout"],
            "positions":        [list(p) for p in s["positions"]],
            "edges":            s["edges"],
            "traffic":          s["traffic"],
            "truck_cost":       s["truck_cost"],
            "alpha":            s["alpha"],
            "n_qubits":         s["n_qubits"],
            "optimal_placement": s["optimal_placement"],
            "optimal_revenue":   s["optimal_revenue"],
            "greedy_placement":  s["greedy_placement"],
            "greedy_revenue":    s["greedy_revenue"],
        })

    out_path = "food_truck_game/scenarios.json"
    with open(out_path, "w") as f:
        json.dump(export, f, indent=2)
    print(f"\n✓ Exported scenario data → {out_path}")
