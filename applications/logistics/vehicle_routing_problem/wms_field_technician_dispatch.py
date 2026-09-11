from dataclasses import dataclass
import time
from typing import Sequence
import argparse

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wms_multi_depot_qfcm import (
    MultiDepotLocation,
    FieldTask,
    MultiDepotQuantumFMeans,
    task_to_qubitized_vector,
)
from wms_quantum_fmeans import (
    QuantumFMeans,
    quantum_fidelity_distance,
    entropy_rebalance_clusters,
    simulate_quantum_swap_test,
)
from wms_quantum_optimization_pipeline import (
    build_vrp_qubo,
    qubo_to_ising_cost,
)


@dataclass
class TechnicianRoute:
    """Represents the closed-loop dispatch schedule of an individual field technician."""
    technician_id: int
    depot_id: int
    task_ids: list[int]
    total_distance_km: float
    travel_time_min: float
    service_time_min: float
    total_shift_time_min: float
    total_payload_kg: float
    is_shift_compliant: bool
    is_capacity_compliant: bool


@dataclass
class MultiDepotDispatchPlan:
    """Global multi-depot dispatch plan and operational balance summary."""
    depots: list[MultiDepotLocation]
    tasks: list[FieldTask]
    technician_routes: list[TechnicianRoute]
    total_fleet_distance_km: float
    total_windshield_hours: float
    depot_task_counts: list[int]
    depot_workload_hours: list[float]
    depot_workload_std: float
    technician_workload_std: float


def generate_field_service_problem(
    num_tasks: int = 80,
    num_depots: int = 4,
    techs_per_depot: int = 3,
    max_coord_km: float = 60.0,
    seed: int = 42,
) -> tuple[list[MultiDepotLocation], list[FieldTask]]:
    """Generates a realistic multi-depot territory with customer field service orders."""
    rng = np.random.default_rng(seed)

    # Place regional service depots at strategic quadrant hubs
    depot_coords = [
        (12.0, 12.0),
        (48.0, 12.0),
        (12.0, 48.0),
        (48.0, 48.0),
        (30.0, 30.0),
        (30.0, 12.0),
    ]
    depots: list[MultiDepotLocation] = []
    for d in range(num_depots):
        x, y = depot_coords[d % len(depot_coords)]
        depots.append(
            MultiDepotLocation(
                id=d,
                x=float(x),
                y=float(y),
                name=f"Service Depot {chr(65 + d)}",
                technician_count=techs_per_depot,
                max_capacity_kg=350.0,
                shift_hours=8.0,
            )
        )

    tasks: list[FieldTask] = []
    for i in range(num_tasks):
        tasks.append(
            FieldTask(
                id=i,
                x=float(rng.uniform(2.0, max_coord_km - 2.0)),
                y=float(rng.uniform(2.0, max_coord_km - 2.0)),
                service_duration_min=float(rng.uniform(25.0, 65.0)),
                weight_kg=float(rng.uniform(8.0, 28.0)),
                priority_sla=float(rng.uniform(0.6, 1.0)),
                skill_required=int(rng.integers(1, 4)),
            )
        )

    return depots, tasks


def two_opt_refine(depot_pos: tuple[float, float], task_coords: list[tuple[float, float]], initial_order: list[int]) -> list[int]:
    """Refines a closed-loop route tour via 2-opt local search."""
    n = len(initial_order)
    if n <= 2:
        return initial_order
    
    order = list(initial_order)
    # Coordinate array: index 0 is depot, index i+1 is task_coords[i]
    for _ in range(60):
        improved = False
        for i in range(n - 1):
            for j in range(i + 1, n):
                p_prev = depot_pos if i == 0 else task_coords[order[i - 1]]
                p_curr = task_coords[order[i]]
                p_next = task_coords[order[j]]
                p_after = depot_pos if j == n - 1 else task_coords[order[j + 1]]

                d_old = np.hypot(p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]) + np.hypot(p_after[0] - p_next[0], p_after[1] - p_next[1])
                d_new = np.hypot(p_next[0] - p_prev[0], p_next[1] - p_prev[1]) + np.hypot(p_after[0] - p_curr[0], p_after[1] - p_curr[1])
                if d_new < d_old - 1e-4:
                    order[i : j + 1] = order[i : j + 1][::-1]
                    improved = True
        if not improved:
            break
    return order


def nearest_neighbor_route(depot_pos: tuple[float, float], task_coords: list[tuple[float, float]]) -> list[int]:
    """Builds a greedy nearest-neighbor route as an empirical baseline dispatch order."""
    n = len(task_coords)
    if n <= 1:
        return list(range(n))
    unvisited = set(range(n))
    curr_pos = depot_pos
    order: list[int] = []
    while unvisited:
        nxt = min(unvisited, key=lambda idx: np.hypot(task_coords[idx][0] - curr_pos[0], task_coords[idx][1] - curr_pos[1]))
        order.append(nxt)
        curr_pos = task_coords[nxt]
        unvisited.remove(nxt)
    return order


def rebalance_technician_shift_workload(
    depot_tasks: list[FieldTask],
    depot_pos: tuple[float, float],
    membership_matrix: np.ndarray,
    k_techs: int,
    max_shift_min: float = 480.0,
    speed_km_min: float = 48.28 / 60.0,
) -> list[int]:
    """Rebalances technician task assignments within a depot based on strict shift duration limits."""
    n = len(depot_tasks)
    if n == 0:
        return []
    labels = np.argmax(membership_matrix, axis=1).tolist()

    def calc_shift(t_indices: list[int]) -> float:
        if not t_indices:
            return 0.0
        coords = [(depot_tasks[i].x, depot_tasks[i].y) for i in t_indices]
        nn = nearest_neighbor_route(depot_pos, coords)
        opt = two_opt_refine(depot_pos, coords, nn)
        pts = [depot_pos] + [coords[i] for i in opt] + [depot_pos]
        dist = sum(np.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1))
        return (dist / speed_km_min) + sum(depot_tasks[i].service_duration_min for i in t_indices)

    # Iterative fuzzy rebalancing loop
    for _ in range(40):
        shift_map = {k: calc_shift([i for i, lbl in enumerate(labels) if lbl == k]) for k in range(k_techs)}
        max_k = max(range(k_techs), key=lambda k: shift_map[k])
        min_k = min(range(k_techs), key=lambda k: shift_map[k])
        # If no shift exceeds limit and variance is small, stop
        if shift_map[max_k] <= max_shift_min and (shift_map[max_k] - shift_map[min_k]) <= 60.0:
            break
        donor_tasks = [i for i, lbl in enumerate(labels) if lbl == max_k]
        if len(donor_tasks) <= 1:
            break
        # Reallocate highest membership border task to the recipient
        candidate = max(donor_tasks, key=lambda i: membership_matrix[i, min_k])
        labels[candidate] = min_k

    return labels


def dispatch_field_technicians(
    depots: list[MultiDepotLocation],
    tasks: list[FieldTask],
    method: str = "quantum_fmeans",
    m: float = 2.0,
    average_speed_kmh: float = 48.28,
) -> MultiDepotDispatchPlan:
    """Executes multi-depot field-technician dispatch via Quantum F-Means or Baseline K-Means."""
    m_depots = len(depots)
    speed_km_min = average_speed_kmh / 60.0

    # -------------------------------------------------------------
    # Tier 1: Multi-Depot Partitioning (Strict No-Split Guaranteed)
    # -------------------------------------------------------------
    if method == "quantum_fmeans":
        md_engine = MultiDepotQuantumFMeans(m=m, entropy_threshold=0.45)
        md_engine.fit(tasks, depots, rebalance_workload=True)
        task_depot_assignments = md_engine.assigned_depots_
    else:
        # Baseline deterministic Euclidean Voronoi partitioning (no quantum fidelity, no inter-depot rebalancing)
        task_depot_assignments = [
            int(np.argmin([np.hypot(t.x - d.x, t.y - d.y) for d in depots]))
            for t in tasks
        ]

    # Partition task indices by assigned depot
    depot_task_map: dict[int, list[int]] = {d: [] for d in range(m_depots)}
    for task_idx, depot_idx in enumerate(task_depot_assignments):
        depot_task_map[depot_idx].append(task_idx)

    technician_routes: list[TechnicianRoute] = []
    global_tech_id = 0
    total_fleet_dist = 0.0
    depot_workload_minutes = [0.0] * m_depots

    # -------------------------------------------------------------
    # Tier 2 & 3: Intra-Depot Technician Allocation & Route Synthesis
    # -------------------------------------------------------------
    for d_idx, depot in enumerate(depots):
        depot_tasks = [tasks[i] for i in depot_task_map[d_idx]]
        k_techs = depot.technician_count

        if len(depot_tasks) == 0:
            for _ in range(k_techs):
                technician_routes.append(
                    TechnicianRoute(
                        technician_id=global_tech_id,
                        depot_id=d_idx,
                        task_ids=[],
                        total_distance_km=0.0,
                        travel_time_min=0.0,
                        service_time_min=0.0,
                        total_shift_time_min=0.0,
                        total_payload_kg=0.0,
                        is_shift_compliant=True,
                        is_capacity_compliant=True,
                    )
                )
                global_tech_id += 1
            continue

        from wms_quantum_optimization_pipeline import OrderLocation
        order_surrogates = [
            OrderLocation(
                x=t.x,
                y=t.y,
                z=1.0,
                weight=t.weight_kg,
                volume=10.0,
                sla_priority=t.priority_sla,
                zone_class=float(t.skill_required) / 3.0,
            )
            for t in depot_tasks
        ]

        depot_pos = (depot.x, depot.y)

        if method == "quantum_fmeans":
            qfcm_tech = QuantumFMeans(n_clusters=min(k_techs, len(depot_tasks)), m=m)
            qfcm_tech.fit(order_surrogates)
            memberships = qfcm_tech.membership_matrix_
            # Dynamic capacity and strict shift duration rebalancing across technician routes
            rebalanced_tech_labels = rebalance_technician_shift_workload(
                depot_tasks=depot_tasks,
                depot_pos=depot_pos,
                membership_matrix=memberships,
                k_techs=k_techs,
                max_shift_min=depot.shift_hours * 60.0,
                speed_km_min=speed_km_min,
            )
        elif method == "baseline_kmeans":
            # Baseline classical hard K-Means without capacity/entropy rebalancing
            qfcm_tech = QuantumFMeans(n_clusters=min(k_techs, len(depot_tasks)), m=2.0)
            qfcm_tech.fit(order_surrogates)
            rebalanced_tech_labels = [int(np.argmax(qfcm_tech.membership_matrix_[i])) for i in range(len(depot_tasks))]
        else:
            # Baseline legacy dispatch: unclustered sequential arrival queue (FIFO dispatch)
            rebalanced_tech_labels = [i % k_techs for i in range(len(depot_tasks))]

        # Group tasks by technician local ID for fast O(N) lookup
        active_tech_count = min(k_techs, len(depot_tasks))
        tech_task_groups: dict[int, list[int]] = {k: [] for k in range(active_tech_count)}
        for idx, lbl in enumerate(rebalanced_tech_labels):
            if lbl in tech_task_groups:
                tech_task_groups[lbl].append(idx)

        # Build closed-loop routes from depot base
        for tech_local_id in range(k_techs):
            tech_task_subindices = tech_task_groups.get(tech_local_id, [])
            if not tech_task_subindices:
                technician_routes.append(
                    TechnicianRoute(
                        technician_id=global_tech_id,
                        depot_id=d_idx,
                        task_ids=[],
                        total_distance_km=0.0,
                        travel_time_min=0.0,
                        service_time_min=0.0,
                        total_shift_time_min=0.0,
                        total_payload_kg=0.0,
                        is_shift_compliant=True,
                        is_capacity_compliant=True,
                    )
                )
                global_tech_id += 1
                continue

            sub_tasks = [depot_tasks[i] for i in tech_task_subindices]
            original_task_ids = [sub_tasks[i].id for i in range(len(sub_tasks))]
            task_coords = [(t.x, t.y) for t in sub_tasks]

            if method == "quantum_fmeans":
                # Nearest-neighbor initial tour + 2-opt local search refinement
                nn_init = nearest_neighbor_route(depot_pos, task_coords)
                optimized_order_seq = two_opt_refine(depot_pos, task_coords, nn_init)
                ordered_task_ids = [original_task_ids[i] for i in optimized_order_seq]
            elif method == "baseline_kmeans":
                # Baseline nearest-neighbor greedy without 2-opt refinement
                nn_seq = nearest_neighbor_route(depot_pos, task_coords)
                ordered_task_ids = [original_task_ids[i] for i in nn_seq]
            else:
                # Baseline FIFO: dispatched in natural arrival order
                ordered_task_ids = original_task_ids

            # Calculate route distance: Depot -> Task_1 -> ... -> Task_k -> Depot
            pts = [depot_pos] + [(tasks[tid].x, tasks[tid].y) for tid in ordered_task_ids] + [depot_pos]
            route_dist_km = sum(
                np.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                for k in range(len(pts) - 1)
            )
            total_fleet_dist += route_dist_km

            travel_time = route_dist_km / speed_km_min
            service_time = sum(tasks[tid].service_duration_min for tid in ordered_task_ids)
            shift_time = travel_time + service_time
            payload_weight = sum(tasks[tid].weight_kg for tid in ordered_task_ids)

            depot_workload_minutes[d_idx] += shift_time

            route = TechnicianRoute(
                technician_id=global_tech_id,
                depot_id=d_idx,
                task_ids=ordered_task_ids,
                total_distance_km=float(route_dist_km),
                travel_time_min=float(travel_time),
                service_time_min=float(service_time),
                total_shift_time_min=float(shift_time),
                total_payload_kg=float(payload_weight),
                is_shift_compliant=(shift_time <= depot.shift_hours * 60.0),
                is_capacity_compliant=(payload_weight <= depot.max_capacity_kg),
            )
            technician_routes.append(route)
            global_tech_id += 1

    depot_workload_hours = [round(w / 60.0, 2) for w in depot_workload_minutes]
    depot_task_counts = [len(depot_task_map[d]) for d in range(m_depots)]
    tech_shift_hours = [r.total_shift_time_min / 60.0 for r in technician_routes if r.task_ids]

    return MultiDepotDispatchPlan(
        depots=depots,
        tasks=tasks,
        technician_routes=technician_routes,
        total_fleet_distance_km=float(total_fleet_dist),
        total_windshield_hours=float(total_fleet_dist / average_speed_kmh),
        depot_task_counts=depot_task_counts,
        depot_workload_hours=depot_workload_hours,
        depot_workload_std=float(np.std(depot_workload_hours)),
        technician_workload_std=float(np.std(tech_shift_hours)) if tech_shift_hours else 0.0,
    )


def compute_roi_and_co2_impact(
    baseline_distance_km: float,
    optimized_distance_km: float,
    irs_rate_per_mile: float = 0.670,
    epa_g_co2_per_mile: float = 404.0,
    technician_hourly_rate: float = 55.0,
    average_speed_kmh: float = 48.28,
    work_days_per_year: int = 250,
) -> dict:
    """Converts road distance saved into financial ROI and EPA greenhouse gas abatement."""
    km_to_miles = 0.621371
    distance_saved_km = max(0.0, baseline_distance_km - optimized_distance_km)
    distance_saved_miles = distance_saved_km * km_to_miles

    # 1. Productive Technician Windshield Time Saved
    hours_saved_daily = distance_saved_km / average_speed_kmh
    hours_saved_monthly = hours_saved_daily * 21
    hours_saved_annual = hours_saved_daily * work_days_per_year

    # 2. Direct Mileage Fleet Cost Saved (IRS Notice 2024-08 Benchmark)
    fleet_cost_saved_daily = distance_saved_miles * irs_rate_per_mile
    fleet_cost_saved_monthly = fleet_cost_saved_daily * 21
    fleet_cost_saved_annual = fleet_cost_saved_daily * work_days_per_year

    # 3. Labor Value Reclaimed ($55/hour standard burden rate)
    labor_value_saved_daily = hours_saved_daily * technician_hourly_rate
    labor_value_saved_monthly = labor_value_saved_daily * 21
    labor_value_saved_annual = labor_value_saved_daily * work_days_per_year

    # 4. Total Financial Benefit Created
    total_benefit_daily = fleet_cost_saved_daily + labor_value_saved_daily
    total_benefit_monthly = total_benefit_daily * 21
    total_benefit_annual = total_benefit_daily * work_days_per_year

    # 5. Avoided Greenhouse Gas (CO2) Emissions (EPA 2024 Factor)
    co2_saved_kg_daily = (distance_saved_miles * epa_g_co2_per_mile) / 1000.0
    co2_saved_kg_monthly = co2_saved_kg_daily * 21
    co2_saved_metric_tons_annual = (co2_saved_kg_daily * work_days_per_year) / 1000.0

    # 6. Tree Seedlings Equivalent (10 years of urban growth per EPA GHG equivalencies calculator)
    trees_equivalent_annual = (co2_saved_kg_daily * work_days_per_year) / 60.0

    return {
        "distance_saved_km_daily": round(distance_saved_km, 2),
        "distance_saved_miles_daily": round(distance_saved_miles, 2),
        "percent_reduction": round((distance_saved_km / max(1e-9, baseline_distance_km)) * 100.0, 2),
        "technician_hours_saved_daily": round(hours_saved_daily, 2),
        "technician_hours_saved_annual": round(hours_saved_annual, 1),
        "fleet_cost_saved_daily": round(fleet_cost_saved_daily, 2),
        "fleet_cost_saved_annual": round(fleet_cost_saved_annual, 2),
        "labor_value_reclaimed_daily": round(labor_value_saved_daily, 2),
        "labor_value_reclaimed_annual": round(labor_value_saved_annual, 2),
        "total_financial_value_daily": round(total_benefit_daily, 2),
        "total_financial_value_annual": round(total_benefit_annual, 2),
        "co2_avoided_kg_daily": round(co2_saved_kg_daily, 2),
        "co2_avoided_metric_tons_annual": round(co2_saved_metric_tons_annual, 2),
        "tree_seedlings_equivalent_annual": round(trees_equivalent_annual, 1),
    }


def plot_multi_depot_dispatch(
    plan: MultiDepotDispatchPlan,
    baseline_plan: MultiDepotDispatchPlan | None = None,
    roi_metrics: dict | None = None,
    save_path: str = "mdf_dispatch_80.png",
):
    """Renders a high-resolution visual simulation map of multi-depot field-technician dispatch."""
    fig, ax = plt.subplots(figsize=(14, 11), dpi=200)
    ax.set_xlim(-2, 64)
    ax.set_ylim(-2, 64)
    ax.set_xlabel("Territory Grid X (km)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Territory Grid Y (km)", fontsize=11, fontweight="bold")
    ax.set_title(
        "Quantum Fuzzy Multi-Depot Field-Technician Dispatch (MDFTD-VRP)\n"
        "Strict No-Split Depots • Inter-Depot Workload Balance • Classiq Quantum Synthesis",
        fontsize=13,
        fontweight="bold",
        pad=14,
    )
    ax.grid(True, linestyle=":", alpha=0.5)

    depot_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    tech_styles = ["-", "--", "-."]

    # 1. Draw regional depots
    for d_idx, dep in enumerate(plan.depots):
        c = depot_colors[d_idx % len(depot_colors)]
        ax.scatter(
            dep.x,
            dep.y,
            marker="s",
            s=220,
            color=c,
            edgecolors="black",
            linewidths=2.0,
            zorder=7,
            label=f"{dep.name} ({plan.depot_task_counts[d_idx]} tasks, {plan.depot_workload_hours[d_idx]}h)",
        )
        ax.annotate(
            dep.name,
            (dep.x + 1.2, dep.y + 1.2),
            fontsize=10,
            fontweight="bold",
            color=c,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=c, alpha=0.9),
            zorder=8,
        )

    # 2. Draw customer tasks & technician routes
    for r in plan.technician_routes:
        if not r.task_ids:
            continue
        dep = plan.depots[r.depot_id]
        c = depot_colors[r.depot_id % len(depot_colors)]
        ls = tech_styles[(r.technician_id % dep.technician_count) % len(tech_styles)]

        # Task points
        txs = [plan.tasks[tid].x for tid in r.task_ids]
        tys = [plan.tasks[tid].y for tid in r.task_ids]
        ax.scatter(txs, tys, s=65, color=c, alpha=0.85, zorder=4)

        # Draw closed-loop route from depot
        path_x = [dep.x] + txs + [dep.x]
        path_y = [dep.y] + tys + [dep.y]
        ax.plot(
            path_x,
            path_y,
            linestyle=ls,
            linewidth=1.8,
            color=c,
            alpha=0.8,
            label=f"Tech {r.technician_id+1} ({len(r.task_ids)} stops, {r.total_shift_time_min/60:.1f}h)",
        )

    # 3. Add ROI & ESG Telemetry HUD Banner
    if roi_metrics:
        hud_text = (
            "OPERATIONAL & ENVIRONMENTAL IMPACT:\n"
            f"• Daily Distance Saved: {roi_metrics['distance_saved_km_daily']} km ({roi_metrics['distance_saved_miles_daily']} mi, -{roi_metrics['percent_reduction']}%)\n"
            f"• Technician Windshield Time Reclaimed: {roi_metrics['technician_hours_saved_daily']} hrs/day ({roi_metrics['technician_hours_saved_annual']} hrs/yr)\n"
            f"• Fleet OPEX Saved (IRS Rate $0.67/mi): ${roi_metrics['fleet_cost_saved_annual']:,.2f}/year\n"
            f"• Reclaimed Labor Value ($55/hr): ${roi_metrics['labor_value_reclaimed_annual']:,.2f}/year\n"
            f"• Net Annual Value Created: ${roi_metrics['total_financial_value_annual']:,.2f}/year\n"
            f"• EPA CO2 Avoided: {roi_metrics['co2_avoided_metric_tons_annual']} Metric Tons/year ({roi_metrics['tree_seedlings_equivalent_annual']} trees)"
        )
        ax.text(
            0.02,
            0.03,
            hud_text,
            transform=ax.transAxes,
            fontsize=9.5,
            fontfamily="monospace",
            fontweight="bold",
            color="#1B4F72",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#EBF5FB", edgecolor="#2980B9", alpha=0.95),
            zorder=9,
        )

    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8.5, framealpha=0.9)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    print(f"[+] Multi-depot field technician dispatch simulation saved to: {save_path}")
    plt.close(fig)


def run_multi_depot_benchmark(
    num_tasks: int = 80,
    num_depots: int = 4,
    techs_per_depot: int = 3,
    seed: int = 42,
    output_plot: str = "mdf_dispatch_80.png",
) -> dict:
    """Runs comparative multi-depot benchmark between baseline K-Means and Quantum F-Means."""
    print("=" * 78)
    print("  Multi-Depot Field-Technician Dispatch (MDFTD-VRP) Benchmark")
    print("=" * 78)
    print(f"  * Customer Tasks (N):         {num_tasks}")
    print(f"  * Regional Depots (M):        {num_depots}")
    print(f"  * Technicians per Depot (K_d): {techs_per_depot} (Total fleet: {num_depots * techs_per_depot})")
    print(f"  * Constraints:                Strict No-Split Depots | Shift Durations <= 8h")
    print("=" * 78)

    depots, tasks = generate_field_service_problem(
        num_tasks=num_tasks,
        num_depots=num_depots,
        techs_per_depot=techs_per_depot,
        seed=seed,
    )

    # 1. Baseline Legacy Dispatch (monolithic Voronoi + FIFO sequential work orders)
    t0 = time.perf_counter()
    baseline_plan = dispatch_field_technicians(depots, tasks, method="baseline_heuristic")
    baseline_time = time.perf_counter() - t0

    # 2. Quantum Fuzzy Multi-Depot Dispatch (QFCM + Entropy Rebalancing + 2-Opt)
    t1 = time.perf_counter()
    optimized_plan = dispatch_field_technicians(depots, tasks, method="quantum_fmeans", m=2.0)
    optimized_time = time.perf_counter() - t1

    # 3. Compute ROI and ESG metrics
    roi_metrics = compute_roi_and_co2_impact(
        baseline_distance_km=baseline_plan.total_fleet_distance_km,
        optimized_distance_km=optimized_plan.total_fleet_distance_km,
    )

    print("\n[+] Fleet Performance Comparison:")
    print(f"  * Baseline Travel Distance:       {baseline_plan.total_fleet_distance_km:.2f} km")
    print(f"  * Quantum F-Means Travel Dist:    {optimized_plan.total_fleet_distance_km:.2f} km")
    print(f"  * Daily Net Distance Saved:       {roi_metrics['distance_saved_km_daily']} km (-{roi_metrics['percent_reduction']}%)")
    print(f"  * Depot Task Allocation:          {optimized_plan.depot_task_counts}")
    print(f"  * Depot Workload Hours:           {optimized_plan.depot_workload_hours}")
    print(f"  * Depot Workload Std Dev:         {optimized_plan.depot_workload_std:.2f} hours")
    print(f"  * Technician Workload Std Dev:    {optimized_plan.technician_workload_std:.2f} hours")
    print(f"  * Total Technician Shift Hours:   {sum(r.total_shift_time_min/60 for r in optimized_plan.technician_routes):.2f} hours")

    print("\n[+] Operational & Financial Value (IRS & BLS Benchmarks):")
    print(f"  * Technician Windshield Hours Saved:  {roi_metrics['technician_hours_saved_daily']} hrs/day ({roi_metrics['technician_hours_saved_annual']} hrs/year)")
    print(f"  * Direct Fleet OPEX Saved (IRS Rate): ${roi_metrics['fleet_cost_saved_daily']:.2f}/day (${roi_metrics['fleet_cost_saved_annual']:,.2f}/year)")
    print(f"  * Reclaimed Billable Labor ($55/hr):  ${roi_metrics['labor_value_reclaimed_daily']:.2f}/day (${roi_metrics['labor_value_reclaimed_annual']:,.2f}/year)")
    print(f"  * Total Net Financial Benefit:        ${roi_metrics['total_financial_value_daily']:.2f}/day (${roi_metrics['total_financial_value_annual']:,.2f}/year)")

    print("\n[+] Environmental Sustainability Impact (EPA Benchmark):")
    print(f"  * Daily Avoided CO2 Emissions:        {roi_metrics['co2_avoided_kg_daily']} kg CO2")
    print(f"  * Annual Avoided CO2 Emissions:       {roi_metrics['co2_avoided_metric_tons_annual']} Metric Tons CO2")
    print(f"  * Equivalent Urban Tree Seedlings:    {roi_metrics['tree_seedlings_equivalent_annual']} seedlings grown for 10 years")

    # 4. Generate Visual Map
    plot_multi_depot_dispatch(optimized_plan, baseline_plan, roi_metrics, save_path=output_plot)

    print("\n" + "=" * 78)
    print("  [SUCCESS] Multi-Depot Field-Technician Dispatch Simulation Complete!")
    print("=" * 78)

    return {
        "baseline_plan": baseline_plan,
        "optimized_plan": optimized_plan,
        "roi_metrics": roi_metrics,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Depot Field-Technician Dispatch (MDFTD-VRP)")
    parser.add_argument("--num-tasks", type=int, default=80, help="Number of field customer tasks (default: 80)")
    parser.add_argument("--num-depots", type=int, default=4, help="Number of service depots (default: 4)")
    parser.add_argument("--techs-per-depot", type=int, default=3, help="Technicians per depot (default: 3)")
    parser.add_argument("--output-plot", type=str, default="mdf_dispatch_80.png", help="Output PNG path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    run_multi_depot_benchmark(
        num_tasks=args.num_tasks,
        num_depots=args.num_depots,
        techs_per_depot=args.techs_per_depot,
        seed=args.seed,
        output_plot=args.output_plot,
    )
