import os
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
from applications.logistics.vehicle_routing_problem.wms_multitier_dispatch import (
    generate_enterprise_service_problem,
    solve_multitier_dispatch,
)
import copy

def evaluate_scenario(num_tasks, total_techs, num_hubs, m, emergency_ratio, seed=42):
    hubs, tasks = generate_enterprise_service_problem(
        num_tasks=num_tasks,
        total_technicians=total_techs,
        num_hubs=num_hubs,
        emergency_sla_ratio=emergency_ratio,
        seed=seed
    )

    hubs1, tasks1 = copy.deepcopy(hubs), copy.deepcopy(tasks)
    hubs2, tasks2 = copy.deepcopy(hubs), copy.deepcopy(tasks)
    hubs3, tasks3 = copy.deepcopy(hubs), copy.deepcopy(tasks)

    res_fifo = solve_multitier_dispatch(hubs1, tasks1, method="baseline_fifo")
    res_km = solve_multitier_dispatch(hubs2, tasks2, method="hard_kmeans")
    res_qfcm = solve_multitier_dispatch(hubs3, tasks3, method="quantum_multitier_qfcm", fuzziness_m=m)

    return {
        "N": num_tasks,
        "K": total_techs,
        "M": num_hubs,
        "m": m,
        "emergency": emergency_ratio,
        "fifo_dist": res_fifo.total_fleet_distance_km,
        "km_dist": res_km.total_fleet_distance_km,
        "qfcm_dist": res_qfcm.total_fleet_distance_km,
        "fifo_shift_comp": res_fifo.shift_compliance_rate,
        "km_shift_comp": res_km.shift_compliance_rate,
        "qfcm_shift_comp": res_qfcm.shift_compliance_rate,
        "fifo_depot_std": res_fifo.depot_workload_std,
        "km_depot_std": res_km.depot_workload_std,
        "qfcm_depot_std": res_qfcm.depot_workload_std,
        "dist_saved_vs_fifo": res_fifo.total_fleet_distance_km - res_qfcm.total_fleet_distance_km,
        "shift_diff_vs_km": res_qfcm.shift_compliance_rate - res_km.shift_compliance_rate,
        "depot_balance_diff_vs_km": res_km.depot_workload_std - res_qfcm.depot_workload_std,
    }

print("=== 1. PARAMETER SWEEP: Fuzziness Exponent (m) ===")
for m_val in [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 3.0]:
    r = evaluate_scenario(num_tasks=80, total_techs=1000, num_hubs=4, m=m_val, emergency_ratio=0.15)
    print(f"m={m_val:.1f} | Dist: FIFO={r['fifo_dist']:.0f}km, KM={r['km_dist']:.0f}km, QFCM={r['qfcm_dist']:.0f}km | ShiftComp: KM={r['km_shift_comp']:.1f}%, QFCM={r['qfcm_shift_comp']:.1f}% | DepotStd: KM={r['km_depot_std']:.2f}h, QFCM={r['qfcm_depot_std']:.2f}h")

print("\n=== 2. PARAMETER SWEEP: Customer Tasks (N) ===")
for n_val in [20, 40, 60, 80, 120, 200, 400]:
    r = evaluate_scenario(num_tasks=n_val, total_techs=1000, num_hubs=4, m=2.0, emergency_ratio=0.15)
    print(f"N={n_val:3d} | Dist: FIFO={r['fifo_dist']:.0f}km, KM={r['km_dist']:.0f}km, QFCM={r['qfcm_dist']:.0f}km | ShiftComp: KM={r['km_shift_comp']:.1f}%, QFCM={r['qfcm_shift_comp']:.1f}% | DistSaved vs FIFO={r['dist_saved_vs_fifo']:.0f}km")

print("\n=== 3. PARAMETER SWEEP: Regional Hubs (M) ===")
for m_hubs in [2, 3, 4, 6, 8, 12]:
    r = evaluate_scenario(num_tasks=120, total_techs=1000, num_hubs=m_hubs, m=2.0, emergency_ratio=0.15)
    print(f"M={m_hubs:2d} | Dist: FIFO={r['fifo_dist']:.0f}km, KM={r['km_dist']:.0f}km, QFCM={r['qfcm_dist']:.0f}km | ShiftComp: KM={r['km_shift_comp']:.1f}%, QFCM={r['qfcm_shift_comp']:.1f}% | DepotStd: KM={r['km_depot_std']:.2f}h, QFCM={r['qfcm_depot_std']:.2f}h")

print("\n=== 4. PARAMETER SWEEP: Fleet Size (K Technicians) ===")
for k_val in [8, 16, 50, 200, 1000, 10000, 35000]:
    r = evaluate_scenario(num_tasks=100, total_techs=k_val, num_hubs=4, m=2.0, emergency_ratio=0.15)
    print(f"K={k_val:5d} | Dist: FIFO={r['fifo_dist']:.0f}km, KM={r['km_dist']:.0f}km, QFCM={r['qfcm_dist']:.0f}km | ShiftComp: KM={r['km_shift_comp']:.1f}%, QFCM={r['qfcm_shift_comp']:.1f}%")

print("\n=== 5. PARAMETER SWEEP: Emergency 911 SLA Ratio ===")
for em_val in [0.0, 0.10, 0.20, 0.35, 0.50]:
    r = evaluate_scenario(num_tasks=100, total_techs=1000, num_hubs=4, m=2.0, emergency_ratio=em_val)
    print(f"Em={em_val:.2f} | Dist: FIFO={r['fifo_dist']:.0f}km, KM={r['km_dist']:.0f}km, QFCM={r['qfcm_dist']:.0f}km | ShiftComp: KM={r['km_shift_comp']:.1f}%, QFCM={r['qfcm_shift_comp']:.1f}% | DepotStd: KM={r['km_depot_std']:.2f}h, QFCM={r['qfcm_depot_std']:.2f}h")
