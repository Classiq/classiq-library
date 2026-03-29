"""
Exhaustive search over all 12^3 = 1728 bulk schedule combinations.

For each of 12 red bulk schedules, the corresponding green and blue schedules
are obtained by rotation:
- Green[i] = Red[(i+4) % 6]  (shift left by 4)
- Blue[i] = Red[(i+2) % 6]   (shift left by 2)

This exploits the 3-fold rotational symmetry of the color code.
"""

import numpy as np
from itertools import product
from color_code_stim import ColorCode
from compare_schedules import schedule_to_cnot_dict_by_color_and_type
from ilp_circuit_distance import mip_circuit_distance
from custom_error_model import apply_custom_error_model, get_edge_ancilla_qids
from visualize_minimal_error import visualize_errors_grid, print_minimal_representatives
import time


def get_red_bulk_schedules():
    """
    Generate all 12 valid red bulk schedules.

    Select 2 non-overlapping pairs from:
      (a,c), (b,c), (b,f), (c,d), (c,e), (c,f), (d,f)
    Then remaining 2 elements form the middle pair.
    Try both orderings of the middle pair.
    """
    from itertools import combinations

    all_elements = set(range(6))

    # Allowed pairs (a=0, b=1, c=2, d=3, e=4, f=5)
    allowed_pairs = [
        (0, 2),  # (a, c)
        (1, 2),  # (b, c)
        (1, 5),  # (b, f)
        (2, 3),  # (c, d)
        (2, 4),  # (c, e)
        (2, 5),  # (c, f)
        (3, 5),  # (d, f)
    ]

    # Find all valid selections of 2 non-overlapping pairs
    valid_selections = []
    for i, pair1 in enumerate(allowed_pairs):
        for pair2 in allowed_pairs[i + 1 :]:
            if set(pair1) & set(pair2):  # They share an element
                continue
            remaining = tuple(sorted(all_elements - set(pair1) - set(pair2)))
            valid_selections.append((pair1, pair2, remaining))

    # Generate schedules
    schedules = []
    for first_pair, last_pair, middle in valid_selections:
        for mid_order in [0, 1]:
            schedule = [0] * 6
            schedule[first_pair[0]] = 1
            schedule[first_pair[1]] = 2
            schedule[last_pair[0]] = 5
            schedule[last_pair[1]] = 6
            if mid_order == 0:
                schedule[middle[0]] = 3
                schedule[middle[1]] = 4
            else:
                schedule[middle[0]] = 4
                schedule[middle[1]] = 3
            schedules.append(schedule)

    return schedules


def rotate_schedule(schedule, shift):
    """Rotate a schedule by shifting positions."""
    return [schedule[(i + shift) % 6] for i in range(6)]


def get_all_color_schedules():
    """
    Get all 12 schedules for each color.
    Green and blue are rotations of red.
    """
    red_schedules = get_red_bulk_schedules()

    # Generate green and blue by rotation
    green_schedules = [rotate_schedule(s, 4) for s in red_schedules]
    blue_schedules = [rotate_schedule(s, 2) for s in red_schedules]

    return red_schedules, green_schedules, blue_schedules


def compute_circuit_distance(colorcode, method="ilp"):
    """
    Compute the circuit-level distance.

    Args:
        colorcode: ColorCode instance
        method: 'ilp' for exact ILP solver (OR-Tools/SCIP),
                'stim' for stim's heuristic search
        time_limit: Time limit in seconds (for ILP method)

    Returns:
        Circuit-level distance (int)
    """
    if method == "ilp":
        dem = colorcode.circuit.detector_error_model()
        result = mip_circuit_distance(dem, time_limit=None, verbose=False)
        if result["distance"] is None:
            raise RuntimeError(f"ILP solver failed with status: {result['status']}")
        return result["distance"]

    elif method == "stim":
        errors = colorcode.circuit.search_for_undetectable_logical_errors(
            dont_explore_detection_event_sets_with_size_above=4,
            dont_explore_edges_with_degree_above=9999,
            dont_explore_edges_increasing_symptom_degree=False,
            canonicalize_circuit_errors=False,
        )
        return len(errors)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'ilp' or 'stim'.")


def exhaustive_search(
    d=7, rounds=1, p_cnot=1e-3, method="ilp", use_custom_error_model=False, verbose=True
):
    """
    Search all 12^3 = 1728 combinations of bulk schedules.

    Args:
        d: Code distance
        rounds: Number of syndrome extraction rounds
        p_cnot: CNOT error probability
        method: 'ilp' for exact ILP solver, 'stim' for heuristic search
        use_custom_error_model: If True, use DEPOLARIZE1 before/after CNOT instead of DEPOLARIZE2,
                                with special handling for edge plaquettes
        verbose: Print progress updates

    Uses fixed edge schedules:
        'r': [1, 4, 2, 6, 3, 5],
        'b': [1, 5, 3, 6, 2, 4],
        'g': [4, 2, 6, 3, 5, 1],
    """
    # Fixed edge schedules (with X part appended)
    edge_schedules = {
        "r": [1, 4, 2, 6, 3, 5],
        "b": [1, 5, 3, 6, 2, 4],
        "g": [4, 2, 6, 3, 5, 1],
    }
    for color in ["r", "g", "b"]:
        edge_schedules[color] = edge_schedules[color] + [
            x + 6 for x in edge_schedules[color]
        ]

    # Get all bulk schedules for each color
    red_bulk, green_bulk, blue_bulk = get_all_color_schedules()

    print(f"Red bulk schedules: {len(red_bulk)}")
    print(f"Green bulk schedules: {len(green_bulk)}")
    print(f"Blue bulk schedules: {len(blue_bulk)}")
    print(f"Total combinations: {len(red_bulk) * len(green_bulk) * len(blue_bulk)}")
    if use_custom_error_model:
        print("Using CUSTOM error model (DEPOLARIZE1 before/after CNOT)")
    print()

    # Build initial ColorCode to get structure (with p_cnot=0 if using custom error model)
    init_p_cnot = 0 if use_custom_error_model else p_cnot
    colorcode_init = ColorCode(
        d=d,
        rounds=rounds,
        cnot_schedule="tri_optimal",
        p_cnot=init_p_cnot,
        exclude_non_essential_pauli_detectors=True,
    )

    # Track best results
    best_distance = 0
    best_configs = []
    all_results = []

    total = len(red_bulk) * len(green_bulk) * len(blue_bulk)
    start_time = time.time()

    for idx, (r_idx, g_idx, b_idx) in enumerate(
        product(range(len(red_bulk)), range(len(green_bulk)), range(len(blue_bulk)))
    ):
        # Build bulk schedules for this combination
        bulk_schedules = {
            "r": red_bulk[r_idx] + [x + 6 for x in red_bulk[r_idx]],
            "g": green_bulk[g_idx] + [x + 6 for x in green_bulk[g_idx]],
            "b": blue_bulk[b_idx] + [x + 6 for x in blue_bulk[b_idx]],
        }

        # Combine bulk and edge schedules
        schedules_by_color_and_type = {
            color: {"bulk": bulk_schedules[color], "edge": edge_schedules[color]}
            for color in ["r", "g", "b"]
        }

        # Build schedule dict
        cnot_dict = schedule_to_cnot_dict_by_color_and_type(
            colorcode_init, schedules_by_color_and_type
        )

        # Build ColorCode with this schedule
        build_p_cnot = 0 if use_custom_error_model else p_cnot
        colorcode = ColorCode(
            d=d,
            rounds=rounds,
            cnot_schedule=cnot_dict,
            p_cnot=build_p_cnot,
            exclude_non_essential_pauli_detectors=True,
        )

        # Apply custom error model if requested
        if use_custom_error_model:
            colorcode.circuit = apply_custom_error_model(colorcode, p_cnot)

        # Compute distance
        distance = compute_circuit_distance(colorcode, method=method)

        config = {
            "r_idx": r_idx,
            "g_idx": g_idx,
            "b_idx": b_idx,
            "r_schedule": red_bulk[r_idx],
            "g_schedule": green_bulk[g_idx],
            "b_schedule": blue_bulk[b_idx],
            "distance": distance,
        }
        all_results.append(config)

        if distance > best_distance:
            best_distance = distance
            best_configs = [config]
            if verbose:
                print(f"[{idx+1}/{total}] New best distance: {distance}")
                print(
                    f"  R: {red_bulk[r_idx]}, G: {green_bulk[g_idx]}, B: {blue_bulk[b_idx]}"
                )
        elif distance == best_distance:
            best_configs.append(config)

        # Progress update
        if verbose and (idx + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed
            remaining = (total - idx - 1) / rate
            print(
                f"[{idx+1}/{total}] Elapsed: {elapsed:.1f}s, ETA: {remaining:.1f}s, Best: {best_distance}"
            )

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("SEARCH COMPLETE")
    print("=" * 80)
    print(f"Total time: {elapsed:.1f}s")
    print(f"Best circuit distance: {best_distance}")
    print(f"Number of configurations with best distance: {len(best_configs)}")
    print()

    # Print best configurations
    print("Best configurations:")
    for i, cfg in enumerate(best_configs[:10], 1):  # Show first 10
        print(f"\n{i}. Distance={cfg['distance']}")
        print(f"   R (idx={cfg['r_idx']}): {cfg['r_schedule']}")
        print(f"   G (idx={cfg['g_idx']}): {cfg['g_schedule']}")
        print(f"   B (idx={cfg['b_idx']}): {cfg['b_schedule']}")

    if len(best_configs) > 10:
        print(
            f"\n... and {len(best_configs) - 10} more configurations with same distance"
        )

    # Distribution of distances
    distances = [r["distance"] for r in all_results]
    unique_distances = sorted(set(distances))
    print("\n" + "=" * 80)
    print("DISTANCE DISTRIBUTION")
    print("=" * 80)
    for dist in unique_distances:
        count = distances.count(dist)
        print(
            f"Distance {dist}: {count} configurations ({100*count/len(distances):.1f}%)"
        )

    return best_configs, all_results


def test_configs_on_d(
    configs,
    d,
    rounds=1,
    p_cnot=1e-3,
    method="ilp",
    use_custom_error_model=False,
    verbose=True,
):
    """
    Test a list of configurations on a specific code distance.

    Args:
        configs: List of config dicts (from exhaustive_search results)
        d: Code distance to test on
        rounds: Number of syndrome extraction rounds
        p_cnot: CNOT error probability
        method: 'ilp' or 'stim'
        use_custom_error_model: If True, use DEPOLARIZE1 before/after CNOT instead of DEPOLARIZE2
        verbose: Print progress

    Returns:
        List of configs with updated distances for this d
    """
    # Fixed edge schedules
    edge_schedules = {
        "r": [1, 4, 2, 6, 3, 5],
        "b": [1, 5, 3, 6, 2, 4],
        "g": [4, 2, 6, 3, 5, 1],
    }
    for color in ["r", "g", "b"]:
        edge_schedules[color] = edge_schedules[color] + [
            x + 6 for x in edge_schedules[color]
        ]

    # Build initial ColorCode to get structure
    init_p_cnot = 0 if use_custom_error_model else p_cnot
    colorcode_init = ColorCode(
        d=d,
        rounds=rounds,
        cnot_schedule="tri_optimal",
        p_cnot=init_p_cnot,
        exclude_non_essential_pauli_detectors=True,
    )

    results = []

    for i, cfg in enumerate(configs):
        if verbose:
            print(
                f"[{i+1}/{len(configs)}] Testing config r={cfg['r_idx']}, g={cfg['g_idx']}, b={cfg['b_idx']} on d={d}..."
            )

        # Build bulk schedules
        bulk_schedules = {
            "r": cfg["r_schedule"] + [x + 6 for x in cfg["r_schedule"]],
            "g": cfg["g_schedule"] + [x + 6 for x in cfg["g_schedule"]],
            "b": cfg["b_schedule"] + [x + 6 for x in cfg["b_schedule"]],
        }

        # Combine bulk and edge schedules
        schedules_by_color_and_type = {
            color: {"bulk": bulk_schedules[color], "edge": edge_schedules[color]}
            for color in ["r", "g", "b"]
        }

        # Build schedule dict
        cnot_dict = schedule_to_cnot_dict_by_color_and_type(
            colorcode_init, schedules_by_color_and_type
        )

        # Build ColorCode with this schedule
        build_p_cnot = 0 if use_custom_error_model else p_cnot
        colorcode = ColorCode(
            d=d,
            rounds=rounds,
            cnot_schedule=cnot_dict,
            p_cnot=build_p_cnot,
            exclude_non_essential_pauli_detectors=True,
        )

        # Apply custom error model if requested
        if use_custom_error_model:
            colorcode.circuit = apply_custom_error_model(colorcode, p_cnot)

        # Compute distance
        distance = compute_circuit_distance(colorcode, method=method)

        # Copy config and add new distance
        result = cfg.copy()
        result[f"distance_d{d}"] = distance
        results.append(result)

        if verbose:
            print(f"    Distance at d={d}: {distance}")

    return results


def save_results(results, filename, d=None, metadata=None):
    """Save results to a pickle file with metadata."""
    import pickle

    data = {
        "results": results,
        "d": d,
        "metadata": metadata or {},
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)
    print(f"Results saved to {filename}")


def load_results(filename):
    """Load results from a pickle file."""
    import pickle

    with open(filename, "rb") as f:
        data = pickle.load(f)
    return data


def get_best_configs(results, distance_key="distance", top_n=None):
    """
    Get configurations with the highest distance.

    Args:
        results: List of config dicts
        distance_key: Key to use for distance comparison
        top_n: If set, return top N distances (not just the max)

    Returns:
        List of configs with best distance(s)
    """
    if not results:
        return []

    distances = sorted(set(r[distance_key] for r in results), reverse=True)

    if top_n:
        target_distances = distances[:top_n]
    else:
        target_distances = [distances[0]]

    return [r for r in results if r[distance_key] in target_distances]


def visualize_config_minimal_error(
    cfg,
    d,
    rounds=1,
    p_cnot=1e-3,
    use_custom_error_model=False,
    save_prefix="minimal_error",
):
    """
    Visualize the minimal undetectable logical error for a configuration.

    Args:
        cfg: Config dict with r_schedule, g_schedule, b_schedule
        d: Code distance
        rounds: Number of syndrome extraction rounds
        p_cnot: CNOT error probability
        use_custom_error_model: Use custom DEPOLARIZE1 model
        save_prefix: Prefix for saved image files

    Returns:
        errors: List of ExplainedError objects
    """
    # Fixed edge schedules
    edge_schedules = {
        "r": [1, 4, 2, 6, 3, 5],
        "b": [1, 5, 3, 6, 2, 4],
        "g": [4, 2, 6, 3, 5, 1],
    }
    for color in ["r", "g", "b"]:
        edge_schedules[color] = edge_schedules[color] + [
            x + 6 for x in edge_schedules[color]
        ]

    # Build bulk schedules
    bulk_schedules = {
        "r": cfg["r_schedule"] + [x + 6 for x in cfg["r_schedule"]],
        "g": cfg["g_schedule"] + [x + 6 for x in cfg["g_schedule"]],
        "b": cfg["b_schedule"] + [x + 6 for x in cfg["b_schedule"]],
    }

    # Combine bulk and edge schedules
    schedules_by_color_and_type = {
        color: {"bulk": bulk_schedules[color], "edge": edge_schedules[color]}
        for color in ["r", "g", "b"]
    }

    # Build initial ColorCode to get structure
    init_p_cnot = 0 if use_custom_error_model else p_cnot
    colorcode_init = ColorCode(
        d=d,
        rounds=rounds,
        cnot_schedule="tri_optimal",
        p_cnot=init_p_cnot,
        exclude_non_essential_pauli_detectors=True,
    )

    # Build schedule dict
    cnot_dict = schedule_to_cnot_dict_by_color_and_type(
        colorcode_init, schedules_by_color_and_type
    )

    # Build ColorCode with this schedule
    build_p_cnot = 0 if use_custom_error_model else p_cnot
    colorcode = ColorCode(
        d=d,
        rounds=rounds,
        cnot_schedule=cnot_dict,
        p_cnot=build_p_cnot,
        exclude_non_essential_pauli_detectors=True,
    )

    # Apply custom error model if requested
    if use_custom_error_model:
        colorcode.circuit = apply_custom_error_model(colorcode, p_cnot)

    # Print Crumble URL for the circuit
    import urllib.parse

    crumble_url = "https://algassert.com/crumble#circuit=" + urllib.parse.quote(
        str(colorcode.circuit), safe=""
    )
    print(f"\nCrumble URL:\n{crumble_url}")

    # Find minimal undetectable logical errors
    errors = colorcode.circuit.search_for_undetectable_logical_errors(
        dont_explore_detection_event_sets_with_size_above=5,
        dont_explore_edges_with_degree_above=9999,
        dont_explore_edges_increasing_symptom_degree=False,
        canonicalize_circuit_errors=False,
    )

    # Print error details
    print(f"\nMinimal error weight: {len(errors)}")
    print_minimal_representatives(errors)

    # Visualize errors in grid
    title = (
        f"d={d}, R:{cfg['r_schedule']}, G:{cfg['g_schedule']}, B:{cfg['b_schedule']}"
    )
    visualize_errors_grid(
        colorcode, errors, title_prefix=title, save_name=f"{save_prefix}_d{d}.png"
    )

    return errors


def main():
    import pickle
    import os

    # ============================================================
    # CONFIGURATION - Change these parameters as needed
    # ============================================================
    d1 = 7  # First distance (exhaustive search)
    d2 = 7  # Second distance (test best configs)
    rounds = 1  # Number of syndrome extraction rounds
    p_cnot = 1e-3  # CNOT error probability
    method_d1 = "ilp"  # Method for d1 search: 'ilp' or 'stim'
    method_d2 = "ilp"  # Method for d2 testing: 'ilp' or 'stim'
    top_n_tiers = 1  # Number of top distance tiers to test on d2
    use_custom_error_model = (
        False  # Use DEPOLARIZE1 before/after CNOT (with edge handling)
    )
    # ============================================================

    print("=" * 80)
    print("EXHAUSTIVE SCHEDULE SEARCH (12^3 = 1728 combinations)")
    print("=" * 80)
    print(f"\nConfiguration: d1={d1}, d2={d2}, rounds={rounds}, p_cnot={p_cnot}")
    print(f"Methods: d1={method_d1}, d2={method_d2}")
    print(f"Custom error model: {use_custom_error_model}")
    print()

    # Step 1: Run exhaustive search on d1 (or load from file if exists)
    d1_results_file = f"search_results_d{d1}.pkl"

    if os.path.exists(d1_results_file):
        print(f"STEP 1: Loading existing results from {d1_results_file}")
        print("-" * 40)
        data = load_results(d1_results_file)
        # Handle both old format ('all_results') and new format ('results')
        all_results_d1 = data.get("results") or data.get("all_results")
        print(f"Loaded {len(all_results_d1)} configurations from d={d1} search")

        # Print distance distribution
        distances = [r["distance"] for r in all_results_d1]
        unique_distances = sorted(set(distances), reverse=True)
        print("\nDistance distribution:")
        for dist in unique_distances:
            count = distances.count(dist)
            print(
                f"  Distance {dist}: {count} configurations ({100*count/len(distances):.1f}%)"
            )
    else:
        print(f"STEP 1: Exhaustive search on d={d1}")
        print("-" * 40)
        best_configs_d1, all_results_d1 = exhaustive_search(
            d=d1,
            rounds=rounds,
            p_cnot=p_cnot,
            method=method_d1,
            use_custom_error_model=use_custom_error_model,
            verbose=True,
        )

        # Save d1 results
        save_results(
            all_results_d1,
            d1_results_file,
            d=d1,
            metadata={
                "rounds": rounds,
                "p_cnot": p_cnot,
                "method": method_d1,
                "custom_error_model": use_custom_error_model,
            },
        )

    # Get configs with top N distance tiers
    best_configs = get_best_configs(
        all_results_d1, distance_key="distance", top_n=top_n_tiers
    )
    print(f"\nFound {len(best_configs)} configs in top {top_n_tiers} distance tier(s)")

    # Step 2: Visualize minimal error for the best config on d1
    if best_configs:
        print("\n" + "=" * 80)
        print(f"STEP 2: Visualizing minimal error for best config on d={d1}")
        print("=" * 80)

        best_cfg_d1 = best_configs[0]
        print(
            f"\nBest config: R:{best_cfg_d1['r_schedule']}, G:{best_cfg_d1['g_schedule']}, B:{best_cfg_d1['b_schedule']}"
        )
        print(f"Distance on d={d1}: {best_cfg_d1['distance']}")

        visualize_config_minimal_error(
            best_cfg_d1,
            d=d2,
            rounds=rounds,
            p_cnot=p_cnot,
            use_custom_error_model=use_custom_error_model,
            save_prefix=f"best_config_d{d1}",
        )

    # Step 3: Test on d2
    print("\n" + "=" * 80)
    print(f"STEP 3: Testing best d={d1} configs on d={d2}")
    print("-" * 40)

    results_d2 = test_configs_on_d(
        best_configs,
        d=d2,
        rounds=rounds,
        p_cnot=p_cnot,
        method=method_d2,
        use_custom_error_model=use_custom_error_model,
        verbose=True,
    )

    # Save combined results
    save_results(
        results_d2,
        f"best_configs_d{d1}_tested_on_d{d2}.pkl",
        metadata={
            "source_d": d1,
            "tested_d": d2,
            "rounds": rounds,
            "p_cnot": p_cnot,
            "custom_error_model": use_custom_error_model,
        },
    )

    # Print summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nConfigs tested: {len(results_d2)}")

    # Sort by d2 distance
    distance_key_d2 = f"distance_d{d2}"
    results_d2_sorted = sorted(
        results_d2, key=lambda x: x.get(distance_key_d2, 0), reverse=True
    )

    print(f"\nTop configs (sorted by d={d2} distance):")
    for i, cfg in enumerate(results_d2_sorted[:10], 1):
        print(
            f"\n{i}. R:{cfg['r_schedule']}, G:{cfg['g_schedule']}, B:{cfg['b_schedule']}"
        )
        print(
            f"   d={d1} distance: {cfg['distance']}, d={d2} distance: {cfg.get(distance_key_d2, 'N/A')}"
        )


if __name__ == "__main__":
    main()
