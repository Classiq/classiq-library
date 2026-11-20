import sys
import json
import urllib.request
from wms_multitier_dispatch import (
    generate_enterprise_service_problem,
    solve_multitier_dispatch,
    run_comprehensive_benchmark,
)

def test_engine():
    print("[*] Testing solve_multitier_dispatch with method='simulated_annealing'...")
    hubs, tasks = generate_enterprise_service_problem(num_tasks=40, total_technicians=12, num_hubs=3, seed=42)
    res = solve_multitier_dispatch(hubs, tasks, method="simulated_annealing")

    print(f"    Method: {res.method_name}")
    print(f"    Total Distance: {res.total_fleet_distance_km:.2f} km")
    print(f"    Total Operating Cost: ${res.total_operating_cost_usd:.2f}")
    print(f"    Skill Compliance: {res.skill_compliance_rate}%")
    print(f"    Shift Compliance: {res.shift_compliance_rate}%")
    print(f"    Runtime: {res.runtime_seconds:.3f} s")
    print(f"    Active Techs: {len(res.active_technicians)}")

    assert res.skill_compliance_rate == 100.0, "Skill compliance must be 100%"
    assert res.total_fleet_distance_km > 0.0, "Distance must be > 0"
    assert len(res.active_technicians) > 0, "Must have active technicians"
    print("[OK] Direct engine test passed!")

    print("[*] Testing run_comprehensive_benchmark with simulated_annealing included...")
    bench = run_comprehensive_benchmark(num_tasks=30, total_technicians=10, num_hubs=2, seed=42)
    assert "simulated_annealing" in bench["scenarios"], "simulated_annealing must be in scenarios"
    sa_entry = bench["scenarios"]["simulated_annealing"]
    print(f"    Benchmark SA Distance: {sa_entry['distance_km']} km, Code: {sa_entry['method_code']}")
    print("[OK] Comprehensive benchmark test passed!")

if __name__ == "__main__":
    try:
        test_engine()
        print("\n[SUCCESS] All Simulated Annealing unit tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Test error: {e}")
        sys.exit(1)
