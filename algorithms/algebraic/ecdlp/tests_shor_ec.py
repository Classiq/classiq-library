from tests_ec_point_add import (
    GLOBAL_G,
    GLOBAL_INITIAL_ECP,
    GLOBAL_TARGET_ECP,
    GLOBAL_CURVE,
)
from tinyec.ec import SubGroup, Curve, Point
import re
import ast
from collections import defaultdict
import numpy as np
from shor_ec import run_shor_quantum

# Paste your raw quantum results here as a string
raw_data = """
[{'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 4, 'x2': 0}: 45, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 6, 'x2': 0}: 45, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 6, 'x2': 3}: 45, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 4, 'x2': 1}: 44, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 1, 'x2': 2}: 43, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 2, 'x2': 2}: 43, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 4, 'x2': 3}: 43, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 2, 'x2': 3}: 43, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 1, 'x2': 0}: 41, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 5, 'x2': 7}: 41, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 6, 'x2': 7}: 40, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 0, 'x2': 7}: 39, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 3, 'x2': 2}: 38, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 1, 'x2': 3}: 38, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 2, 'x2': 7}: 38, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 1, 'x2': 7}: 37, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 4, 'x2': 5}: 36, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 0, 'x2': 3}: 36, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 0, 'x2': 5}: 35, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 3, 'x2': 3}: 34, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 5, 'x2': 2}: 34, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 7, 'x2': 2}: 34, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 2, 'x2': 5}: 34, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 6, 'x2': 6}: 33, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 7, 'x2': 4}: 33, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 7, 'x2': 3}: 33, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 2, 'x2': 4}: 33, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 7, 'x2': 5}: 32, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 6, 'x2': 2}: 32, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 2, 'x2': 0}: 32, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 5, 'x2': 0}: 31, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 0, 'x2': 6}: 31, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 6, 'x2': 4}: 31, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 3, 'x2': 6}: 30, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 4, 'x2': 6}: 30, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 6, 'x2': 5}: 30, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 3, 'x2': 5}: 30, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 5, 'x2': 3}: 30, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 0, 'x2': 1}: 30, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 3, 'x2': 7}: 30, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 5, 'x2': 4}: 29, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 1, 'x2': 6}: 29, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 6, 'x2': 1}: 29, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 1, 'x2': 1}: 29, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 4, 'x2': 2}: 28, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 1, 'x2': 5}: 28, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 5, 'x2': 6}: 27, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 3, 'x2': 0}: 27, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 7, 'x2': 1}: 27, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 2, 'x2': 6}: 26, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 7, 'x2': 0}: 26, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 4, 'x2': 4}: 26, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 3, 'x2': 1}: 26, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 2, 'x2': 1}: 25, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 3, 'x2': 4}: 25, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 4, 'x2': 7}: 25, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 0, 'x2': 4}: 25, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 1, 'x2': 4}: 24, {'ecp_x': 3, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 0, 'x2': 2}: 24, {'ecp_x': 3, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 7, 'x2': 7}: 24, {'ecp_x': 4, 'ecp_y': 5, 't0': 0, 'l': 0, 'x1': 5, 'x2': 1}: 22, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 5, 'x2': 5}: 21, {'ecp_x': 5, 'ecp_y': 0, 't0': 0, 'l': 0, 'x1': 7, 'x2': 6}: 20, {'ecp_x': 4, 'ecp_y': 2, 't0': 0, 'l': 0, 'x1': 0, 'x2': 0}: 19]
"""

pattern = r"(\{[^\}]+\}): (\d+)"
matches = re.findall(pattern, raw_data)

quantum_results = []
for dict_str, count in matches:
    d = ast.literal_eval(dict_str)
    d["count"] = int(count)
    quantum_results.append(d)

# Build a lookup for the most frequent (ecp_x, ecp_y) for each (k1, k2)
lookup = defaultdict(list)
for res in quantum_results:
    k1 = res["x1"]
    k2 = res["x2"]
    xy = (res["ecp_x"], res["ecp_y"])
    count = res["count"]
    lookup[(k1, k2)].append((xy, count))

quantum_lookup = {}
for key, values in lookup.items():
    most_frequent = max(values, key=lambda x: x[1])[0]
    quantum_lookup[key] = most_frequent


def compare_quantum_vs_classical(quantum_lookup, test_name=""):
    """
    Compare quantum results with classical elliptic curve calculations.
    Returns (matches, mismatches) counts.
    """
    print(f"\n--- Running {test_name} ---")
    field = SubGroup(p=GLOBAL_CURVE.p, g=(GLOBAL_G[0], GLOBAL_G[1]), n=10, h=None)
    curve = Curve(a=GLOBAL_CURVE.a, b=GLOBAL_CURVE.b, field=field, name="custom")
    initial_ecp_tinyec = Point(curve, GLOBAL_INITIAL_ECP[0], GLOBAL_INITIAL_ECP[1])
    target_ecp_tinyec = Point(curve, GLOBAL_TARGET_ECP[0], GLOBAL_TARGET_ECP[1])
    G_tinyec = Point(curve, GLOBAL_G[0], GLOBAL_G[1])

    matches = 0
    mismatches = 0
    for k1 in range(8):
        for k2 in range(8):
            try:
                temp = initial_ecp_tinyec + k1 * G_tinyec - k2 * target_ecp_tinyec
                classical_result = (temp.x, temp.y)
            except Exception as e:
                classical_result = f"Undefined: {e}"
            quantum_result = quantum_lookup.get((k1, k2), None)
            print(
                f"k1={k1}, k2={k2} | Quantum: {quantum_result} | Classical: {classical_result}"
            )
            if quantum_result is not None and isinstance(classical_result, tuple):
                if quantum_result == classical_result:
                    matches += 1
                else:
                    mismatches += 1
    print(f"\nSummary: {matches} matches, {mismatches} mismatches (out of 64 pairs)")
    return matches, mismatches


def test_shor_no_qft_parsed_quantum():
    # Use the shared comparison function
    compare_quantum_vs_classical(
        quantum_lookup, "test_shor_no_qft_parsed_quantum (parsed quantum vs classical)"
    )


def apply_qft_classically(raw_data, num_bits=3):
    print(
        "\n--- Running apply_qft_classically (parsing and QFT-inverse transformation) ---"
    )
    """
    Parse the raw quantum results and apply the inverse QFT logic classically to x1 and x2.
    Returns a list of (x1_inv, x2_inv, probability) tuples (post-QFT-inverse).
    """
    pattern = r"(\{[^\}]+\}): (\d+)"
    matches = re.findall(pattern, raw_data)
    results = []
    total_counts = 0
    for dict_str, count in matches:
        d = ast.literal_eval(dict_str)
        d["count"] = int(count)
        results.append(d)
        total_counts += int(count)

    def inverse_qft(val, n):
        b = format(val, f"0{n}b")
        return int(b[::-1], 2)

    print("Original (x1, x2) | After inverse QFT (x1, x2) | Probability")
    post_qft_pairs = []
    for res in results:
        x1 = res["x1"]
        x2 = res["x2"]
        x1_inv = inverse_qft(x1, num_bits)
        x2_inv = inverse_qft(x2, num_bits)
        count = res["count"]
        prob = count / total_counts
        print(f"({x1}, {x2}) | ({x1_inv}, {x2_inv}) | Probability: {prob:.4f}")
        post_qft_pairs.append((x1_inv, x2_inv, prob))
    return post_qft_pairs


def solve_ecdlp_from_qft_inverse(post_qft_pairs, curve, G, initial_ecp, target_ecp):
    solutions = []
    for k1, k2, prob in post_qft_pairs:
        try:
            lhs = initial_ecp + k1 * G - k2 * target_ecp
            if lhs.x is None and lhs.y is None:
                solutions.append((k1, k2, prob))
        except Exception:
            continue
    print(
        "\nECDLP solutions (k1, k2, probability) where initial_ecp + k1*G - k2*target_ecp = O:"
    )
    for sol in solutions:
        print(sol)
    return solutions


def retrieve_discrete_log_from_qft(post_qft_pairs, r):
    solutions = set()
    for y1, y2, prob in post_qft_pairs:
        if y1 == 0:
            continue
        try:
            y1_inv = pow(y1, -1, r)
            l = (-y2 * y1_inv) % r
            solutions.add(l)
        except ValueError:
            continue
    print("\nPossible discrete log values l = -y2 * y1^{-1} mod r:")
    for l in solutions:
        print(l)
    return solutions


def test_shor_no_qft():
    quantum_results_raw = run_shor_quantum()
    print("Quantum results type:", type(quantum_results_raw))
    print("Quantum results:", quantum_results_raw)

    # Convert the live quantum results to string format for parsing (same as in test_shor_no_qft_parsed_quantum)
    raw_data = str(quantum_results_raw)

    # Use the same parsing logic as test_shor_no_qft_parsed_quantum
    pattern = r"(\{[^\}]+\}): (\d+)"
    matches = re.findall(pattern, raw_data)

    quantum_results = []
    for dict_str, count in matches:
        d = ast.literal_eval(dict_str)
        d["count"] = int(count)
        quantum_results.append(d)

    # Build a lookup for the most frequent (ecp_x, ecp_y) for each (k1, k2)
    lookup = defaultdict(list)
    for res in quantum_results:
        k1 = res["x1"]
        k2 = res["x2"]
        xy = (res["ecp_x"], res["ecp_y"])
        count = res["count"]
        lookup[(k1, k2)].append((xy, count))

    quantum_lookup_live = {}
    for key, values in lookup.items():
        most_frequent = max(values, key=lambda x: x[1])[0]
        quantum_lookup_live[key] = most_frequent

    # Use the shared comparison function
    compare_quantum_vs_classical(
        quantum_lookup_live, "test_shor_no_qft (live quantum vs classical)"
    )


if __name__ == "__main__":
    test_shor_no_qft_parsed_quantum()
    test_shor_no_qft()

    """
    post_qft_pairs = apply_qft_classically(raw_data)
    # Setup curve and points as in previous tests
    field = SubGroup(p=GLOBAL_CURVE.p, g=(GLOBAL_G[0], GLOBAL_G[1]), n=10, h=None)
    curve = Curve(a=GLOBAL_CURVE.a, b=GLOBAL_CURVE.b, field=field, name="custom")
    initial_ecp_tinyec = Point(curve, GLOBAL_INITIAL_ECP[0], GLOBAL_INITIAL_ECP[1])
    target_ecp_tinyec = Point(curve, GLOBAL_TARGET_ECP[0], GLOBAL_TARGET_ECP[1])
    G_tinyec = Point(curve, GLOBAL_G[0], GLOBAL_G[1])
    solve_ecdlp_from_qft_inverse(post_qft_pairs, curve, G_tinyec, initial_ecp_tinyec, target_ecp_tinyec)
    retrieve_discrete_log_from_qft(post_qft_pairs, r=5)
    """
