"""
Generate all zero-collision schedules from the optimal distance-6 schedules.

Applies three distance-preserving transformations:
1. Swap values 1 <-> 2
2. Swap values 5 <-> 6
3. Time reversal: 1<->6, 2<->5, 3<->4

Saves all 864 unique zero-collision schedules to a CSV file.
"""

import pickle
import csv
from color_code_stim import ColorCode


def generate_8_variations(schedule):
    """
    Generate 8 variations of a schedule by applying distance-preserving transformations.

    Transformations:
    1. Swap values 1 and 2
    2. Swap values 5 and 6
    3. Time reversal: 1<->6, 2<->5, 3<->4
    """
    s = list(schedule)
    variations = []

    for do_reverse in [False, True]:
        for swap_12 in [False, True]:
            for swap_56 in [False, True]:
                v = s[:]

                # Time reversal: 1<->6, 2<->5, 3<->4
                if do_reverse:
                    v = [7 - x for x in v]

                # Swap values 1 and 2
                if swap_12:
                    v = [2 if x == 1 else (1 if x == 2 else x) for x in v]

                # Swap values 5 and 6
                if swap_56:
                    v = [6 if x == 5 else (5 if x == 6 else x) for x in v]

                variations.append(tuple(v))

    return variations


def setup_collision_detection(d=7):
    """Set up data structures for collision detection."""
    colorcode = ColorCode(d=d, rounds=1, cnot_schedule="tri_optimal", p_cnot=0)

    # Canonical order of data qubits around a plaquette (clockwise from upper-left)
    CANONICAL_OFFSETS = [(-2, 1), (2, 1), (4, 0), (2, -1), (-2, -1), (-4, 0)]

    data_qubits = colorcode.qubit_groups["data"]
    z_ancillas = colorcode.qubit_groups["anc_Z"]

    data_by_pos = {(dq["x"], dq["y"]): dq["qid"] for dq in data_qubits}
    z_anc_info = {
        anc["qid"]: {
            "x": anc["x"],
            "y": anc["y"],
            "color": anc["color"],
            "boundary": anc["boundary"],
        }
        for anc in z_ancillas
    }

    def get_data_qubits_canonical_order(anc_qid):
        info = z_anc_info[anc_qid]
        return [
            data_by_pos.get((info["x"] + dx, info["y"] + dy))
            for dx, dy in CANONICAL_OFFSETS
            if (info["x"] + dx, info["y"] + dy) in data_by_pos
        ]

    z_anc_to_data = {
        anc["qid"]: get_data_qubits_canonical_order(anc["qid"]) for anc in z_ancillas
    }
    bulk_anc_list = [anc["qid"] for anc in z_ancillas if anc["boundary"] is None]

    return z_anc_info, z_anc_to_data, bulk_anc_list


def count_collisions(
    r_schedule, g_schedule, b_schedule, z_anc_info, z_anc_to_data, bulk_anc_list
):
    """
    Count the number of collisions (same data qubit accessed at same time step by different plaquettes).
    Only considers bulk plaquettes.
    """
    schedules = {"r": r_schedule, "g": g_schedule, "b": b_schedule}

    # Track which ancillas access each data qubit at each time step
    collisions = {ts: {} for ts in range(1, 7)}

    for anc_qid in bulk_anc_list:
        info = z_anc_info[anc_qid]
        data_list = z_anc_to_data[anc_qid]
        schedule = schedules[info["color"]]

        for pos_idx, dq_qid in enumerate(data_list):
            if pos_idx < len(schedule):
                ts = schedule[pos_idx]
                if dq_qid not in collisions[ts]:
                    collisions[ts][dq_qid] = []
                collisions[ts][dq_qid].append(anc_qid)

    # Count collisions (data qubits accessed by multiple ancillas at same time step)
    return sum(
        1 for ts_dict in collisions.values() for dqs in ts_dict.values() if len(dqs) > 1
    )


def generate_zero_collision_schedules(results_file="search_results_d7.pkl", d=7):
    """
    Generate all zero-collision schedules from optimal configurations.

    Args:
        results_file: Path to the pickle file with exhaustive search results
        d: Code distance (for collision detection)

    Returns:
        List of dicts with schedule information
    """
    # Load optimal schedules
    with open(results_file, "rb") as f:
        data = pickle.load(f)

    results = data.get("results") or data.get("all_results")
    max_dist = max(r["distance"] for r in results)
    optimal_configs = [r for r in results if r["distance"] == max_dist]

    print(
        f"Loaded {len(optimal_configs)} optimal configurations with distance {max_dist}"
    )

    # Setup collision detection
    z_anc_info, z_anc_to_data, bulk_anc_list = setup_collision_detection(d)

    # Find all zero-collision schedules
    zero_collision_schedules = []
    unique_modified = set()

    for orig_idx, orig_cfg in enumerate(optimal_configs):
        orig_r = tuple(orig_cfg["r_schedule"])
        orig_g = tuple(orig_cfg["g_schedule"])
        orig_b = tuple(orig_cfg["b_schedule"])

        r_vars = generate_8_variations(orig_r)
        g_vars = generate_8_variations(orig_g)
        b_vars = generate_8_variations(orig_b)

        for mod_r in r_vars:
            for mod_g in g_vars:
                for mod_b in b_vars:
                    num_collisions = count_collisions(
                        mod_r, mod_g, mod_b, z_anc_info, z_anc_to_data, bulk_anc_list
                    )

                    if num_collisions == 0:
                        key = (mod_r, mod_g, mod_b)
                        if key not in unique_modified:
                            unique_modified.add(key)
                            zero_collision_schedules.append(
                                {
                                    "orig_config_idx": orig_idx,
                                    "orig_r_schedule": list(orig_r),
                                    "orig_g_schedule": list(orig_g),
                                    "orig_b_schedule": list(orig_b),
                                    "r_schedule": list(mod_r),
                                    "g_schedule": list(mod_g),
                                    "b_schedule": list(mod_b),
                                    "circuit_distance": max_dist,
                                    "collisions": 0,
                                }
                            )

    print(f"Found {len(zero_collision_schedules)} unique zero-collision schedules")
    return zero_collision_schedules


def save_to_csv(schedules, output_file="zero_collision_schedules.csv"):
    """Save schedules to a CSV file."""
    if not schedules:
        print("No schedules to save")
        return

    fieldnames = [
        "index",
        "r_schedule",
        "g_schedule",
        "b_schedule",
        "orig_r_schedule",
        "orig_g_schedule",
        "orig_b_schedule",
        "orig_config_idx",
        "circuit_distance",
        "collisions",
    ]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, sched in enumerate(schedules):
            row = {
                "index": i + 1,
                "r_schedule": str(sched["r_schedule"]),
                "g_schedule": str(sched["g_schedule"]),
                "b_schedule": str(sched["b_schedule"]),
                "orig_r_schedule": str(sched["orig_r_schedule"]),
                "orig_g_schedule": str(sched["orig_g_schedule"]),
                "orig_b_schedule": str(sched["orig_b_schedule"]),
                "orig_config_idx": sched["orig_config_idx"],
                "circuit_distance": sched["circuit_distance"],
                "collisions": sched["collisions"],
            }
            writer.writerow(row)

    print(f"Saved {len(schedules)} schedules to {output_file}")


def main():
    import os

    print("=" * 80)
    print("GENERATING ZERO-COLLISION SCHEDULES")
    print("=" * 80)
    print()

    # Generate schedules
    schedules = generate_zero_collision_schedules(
        results_file="search_results_d7.pkl", d=7
    )

    # Save to CSV
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "zero_collision_schedules.csv")

    save_to_csv(schedules, output_file)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total zero-collision schedules: {len(schedules)}")
    print(
        f"Circuit-level distance: {schedules[0]['circuit_distance'] if schedules else 'N/A'}"
    )
    print(f"Output file: {output_file}")

    # Print first few schedules as examples
    print("\nFirst 5 schedules:")
    for i, sched in enumerate(schedules[:5]):
        print(
            f"  {i+1}. R={sched['r_schedule']}, G={sched['g_schedule']}, B={sched['b_schedule']}"
        )


if __name__ == "__main__":
    main()
