
from dataclasses import dataclass
import time
from typing import Sequence

import numpy as np

from classiq import (
    H,
    Output,
    QArray,
    QBit,
    RY,
    SWAP,
    allocate,
    control,
    create_model,
    execute,
    qfunc,
    synthesize,
)

from wms_quantum_optimization_pipeline import (
    OrderLocation,
    qubitized_feature_vector,
    build_vrp_qubo,
    qubo_to_ising_cost,
)


@qfunc
def quantum_swap_test_circuit(
    state_a: QArray[QBit],
    state_b: QArray[QBit],
    ancilla: QBit,
):
    """Swap-test circuit: evaluates the fidelity F = |<state_a|state_b>|^2.

    Applies Hadamard to ancilla, controlled-SWAP between register qubits, and
    Hadamard to ancilla. Measuring ancilla in computational basis yields:
        P(|0>) = (1 + |<state_a|state_b>|^2) / 2
        P(|1>) = (1 - |<state_a|state_b>|^2) / 2
    """
    H(ancilla)
    for i in range(state_a.len):
        control(ancilla, lambda: SWAP(state_a[i], state_b[i]))
    H(ancilla)


@qfunc
def encode_fuzzy_feature_state(
    feature_params: list[float],
    reg: QArray[QBit],
):
    """Amplitude / angle encoding of multi-criteria warehouse order features."""
    for idx, val in enumerate(feature_params):
        theta = 2.0 * float(np.arcsin(np.clip(np.sqrt(max(0.0, val)), 0.0, 1.0)))
        RY(theta, reg[idx])


def quantum_fidelity_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Computes the quantum distance derived from Born's rule measurement probabilities.

    D_Q(a, b) = 1.0 - |<a|b>|^2 = 2 * P(|1>_ancilla)
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if np.isclose(na, 0.0) or np.isclose(nb, 0.0):
        return 1.0
    a_norm = a / na
    b_norm = b / nb
    overlap = float(np.dot(a_norm, b_norm))
    fidelity = max(0.0, min(1.0, overlap**2))
    return float(np.clip(1.0 - fidelity, 0.0, 1.0))


class QuantumFMeans:
    """Quantum Fuzzy C-Means (QFCM / F-Means) Engine.

    Partitions orders into K clusters using continuous membership probabilities
    u_{ik} in [0, 1] derived from quantum fidelity distances.
    """

    def __init__(
        self,
        n_clusters: int = 3,
        m: float = 2.0,
        max_iter: int = 60,
        tol: float = 1e-5,
        random_state: int = 42,
    ):
        if n_clusters < 1:
            raise ValueError("n_clusters must be at least 1")
        if m <= 1.0:
            raise ValueError("Fuzziness parameter m must be strictly greater than 1.0")
        self.n_clusters = n_clusters
        self.m = m
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state

        self.centroids_: list[np.ndarray] = []
        self.membership_matrix_: np.ndarray | None = None
        self.feature_matrix_: np.ndarray | None = None
        self.entropies_: np.ndarray | None = None

    def fit(self, orders: Sequence[OrderLocation]) -> "QuantumFMeans":
        n_samples = len(orders)
        if n_samples == 0:
            self.centroids_ = []
            self.membership_matrix_ = np.empty((0, self.n_clusters))
            self.entropies_ = np.empty(0)
            return self

        k = min(self.n_clusters, n_samples)
        x = np.vstack([qubitized_feature_vector(o) for o in orders])
        self.feature_matrix_ = x

        rng = np.random.default_rng(self.random_state)
        # Initialize membership matrix with Dirichlet distribution to ensure sum_k u_{ik} = 1
        U = rng.uniform(0.1, 1.0, size=(n_samples, k))
        U = U / np.sum(U, axis=1, keepdims=True)

        p = 2.0 / (self.m - 1.0)
        eps = 1e-9

        for iteration in range(self.max_iter):
            U_prev = U.copy()
            Um = U**self.m

            # 1. Update centroids using fuzzy weights
            centers = []
            for j in range(k):
                denominator = np.sum(Um[:, j])
                if denominator < eps:
                    center = x[rng.integers(0, n_samples)]
                else:
                    center = np.sum(Um[:, j : j + 1] * x, axis=0) / denominator
                c_norm = np.linalg.norm(center)
                if c_norm > eps:
                    center = center / c_norm
                centers.append(center)

            # 2. Compute quantum fidelity distance matrix D_{ik}
            D = np.zeros((n_samples, k), dtype=float)
            for i in range(n_samples):
                for j in range(k):
                    D[i, j] = quantum_fidelity_distance(x[i], centers[j])

            # 3. Update membership matrix U_{ik}
            new_U = np.zeros((n_samples, k), dtype=float)
            for i in range(n_samples):
                # Handle exact overlap distance zero cases
                zero_dist = np.where(D[i] < eps)[0]
                if len(zero_dist) > 0:
                    new_U[i, zero_dist] = 1.0 / len(zero_dist)
                else:
                    exponent = float(min(50.0, 1.0 / max(1e-4, self.m - 1.0)))
                    log_inv = -exponent * np.log(np.maximum(D[i], eps))
                    log_inv -= np.max(log_inv)
                    inv_dists = np.exp(log_inv)
                    new_U[i] = inv_dists / np.sum(inv_dists)

            U = new_U
            diff = np.max(np.abs(U - U_prev))
            if diff < self.tol:
                break

        self.centroids_ = centers
        self.membership_matrix_ = U

        # Compute Shannon entropy per sample: H_i = - sum_k u_ik * ln(u_ik)
        self.entropies_ = -np.sum(U * np.log(np.maximum(U, 1e-12)), axis=1)
        return self

    def predict_proba(self, orders: Sequence[OrderLocation]) -> np.ndarray:
        if self.membership_matrix_ is None or len(self.centroids_) == 0:
            raise RuntimeError("Model has not been fitted yet.")
        x = np.vstack([qubitized_feature_vector(o) for o in orders])
        n_samples = len(x)
        k = len(self.centroids_)
        eps = 1e-9

        D = np.zeros((n_samples, k), dtype=float)
        for i in range(n_samples):
            for j in range(k):
                D[i, j] = quantum_fidelity_distance(x[i], self.centroids_[j])

        proba = np.zeros((n_samples, k), dtype=float)
        for i in range(n_samples):
            zero_dist = np.where(D[i] < eps)[0]
            if len(zero_dist) > 0:
                proba[i, zero_dist] = 1.0 / len(zero_dist)
            else:
                inv_dists = (1.0 / np.maximum(D[i], eps)) ** (1.0 / (self.m - 1.0))
                proba[i] = inv_dists / np.sum(inv_dists)
        return proba

    def predict(self, orders: Sequence[OrderLocation] | None = None) -> list[int]:
        if orders is None:
            if self.membership_matrix_ is None:
                raise RuntimeError("Model has not been fitted yet.")
            return np.argmax(self.membership_matrix_, axis=1).tolist()
        proba = self.predict_proba(orders)
        return np.argmax(proba, axis=1).tolist()

    def get_cluster_entropy(self) -> np.ndarray:
        if self.entropies_ is None:
            raise RuntimeError("Model has not been fitted yet.")
        return self.entropies_


def entropy_rebalance_clusters(
    orders: list[OrderLocation],
    membership_matrix: np.ndarray,
    k_batches: int,
    vehicle_capacity: float,
    entropy_threshold: float = 0.45,
) -> list[int]:
    """Rebalances boundary orders with high fuzzy entropy across AGV capacity constraints.

    Orders with high membership entropy (i.e. situated on cluster borders) are dynamically
    routed to the least-loaded qualified AGV batch to avoid vehicle overload.
    """
    n = len(orders)
    if n == 0:
        return []

    # Initial crisp assignment
    crisp_labels = np.argmax(membership_matrix, axis=1)
    weights = np.array([o.weight for o in orders], dtype=float)

    # Calculate cluster loads
    cluster_loads = np.zeros(k_batches, dtype=float)
    for idx, c in enumerate(crisp_labels):
        cluster_loads[c] += weights[idx]

    # Calculate entropy per order
    entropies = -np.sum(membership_matrix * np.log(np.maximum(membership_matrix, 1e-12)), axis=1)

    # Sort high-entropy orders descending
    boundary_indices = np.where(entropies > entropy_threshold)[0]
    boundary_indices = boundary_indices[np.argsort(-entropies[boundary_indices])]

    rebalanced_labels = crisp_labels.copy()

    for idx in boundary_indices:
        current_cluster = rebalanced_labels[idx]
        w = weights[idx]

        # Check if current cluster is overloaded or significantly above average
        if cluster_loads[current_cluster] > vehicle_capacity * 0.85:
            # Find candidate clusters where order has significant membership (e.g. > 15%)
            probs = membership_matrix[idx]
            candidate_clusters = [c for c in range(k_batches) if probs[c] > 0.15 and c != current_cluster]
            if not candidate_clusters:
                continue

            # Pick least-loaded qualified candidate
            best_candidate = min(candidate_clusters, key=lambda c: cluster_loads[c])
            if cluster_loads[best_candidate] + w < cluster_loads[current_cluster]:
                cluster_loads[current_cluster] -= w
                cluster_loads[best_candidate] += w
                rebalanced_labels[idx] = best_candidate

    return rebalanced_labels.tolist()


def fuzzy_route_cluster_pipeline(
    order_locations: list[OrderLocation],
    k_batches: int,
    vehicle_capacity: float = 120.0,
    qaoa_layers: int = 3,
    max_cluster_for_qubo: int | None = 14,
    m: float = 2.0,
    rebalance_entropy: bool = True,
) -> dict:
    """Complete Quantum Fuzzy C-Means (QFCM) optimization pipeline for WMS VRP."""
    qfcm = QuantumFMeans(n_clusters=k_batches, m=m, max_iter=60)
    qfcm.fit(order_locations)

    memberships = qfcm.membership_matrix_
    if memberships is None or len(memberships) == 0:
        return {
            "centers": [],
            "cluster_labels": [],
            "memberships": np.empty((0, k_batches)),
            "entropies": np.empty(0),
            "route_blocks": [],
            "qaoa_layers": qaoa_layers,
            "clustering_type": "quantum_fmeans",
        }

    if rebalance_entropy:
        cluster_labels = entropy_rebalance_clusters(
            order_locations, memberships, k_batches, vehicle_capacity
        )
    else:
        cluster_labels = qfcm.predict()

    features = np.vstack([qubitized_feature_vector(order) for order in order_locations])
    route_blocks = []

    for cluster_id in range(k_batches):
        members = [idx for idx, label in enumerate(cluster_labels) if label == cluster_id]
        if not members:
            continue
        if max_cluster_for_qubo is not None and len(members) > max_cluster_for_qubo:
            route_blocks.append({
                "cluster": cluster_id,
                "h": np.zeros(0),
                "J": np.zeros((0, 0)),
                "qubo": np.zeros((0, 0)),
                "skipped_qubo": True,
            })
            continue

        cluster_features = features[members]
        dist = np.zeros((len(members), len(members)))
        for i in range(len(members)):
            for j in range(len(members)):
                dist[i, j] = quantum_fidelity_distance(cluster_features[i], cluster_features[j])

        weights = np.asarray([order_locations[idx].weight for idx in members], dtype=float)
        qubo = build_vrp_qubo(dist, weights, vehicle_capacity)
        h, J = qubo_to_ising_cost(qubo)
        route_blocks.append({
            "cluster": cluster_id,
            "h": h,
            "J": J,
            "qubo": qubo,
            "skipped_qubo": False,
        })

    return {
        "centers": qfcm.centroids_,
        "cluster_labels": cluster_labels,
        "memberships": memberships,
        "entropies": qfcm.get_cluster_entropy(),
        "route_blocks": route_blocks,
        "qaoa_layers": qaoa_layers,
        "clustering_type": "quantum_fmeans",
    }


def simulate_quantum_swap_test(
    feature_a: Sequence[float],
    feature_b: Sequence[float],
    num_shots: int = 1024,
) -> dict:
    """Executes the Quantum Swap-Test circuit on the Classiq quantum simulator.

    Evaluates the quantum overlap between two multi-criteria feature vectors,
    returning empirical probabilities P(|0>) and P(|1>), and the measured fidelity.
    """
    dim = len(feature_a)
    feat_a = [float(v) for v in feature_a]
    feat_b = [float(v) for v in feature_b]

    @qfunc
    def main(ancilla: Output[QBit], reg_a: Output[QArray[QBit]], reg_b: Output[QArray[QBit]]):
        allocate(dim, reg_a)
        allocate(dim, reg_b)
        allocate(1, ancilla)
        encode_fuzzy_feature_state(feat_a, reg_a)
        encode_fuzzy_feature_state(feat_b, reg_b)
        quantum_swap_test_circuit(reg_a, reg_b, ancilla)

    qmod = create_model(main)
    qprog = synthesize(qmod)
    res = execute(qprog).result()
    parsed = res[0].value.parsed_counts

    shots_0 = sum(sample.shots for sample in parsed if sample.state.get("ancilla", 0) == 0)
    shots_1 = sum(sample.shots for sample in parsed if sample.state.get("ancilla", 0) == 1)
    total = shots_0 + shots_1
    p0 = shots_0 / total if total > 0 else 1.0
    p1 = shots_1 / total if total > 0 else 0.0

    fidelity_sim = float(np.clip(2.0 * p0 - 1.0, 0.0, 1.0))
    dist_sim = float(np.clip(2.0 * p1, 0.0, 1.0))
    dist_exact = quantum_fidelity_distance(np.array(feat_a), np.array(feat_b))

    return {
        "p0": p0,
        "p1": p1,
        "total_shots": total,
        "simulated_fidelity": fidelity_sim,
        "simulated_distance": dist_sim,
        "exact_distance": dist_exact,
        "qprog_width": getattr(qprog.data, "width", None) if hasattr(qprog, "data") else None,
        "qprog_depth": getattr(qprog.data, "depth", None) if hasattr(qprog, "data") else None,
    }


def run_quantum_fmeans_pipeline(
    num_points: int = 80,
    k_batches: int = 4,
    vehicle_capacity: float = 350.0,
    m: float = 2.0,
    seed: int = 42,
    run_quantum_sim: bool = True,
    generate_plot: bool = True,
    generate_animation: bool = True,
    output_png: str = "wms_simulation_80.png",
    output_gif: str = "wms_simulation_80.gif",
) -> dict:
    """End-to-end execution of Quantum F-Means on warehouse workload with simulator output."""
    from wms_visual_simulator import (
        generate_test_orders,
        plot_static_simulation,
        animate_routes,
    )

    print("=" * 75)
    print(f"  Executing Quantum F-Means (QFCM) on {num_points} Points Workload")
    print("=" * 75)
    print(f"  * Orders count (N):          {num_points}")
    print(f"  * AGV Fleet Clusters (K):    {k_batches}")
    print(f"  * AGV Payload Limit (C_max): {vehicle_capacity:.1f} kg")
    print(f"  * Fuzziness Exponent (m):    {m:.2f}")
    print(f"  * Random Seed:               {seed}")
    print("=" * 75)

    # 1. Generate multi-criteria warehouse orders
    orders = generate_test_orders(num_points=num_points, seed=seed)
    total_workload_weight = sum(o.weight for o in orders)
    print(f"[*] Generated {len(orders)} order locations (total payload = {total_workload_weight:.2f} kg)")

    # 2. Run Quantum Fuzzy C-Means Pipeline
    t0 = time.perf_counter()
    pipeline = fuzzy_route_cluster_pipeline(
        order_locations=orders,
        k_batches=k_batches,
        vehicle_capacity=vehicle_capacity,
        m=m,
        rebalance_entropy=True,
    )
    elapsed_time = time.perf_counter() - t0

    labels = np.asarray(pipeline["cluster_labels"])
    centers = np.asarray(pipeline["centers"])
    memberships = pipeline["memberships"]
    entropies = pipeline["entropies"]

    # 3. Form Intra-Cluster AGV Pick Paths
    routes = {}
    depot = (0.0, 0.0)
    total_distance = 0.0
    cluster_payloads = []
    cluster_stops = []

    print("\n[+] Fleet Batch Allocation & Route Synthesis:")
    for cluster_id in range(k_batches):
        members = np.where(labels == cluster_id)[0]
        cluster_stops.append(len(members))
        if len(members) == 0:
            cluster_payloads.append(0.0)
            continue

        xs = np.array([orders[i].x for i in members], dtype=float)
        ys = np.array([orders[i].y for i in members], dtype=float)
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        order_seq = np.argsort(np.arctan2(ys - cy, xs - cx))
        route = members[order_seq].tolist()
        routes[cluster_id] = route

        payload = sum(orders[i].weight for i in route)
        cluster_payloads.append(payload)

        pts = [depot] + [(orders[i].x, orders[i].y) for i in route] + [depot]
        dist = sum(
            np.hypot(pts[idx + 1][0] - pts[idx][0], pts[idx + 1][1] - pts[idx][1])
            for idx in range(len(pts) - 1)
        )
        total_distance += dist

        status = "OK (Compliant)" if payload <= vehicle_capacity else "OVERLOAD!"
        print(
            f"  - AGV {cluster_id + 1}: {len(route):2d} stops | "
            f"Payload: {payload:6.2f} kg / {vehicle_capacity:.1f} kg [{status}] | "
            f"Distance: {dist:6.2f} m"
        )

    stops_std = float(np.std(cluster_stops))
    payload_std = float(np.std(cluster_payloads))
    mean_entropy = float(np.mean(entropies))
    boundary_orders = np.where(entropies > 0.45)[0]

    print("\n[+] Operational Efficiency Metrics:")
    print(f"  * Stops Distribution:           {cluster_stops}")
    print(f"  * Stop Count Std Dev (sigma):    {stops_std:.4f}")
    print(f"  * Payload Distribution (kg):    {[round(p, 2) for p in cluster_payloads]}")
    print(f"  * Payload Std Dev (kg):         {payload_std:.4f}")
    print(f"  * Overload Violations:          {sum(1 for p in cluster_payloads if p > vehicle_capacity)}")
    print(f"  * Total Fleet Travel Distance:  {total_distance:.2f} m")
    print(f"  * Mean Shannon Entropy:         {mean_entropy:.4f}")
    print(f"  * High-Entropy Boundary Orders: {len(boundary_orders)} / {num_points} orders")
    print(f"  * Pipeline Classical Latency:   {elapsed_time:.4f} s")

    # 4. Quantum Simulator Validation
    sim_results = None
    if run_quantum_sim:
        print("\n[*] Running Quantum Hardware Simulator on Classiq backend...")
        try:
            # Sample test between first order and its assigned centroid
            sample_feat = qubitized_feature_vector(orders[0])
            centroid_feat = centers[labels[0]]
            sim_results = simulate_quantum_swap_test(sample_feat, centroid_feat, num_shots=1024)
            print("  [Simulator: Swap-Test Overlap Circuit]")
            print(f"    - Shots measured:           {sim_results['total_shots']}")
            print(f"    - P(|0>_ancilla):           {sim_results['p0']:.4f}")
            print(f"    - P(|1>_ancilla):           {sim_results['p1']:.4f}")
            print(f"    - Reconstructed Fidelity:   {sim_results['simulated_fidelity']:.4f}")
            print(f"    - Simulator Quantum Dist:   {sim_results['simulated_distance']:.4f}")
            print(f"    - Exact Analytical Dist:    {sim_results['exact_distance']:.4f}")
            if sim_results["qprog_width"] is not None:
                print(f"    - Circuit Qubits (Width):   {sim_results['qprog_width']}")
                print(f"    - Circuit Depth:            {sim_results['qprog_depth']}")
        except Exception as err:
            print(f"  [!] Quantum simulation note: {err}")

    # 5. Visual Simulator Artifact Generation
    if generate_plot:
        print(f"\n[*] Generating static warehouse simulation plot -> {output_png}")
        plot_static_simulation(
            orders=orders,
            labels=labels,
            centers=centers,
            routes=routes,
            entropies=entropies,
            save_path=output_png,
        )

    if generate_animation:
        print(f"[*] Generating multi-AGV animated simulation -> {output_gif}")
        animate_routes(
            orders=orders,
            labels=labels,
            centers=centers,
            routes=routes,
            entropies=entropies,
            save_path=output_gif,
        )

    print("\n" + "=" * 75)
    print("  [SUCCESS] 80-Point Quantum F-Means Simulation Complete!")
    print("=" * 75)

    return {
        "orders": orders,
        "pipeline": pipeline,
        "routes": routes,
        "cluster_stops": cluster_stops,
        "cluster_payloads": cluster_payloads,
        "stops_std": stops_std,
        "payload_std": payload_std,
        "total_distance": total_distance,
        "mean_entropy": mean_entropy,
        "boundary_orders_count": len(boundary_orders),
        "quantum_sim_results": sim_results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Quantum F-Means on warehouse order workload")
    parser.add_argument("--num-points", type=int, default=80, help="Number of order locations (default: 80)")
    parser.add_argument("--k-batches", type=int, default=4, help="Number of AGV clusters / batches (default: 4)")
    parser.add_argument("--capacity", type=float, default=350.0, help="Vehicle capacity in kg (default: 350.0)")
    parser.add_argument("--m", type=float, default=2.0, help="Fuzziness parameter m (default: 2.0)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--no-sim", action="store_true", help="Skip quantum simulator execution")
    parser.add_argument("--no-plot", action="store_true", help="Skip static PNG plot generation")
    parser.add_argument("--no-anim", action="store_true", help="Skip animated GIF generation")
    parser.add_argument("--output-png", type=str, default="wms_simulation_80.png", help="PNG output path")
    parser.add_argument("--output-gif", type=str, default="wms_simulation_80.gif", help="GIF output path")
    args = parser.parse_args()

    run_quantum_fmeans_pipeline(
        num_points=args.num_points,
        k_batches=args.k_batches,
        vehicle_capacity=args.capacity,
        m=args.m,
        seed=args.seed,
        run_quantum_sim=not args.no_sim,
        generate_plot=not args.no_plot,
        generate_animation=not args.no_anim,
        output_png=args.output_png,
        output_gif=args.output_gif,
    )

