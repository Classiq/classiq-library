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

from wms_quantum_fmeans import (
    QuantumFMeans,
    quantum_fidelity_distance,
    quantum_swap_test_circuit,
    encode_fuzzy_feature_state,
)


@dataclass(frozen=True)
class MultiDepotLocation:
    """Represents a regional service depot / dispatch base."""
    id: int
    x: float
    y: float
    name: str = ""
    technician_count: int = 3
    max_capacity_kg: float = 350.0
    shift_hours: float = 8.0


@dataclass(frozen=True)
class FieldTask:
    """Represents a field-service customer task / work order."""
    id: int
    x: float
    y: float
    service_duration_min: float = 45.0
    weight_kg: float = 15.0
    priority_sla: float = 0.8
    skill_required: int = 1


def task_to_qubitized_vector(task: FieldTask, max_x: float = 60.0, max_y: float = 50.0) -> np.ndarray:
    """Encodes a field-service task into a normalized 7-dimensional quantum state vector."""
    raw = np.array(
        [
            task.x / max_x,
            task.y / max_y,
            min(1.0, task.service_duration_min / 120.0),
            min(1.0, task.weight_kg / 50.0),
            task.priority_sla,
            float(task.skill_required) / 3.0,
            0.5,
        ],
        dtype=float,
    ) + 0.05
    norm = np.linalg.norm(raw)
    return raw / norm if norm > 1e-9 else raw


def depot_to_qubitized_vector(depot: MultiDepotLocation, max_x: float = 60.0, max_y: float = 50.0) -> np.ndarray:
    """Encodes a regional depot into a normalized 7-dimensional quantum state vector."""
    raw = np.array(
        [
            depot.x / max_x,
            depot.y / max_y,
            0.5,
            0.5,
            1.0,
            1.0,
            0.5,
        ],
        dtype=float,
    ) + 0.05
    norm = np.linalg.norm(raw)
    return raw / norm if norm > 1e-9 else raw


class MultiDepotQuantumFMeans:
    """Tier-1 Multi-Depot Quantum Fuzzy C-Means (QFCM) Engine.

    Assigns field-service tasks across M regional depots using quantum fidelity
    overlap and multi-depot Shannon entropy rebalancing. Strictly guarantees
    No Split Across Depots (sum_d y_{id} = 1).
    """

    def __init__(
        self,
        m: float = 2.0,
        entropy_threshold: float = 0.45,
        max_iter: int = 60,
        tol: float = 1e-5,
    ):
        if m <= 1.0:
            raise ValueError("Fuzziness exponent m must be strictly greater than 1.0")
        self.m = m
        self.entropy_threshold = entropy_threshold
        self.max_iter = max_iter
        self.tol = tol

        self.depot_memberships_: np.ndarray | None = None
        self.depot_entropies_: np.ndarray | None = None
        self.assigned_depots_: list[int] = []

    def fit(
        self,
        tasks: Sequence[FieldTask],
        depots: Sequence[MultiDepotLocation],
        rebalance_workload: bool = True,
    ) -> "MultiDepotQuantumFMeans":
        n = len(tasks)
        m_depots = len(depots)
        if n == 0 or m_depots == 0:
            self.depot_memberships_ = np.empty((0, m_depots))
            self.depot_entropies_ = np.empty(0)
            self.assigned_depots_ = []
            return self

        # 1. Feature vectors
        task_vecs = np.vstack([task_to_qubitized_vector(t) for t in tasks])
        depot_vecs = np.vstack([depot_to_qubitized_vector(d) for d in depots])

        # 2. Compute quantum fidelity distance matrix D_{id} = 1 - |<psi_i|depot_d>|^2
        D = np.zeros((n, m_depots), dtype=float)
        for i in range(n):
            for d in range(m_depots):
                D[i, d] = quantum_fidelity_distance(task_vecs[i], depot_vecs[d])

        # 3. Compute continuous fuzzy membership probabilities U_{id}
        eps = 1e-9
        U = np.zeros((n, m_depots), dtype=float)
        p = float(min(50.0, 1.0 / max(1e-4, self.m - 1.0)))
        for i in range(n):
            zero_dist = np.where(D[i] < eps)[0]
            if len(zero_dist) > 0:
                U[i, zero_dist] = 1.0 / len(zero_dist)
            else:
                scaled_inv = 1.0 / np.maximum(D[i], eps)
                scaled_inv = scaled_inv / np.max(scaled_inv)
                inv_dists = scaled_inv ** p
                sum_inv = np.sum(inv_dists)
                U[i] = inv_dists / sum_inv if sum_inv > 1e-12 else (1.0 / m_depots)

        self.depot_memberships_ = U
        self.depot_entropies_ = -np.sum(U * np.log(np.maximum(U, 1e-12)), axis=1)

        # 4. Enforce strict No Split Across Depots and Workload Equilibrium
        if rebalance_workload:
            self.assigned_depots_ = self._entropy_rebalance_depots(tasks, depots, U)
        else:
            self.assigned_depots_ = np.argmax(U, axis=1).tolist()

        return self

    def _entropy_rebalance_depots(
        self,
        tasks: Sequence[FieldTask],
        depots: Sequence[MultiDepotLocation],
        memberships: np.ndarray,
    ) -> list[int]:
        """Dynamically shifts high-entropy boundary tasks from overloaded depots to underloaded depots."""
        n = len(tasks)
        m_depots = len(depots)
        crisp_labels = np.argmax(memberships, axis=1)

        # Workload metric per task: on-site service time + estimated depot transit time (minutes)
        # Average driving speed: 48.28 km/h = 0.804 km/min
        transit_speed_km_min = 48.28 / 60.0

        def calc_depot_workloads(labels: np.ndarray) -> np.ndarray:
            loads = np.zeros(m_depots, dtype=float)
            for idx, d in enumerate(labels):
                task = tasks[idx]
                dep = depots[d]
                dist_km = np.hypot(task.x - dep.x, task.y - dep.y)
                travel_time_min = (dist_km / transit_speed_km_min) * 1.25  # 1.25 route circuity factor
                loads[d] += task.service_duration_min + travel_time_min
            return loads

        current_loads = calc_depot_workloads(crisp_labels)
        # Total technician capacity in minutes per depot:
        depot_capacities = np.array([d.technician_count * d.shift_hours * 60.0 for d in depots], dtype=float)
        target_load = float(np.mean(current_loads))
        target_count = float(n / m_depots)

        # Identify boundary tasks with high Shannon entropy (situated between service depot territories)
        boundary_indices = np.where(self.depot_entropies_ > 0.25)[0]
        # Sort descending by entropy
        boundary_indices = boundary_indices[np.argsort(-self.depot_entropies_[boundary_indices])]

        rebalanced = crisp_labels.copy()

        for idx in boundary_indices:
            cur_dep = rebalanced[idx]
            task = tasks[idx]
            cur_load_ratio = current_loads[cur_dep] / max(depot_capacities[cur_dep], 1e-9)
            is_overloaded = (
                (cur_load_ratio > 0.80)
                or (current_loads[cur_dep] > target_load * 1.05)
                or (np.sum(rebalanced == cur_dep) > target_count + 1)
            )

            if is_overloaded:
                probs = memberships[idx]
                candidates = [d for d in range(m_depots) if d != cur_dep and probs[d] > 0.10]
                if not candidates:
                    continue

                # Choose candidate depot with lowest current workload
                best_cand = min(candidates, key=lambda d: current_loads[d])
                if current_loads[best_cand] < current_loads[cur_dep]:
                    dist_cur = np.hypot(task.x - depots[cur_dep].x, task.y - depots[cur_dep].y)
                    dist_new = np.hypot(task.x - depots[best_cand].x, task.y - depots[best_cand].y)
                    dt_cur = (dist_cur / transit_speed_km_min) * 1.25 + task.service_duration_min
                    dt_new = (dist_new / transit_speed_km_min) * 1.25 + task.service_duration_min

                    if current_loads[best_cand] + dt_new < current_loads[cur_dep]:
                        current_loads[cur_dep] -= dt_cur
                        current_loads[best_cand] += dt_new
                        rebalanced[idx] = best_cand

        return rebalanced.tolist()
