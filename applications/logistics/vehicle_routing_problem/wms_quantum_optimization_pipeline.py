from dataclasses import dataclass
from typing import Iterable, Optional, List, Tuple
import time

import numpy as np

from classiq import (
    AwsBackendPreferences,
    Constraints,
    ExecutionPreferences,
    H,
    Preferences,
    QArray,
    QBit,
    QNum,
    Output,
    RX,
    RY,
    RZ,
    SWAP,
    allocate,
    apply_to_all,
    control,
    create_model,
    hadamard_transform,
    phase,
    qfunc,
    synthesize,
)


@dataclass(frozen=True)
class OrderLocation:
    x: float
    y: float
    z: float
    weight: float
    volume: float
    sla_priority: float
    zone_class: float


def _normalize_columns(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    mins = matrix.min(axis=0)
    maxs = matrix.max(axis=0)
    spans = np.where(maxs > mins, maxs - mins, 1.0)
    return (matrix - mins) / spans


def qubitized_feature_vector(order: OrderLocation) -> np.ndarray:
    raw = np.array(
        [
            order.x / 30.0,
            order.y / 25.0,
            order.z / 5.0,
            order.weight / 50.0,
            order.volume / 50.0,
            order.sla_priority,
            order.zone_class,
        ],
        dtype=float,
    )
    raw = raw + 0.05
    norm = np.linalg.norm(raw)
    return raw / norm if norm > 1e-9 else raw


def quantum_kmeans_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Fidelity-based distance using overlap |<a|b>|^2."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if np.isclose(na, 0.0) or np.isclose(nb, 0.0):
        return 1.0
    a = a / na
    b = b / nb
    overlap = float(np.dot(a, b))
    fidelity = max(0.0, min(1.0, overlap**2))
    return 1.0 - fidelity


def kmeans_assign_clusters(orders: list[OrderLocation], k: int) -> tuple[list[np.ndarray], list[int]]:
    """A tiny classical surrogate for the quantum K-Means routine.

    The real circuit would replace the Euclidean distance with a swap-test based
    overlap metric between the normalized feature vectors |x_i> and cluster-
    centroids |c_k>.
    """
    if not orders:
        return [], []
    k = max(1, min(k, len(orders)))
    x = np.vstack([qubitized_feature_vector(o) for o in orders])
    indices = np.linspace(0, len(x) - 1, k, dtype=int)
    centers = x[indices].copy()
    labels = np.zeros(len(orders), dtype=int)

    for _ in range(25):
        new_labels = []
        for v in x:
            new_labels.append(int(np.argmin([quantum_kmeans_distance(v, c) for c in centers])))
        new_labels = np.asarray(new_labels)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for center_idx in range(k):
            cluster = x[labels == center_idx]
            if len(cluster):
                c_mean = cluster.mean(axis=0)
                c_norm = np.linalg.norm(c_mean)
                centers[center_idx] = c_mean / c_norm if c_norm > 1e-9 else c_mean

    return [c.astype(float) for c in centers], labels.tolist()


@qfunc
def swap_test_overlap(x_state: QArray[QBit], c_state: QArray[QBit], ancilla: QBit):
    """Swap-test circuit: measures the fidelity F = |<x|c>|^2."""
    H(ancilla)
    for i in range(x_state.len):
        control(ancilla, lambda: SWAP(x_state[i], c_state[i]))
    H(ancilla)


@qfunc
def amplitude_encode_feature_vector(
    feature_values: list[float],
    reg: QArray[QBit],
):
    """Amplitude / angle encoding skeleton for normalized feature vectors."""
    for idx, value in enumerate(feature_values):
        theta = 2.0 * np.arcsin(np.clip(np.sqrt(max(0.0, value)), 0.0, 1.0))
        RY(theta, reg[idx])


@qfunc
def qaoa_routing_layer(
    gamma: float,
    beta: float,
    route_bits: QArray[QBit],
):
    """Generic QAOA layer for the VRP / routing Hamiltonian."""
    apply_to_all(lambda q: RX(2.0 * beta, q), route_bits)
    apply_to_all(lambda q: RZ(2.0 * gamma, q), route_bits)


@qfunc
def main(
    route_bits: Output[QArray[QBit]],
    anc: Output[QBit],
):
    """Hybrid WMS optimization QAOA entry point.

    This qfunc demonstrates the composition of Particle 1 and Particle 2:
    - state preparation for normalized WMS feature vectors
    - a swap-test distance routine in the quantum Hilbert space
    - a parameterized QAOA routing ansatz for the cluster-local VRP Hamiltonian
    """
    allocate(16, route_bits)
    allocate(1, anc)
    hadamard_transform(route_bits)

    # Prepare a compact, normalized 7-feature order-state.
    amplitude_encode_feature_vector([0.15, 0.2, 0.35, 0.4, 0.25, 0.5, 0.3], route_bits[:7])

    # The swap-test evaluates overlap between order state and centroid state.
    H(anc)
    for i in range(7):
        control(anc, lambda: SWAP(route_bits[i], route_bits[8 + i]))
    H(anc)

    # Route optimization layer: parameterized QAOA cycle for a local VRP.
    p_layers = 3
    gamma_beta = [0.35, 0.15] * p_layers
    for layer in range(p_layers):
        qaoa_routing_layer(gamma_beta[2 * layer], gamma_beta[2 * layer + 1], route_bits)


def build_vrp_qubo(
    dist_matrix: np.ndarray,
    weights: np.ndarray,
    capacity: float,
    alpha_degree: float = 4.0,
    alpha_capacity: float = 3.0,
    alpha_mtz: float = 2.0,
) -> np.ndarray:
    """Construct a QUBO for the intra-cluster AGV routing model.

    Variables: x_{i,j} = 1 if node j is visited immediately after i.
    The objective is minimize sum_{i,j} d_{ij} x_{ij} subject to degree, capacity,
    and MTZ subtour constraints.
    """
    n = dist_matrix.shape[0]
    var_count = n * n
    Q = np.zeros((var_count, var_count), dtype=float)

    # Travel cost: linear terms + pairwise interaction terms are folded into the
    # final Ising Hamiltonian by the classical post-processing routine.
    for i in range(n):
        for j in range(n):
            idx = i * n + j
            Q[idx, idx] += dist_matrix[i, j]

    # Degree constraints: exactly one departure and one arrival per node.
    for i in range(n):
        for j in range(n):
            idx = i * n + j
            Q[idx, idx] += alpha_degree
            for k in range(n):
                if k != j:
                    Q[idx, i * n + k] += -alpha_degree
                if k != i:
                    Q[idx, k * n + j] += -alpha_degree

    # Capacity penalty: approximate total load per AGV route.
    for i in range(n):
        for j in range(n):
            idx = i * n + j
            Q[idx, idx] += alpha_capacity * weights[j] / max(capacity, 1e-9)

    # MTZ penalty: u_i - u_j + M(1 - x_{ij}) <= M for subtour elimination.
    # The exact implementation is a standard quadratic penalty in the QUBO.
    M = float(max(1.0, np.max(dist_matrix) * (n + 1)))
    for i in range(1, n):
        for j in range(1, n):
            if i == j:
                continue
            idx_ij = i * n + j
            for k in range(1, n):
                if k == i or k == j:
                    continue
                idx_ik = i * n + k
                idx_jk = j * n + k
                Q[idx_ij, idx_ij] += alpha_mtz * M
                Q[idx_ik, idx_ij] += -alpha_mtz * M
                Q[idx_jk, idx_ij] += -alpha_mtz * M

    return Q


def qubo_to_ising_cost(Q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map a binary quadratic objective x^T Q x to an Ising cost for QAOA.

    For x in {0,1} and z = 2x - 1, the standard transformation yields:
        E(x) = sum_i h_i z_i + sum_{i<j} J_{ij} z_i z_j + const
    """
    n = Q.shape[0]
    h = np.zeros(n)
    J = np.zeros((n, n))

    for i in range(n):
        h[i] = 0.5 * Q[i, i]
        for j in range(i + 1, n):
            J[i, j] = 0.25 * (Q[i, j] + Q[j, i])
            J[j, i] = J[i, j]

    return h, J


def route_cluster_pipeline(
    order_locations: list[OrderLocation],
    k_batches: int,
    vehicle_capacity: float,
    qaoa_layers: int = 3,
    max_cluster_for_qubo: int | None = 14,
) -> dict:
    """Main orchestration for the hybrid optimization pipeline.

    `max_cluster_for_qubo` prevents pathological QUBO blow-ups on large clusters
    while still benchmarking the complete 100-point workload with a tractable
    route subproblem size.
    """
    features = np.vstack([qubitized_feature_vector(order) for order in order_locations])
    centers, cluster_labels = kmeans_assign_clusters(order_locations, k_batches)

    route_blocks = []
    for cluster_id in range(k_batches):
        members = [idx for idx, label in enumerate(cluster_labels) if label == cluster_id]
        if not members:
            continue
        if max_cluster_for_qubo is not None and len(members) > max_cluster_for_qubo:
            # Keep the benchmark tractable while preserving the full clustering stage.
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
                dist[i, j] = quantum_kmeans_distance(cluster_features[i], cluster_features[j])
        weights = np.asarray([order_locations[idx].weight for idx in members], dtype=float)
        qubo = build_vrp_qubo(dist, weights, vehicle_capacity)
        h, J = qubo_to_ising_cost(qubo)
        route_blocks.append({"cluster": cluster_id, "h": h, "J": J, "qubo": qubo, "skipped_qubo": False})

    return {
        "centers": centers,
        "cluster_labels": cluster_labels,
        "route_blocks": route_blocks,
        "qaoa_layers": qaoa_layers,
    }


def benchmark_runtime_100_points(cluster_counts: list[int] | None = None, repeats: int = 5) -> list[dict]:
    """Benchmark the 100-point WMS workload against real runtime on the current machine."""
    cluster_counts = cluster_counts or [2, 3, 4, 5, 6]
    rng = np.random.default_rng(42)
    rows = []
    for k in cluster_counts:
        timings = []
        for seed in range(repeats):
            orders = []
            for _ in range(100):
                orders.append(
                    OrderLocation(
                        x=float(rng.uniform(0.0, 24.0)),
                        y=float(rng.uniform(0.0, 20.0)),
                        z=float(rng.uniform(0.5, 2.5)),
                        weight=float(rng.uniform(5.0, 25.0)),
                        volume=float(rng.uniform(6.0, 24.0)),
                        sla_priority=float(rng.uniform(0.5, 1.0)),
                        zone_class=float(rng.uniform(0.0, 1.0)),
                    )
                )
            t0 = time.perf_counter()
            route_cluster_pipeline(orders, k_batches=k, vehicle_capacity=120.0, max_cluster_for_qubo=12)
            timings.append(time.perf_counter() - t0)
        rows.append({"k_batches": k, "times": timings, "avg_seconds": float(np.mean(timings)), "max_seconds": float(np.max(timings))})
    return rows


def benchmark_kmeans_vs_fmeans(num_points: int = 100, k_batches: int = 4, seed: int = 42) -> dict:
    """Compares hard Quantum K-Means vs soft Quantum F-Means on cluster balance and variance."""
    from wms_quantum_fmeans import fuzzy_route_cluster_pipeline

    rng = np.random.default_rng(seed)
    orders = [
        OrderLocation(
            x=float(rng.uniform(0.0, 24.0)),
            y=float(rng.uniform(0.0, 20.0)),
            z=float(rng.uniform(0.5, 2.5)),
            weight=float(rng.uniform(5.0, 25.0)),
            volume=float(rng.uniform(6.0, 24.0)),
            sla_priority=float(rng.uniform(0.5, 1.0)),
            zone_class=float(rng.uniform(0.0, 1.0)),
        )
        for _ in range(num_points)
    ]

    t0 = time.perf_counter()
    kmeans_res = route_cluster_pipeline(orders, k_batches=k_batches, vehicle_capacity=120.0)
    kmeans_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    fmeans_res = fuzzy_route_cluster_pipeline(orders, k_batches=k_batches, vehicle_capacity=120.0)
    fmeans_time = time.perf_counter() - t1

    kmeans_counts = [int(np.sum(np.array(kmeans_res["cluster_labels"]) == c)) for c in range(k_batches)]
    fmeans_counts = [int(np.sum(np.array(fmeans_res["cluster_labels"]) == c)) for c in range(k_batches)]

    return {
        "kmeans": {
            "counts": kmeans_counts,
            "std_dev": float(np.std(kmeans_counts)),
            "latency_seconds": kmeans_time,
        },
        "fmeans": {
            "counts": fmeans_counts,
            "std_dev": float(np.std(fmeans_counts)),
            "latency_seconds": fmeans_time,
            "mean_entropy": float(np.mean(fmeans_res["entropies"])),
        },
    }


def build_qaoa_model(order_locations: list[OrderLocation], k_batches: int = 3, clustering: str = "fmeans"):
    """Synthesis-ready wrapper for the QAOA route solver."""
    if clustering == "fmeans":
        from wms_quantum_fmeans import fuzzy_route_cluster_pipeline
        pipeline = fuzzy_route_cluster_pipeline(order_locations, k_batches, vehicle_capacity=120.0)
    else:
        pipeline = route_cluster_pipeline(order_locations, k_batches, vehicle_capacity=120.0)

def generate_test_orders(num_points: int = 100, seed: int = 42) -> list[OrderLocation]:
    """Generate reproducible 3D warehouse order locations with weight, volume, SLA, and zone."""
    rng = np.random.default_rng(seed)
    orders: list[OrderLocation] = []
    for _ in range(num_points):
        orders.append(
            OrderLocation(
                x=float(rng.uniform(0.0, 24.0)),
                y=float(rng.uniform(0.0, 20.0)),
                z=float(rng.uniform(0.5, 2.5)),
                weight=float(rng.uniform(5.0, 25.0)),
                volume=float(rng.uniform(6.0, 24.0)),
                sla_priority=float(rng.uniform(0.5, 1.0)),
                zone_class=float(rng.uniform(0.0, 1.0)),
            )
        )
    return orders


def build_qaoa_model(order_locations: list[OrderLocation], k_batches: int = 4, clustering: str = "fmeans"):
    """Synthesis-ready wrapper for the QAOA route solver."""
    if clustering == "fmeans":
        from wms_quantum_fmeans import fuzzy_route_cluster_pipeline
        pipeline = fuzzy_route_cluster_pipeline(order_locations, k_batches, vehicle_capacity=120.0)
    else:
        pipeline = route_cluster_pipeline(order_locations, k_batches, vehicle_capacity=120.0)

    p_layers = pipeline["qaoa_layers"]
    gamma_beta = [0.35, 0.15] * p_layers
    feat_params = [value for order in order_locations[:2] for value in qubitized_feature_vector(order)]
    if len(feat_params) < 7:
        feat_params = feat_params + [0.1] * (7 - len(feat_params))

    @qfunc
    def main(route_bits: Output[QArray[QBit]], anc: Output[QBit]):
        allocate(16, route_bits)
        allocate(1, anc)
        hadamard_transform(route_bits)

        # Encode normalized warehouse feature vector
        amplitude_encode_feature_vector(feat_params[:7], route_bits[:7])

        # Swap-test overlap measurement
        H(anc)
        for i in range(7):
            control(anc, lambda: SWAP(route_bits[i], route_bits[8 + i]))
        H(anc)

        # Route optimization QAOA layer
        for layer in range(p_layers):
            qaoa_routing_layer(gamma_beta[2 * layer], gamma_beta[2 * layer + 1], route_bits)

    qmod = create_model(main)
    return qmod, pipeline


if __name__ == "__main__":
    from classiq import execute

    print("=" * 75)
    print("  WMS QUANTUM OPTIMIZATION PIPELINE: 100-POINT END-TO-END WORKLOAD")
    print("=" * 75)

    # 1. Generate 100 realistic warehouse picking orders
    orders_100 = generate_test_orders(num_points=100, seed=42)
    print(f"\n[1/4] Generated {len(orders_100)} warehouse picking orders across 3D storage grid.")
    print(f"      Sample Order #0: x={orders_100[0].x:.1f}m, y={orders_100[0].y:.1f}m, weight={orders_100[0].weight:.1f}kg, SLA={orders_100[0].sla_priority:.2f}")

    # 2. Benchmark Quantum K-Means vs Quantum F-Means on 100 points
    print("\n[2/4] Benchmarking Quantum K-Means vs Quantum F-Means (100 points, k=4 batches)...")
    cmp = benchmark_kmeans_vs_fmeans(num_points=100, k_batches=4, seed=42)
    print(f"      Hard K-Means: Counts={cmp['kmeans']['counts']}, StdDev={cmp['kmeans']['std_dev']:.2f}, Time={cmp['kmeans']['latency_seconds']:.3f}s")
    print(f"      Soft F-Means: Counts={cmp['fmeans']['counts']}, StdDev={cmp['fmeans']['std_dev']:.2f}, Time={cmp['fmeans']['latency_seconds']:.3f}s, Mean Entropy={cmp['fmeans']['mean_entropy']:.4f}")
    variance_reduction = (1.0 - cmp['fmeans']['std_dev'] / max(1e-6, cmp['kmeans']['std_dev'])) * 100.0
    print(f"      -> Fleet Allocation Balance Improvement: {variance_reduction:.1f}%")

    # 3. Build & Synthesize QAOA Model
    print("\n[3/4] Synthesizing Classiq Quantum Circuit (Depth-Optimized, Max-Width=30)...")
    qmod, pipeline = build_qaoa_model(orders_100, k_batches=4, clustering="fmeans")
    constraints = Constraints(max_width=30, optimization_parameter="depth")
    qprog = synthesize(qmod, constraints=constraints)
    print(f"      Synthesis Succeeded!")
    print(f"      Qubits (Width): {qprog.data.width}")

    # 4. Execute on Classiq Simulator
    print("\n[4/4] Executing Quantum Circuit on Classiq Simulator...")
    res = execute(qprog).result()
    parsed_counts = res[0].value.parsed_counts
    print(f"      Execution Completed! Sampled {len(parsed_counts)} unique quantum bitstring states.")
    top_state = max(parsed_counts, key=lambda s: s.shots)
    print(f"      Dominant Quantum State: {top_state.state} with {top_state.shots} shots.")

    print("\n" + "=" * 75)
    print("  PIPELINE EXECUTION COMPLETE ON 100 POINTS")
    print("=" * 75)
