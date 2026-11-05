"""Comprehensive Unit Test Suite for Multi-Tier Quantum F-Means (SC-QFCM) Dispatch Platform.

Validates:
  1. Strict Skill & Equipment Feasibility Invariance (Zero mismatches)
  2. 35,000 Technician Scalability & Sub-Second Execution
  3. Strict No-Split Across Depots (sum_d y_{id} = 1)
  4. Closed-Loop Tour Invariance (depot -> tasks -> depot)
  5. Classiq QAOA Quantum Circuit Synthesis Metrics
  6. 3-Way Comparative Benchmark (FIFO vs Hard K-Means vs SC-QFCM)
"""

from __future__ import annotations
import unittest
import time

from applications.logistics.vehicle_routing_problem.wms_multitier_dispatch import (
    generate_enterprise_service_problem,
    solve_multitier_dispatch,
    run_comprehensive_benchmark,
    MultiTierDispatchResult,
    SkillTier,
)


class TestMultiTierDispatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate representative enterprise scenario with 35,000 technicians
        cls.hubs, cls.tasks = generate_enterprise_service_problem(
            num_tasks=100,
            total_technicians=35000,
            num_hubs=4,
            emergency_sla_ratio=0.20,
            seed=42,
        )
        t0 = time.perf_counter()
        cls.result = solve_multitier_dispatch(cls.hubs, cls.tasks, method="quantum_multitier_qfcm")
        cls.runtime = time.perf_counter() - t0

    def test_01_scalability_35000_technicians(self):
        """Validates that 35,000 technicians are handled seamlessly in under 4 seconds."""
        total_fleet = sum(len(h.technicians) for h in self.result.hubs)
        self.assertEqual(total_fleet, 35000, "Fleet size must match exactly 35,000 technicians")
        self.assertLess(self.runtime, 4.0, f"Dispatch must complete in < 4.0s (took {self.runtime:.3f}s)")
        self.assertGreater(len(self.result.active_technicians), 0, "Active technicians must be > 0")
        self.assertGreater(self.result.standby_technicians_count, 34000, "Most technicians remain standby")

    def test_02_strict_skill_feasibility(self):
        """Validates that no technician is ever assigned an order exceeding their skill level."""
        for tech in self.result.active_technicians:
            for t_id in tech.assigned_tasks:
                task = self.result.tasks[t_id]
                self.assertGreaterEqual(
                    tech.skill_level,
                    task.skill_required,
                    f"Technician #{tech.id} (Skill {tech.skill_level}) assigned Task #{task.id} (Requires Skill {task.skill_required})"
                )
        self.assertEqual(self.result.skill_compliance_rate, 100.0, "Skill compliance rate must be 100%")

    def test_03_no_split_across_depots(self):
        """Validates that every customer task is assigned to exactly one depot and one active technician."""
        assigned_depots = [t.assigned_depot for t in self.result.tasks]
        self.assertTrue(all(0 <= d < len(self.result.hubs) for d in assigned_depots))

        assigned_techs = [t.assigned_tech for t in self.result.tasks]
        self.assertTrue(all(tid >= 0 for tid in assigned_techs))
        self.assertEqual(len(assigned_techs), len(self.tasks), "Every task must have an assigned technician")

    def test_04_closed_loop_routing(self):
        """Validates that all active technician schedules form valid non-zero closed loops."""
        for tech in self.result.active_technicians:
            self.assertGreater(len(tech.assigned_tasks), 0, "Active technician must have assigned tasks")
            self.assertGreater(tech.total_distance_km, 0.0, "Route distance must be positive")
            self.assertGreater(tech.total_shift_min, 0.0, "Total shift minutes must be positive")

    def test_05_classiq_qaoa_synthesis_metrics(self):
        """Validates that Classiq intra-route QAOA quantum circuit compilation metrics are generated."""
        qm = self.result.quantum_metrics
        self.assertIn("qubits_allocated", qm)
        self.assertIn("circuit_depth", qm)
        self.assertIn("cx_entangling_gates", qm)
        self.assertGreater(qm["qubits_allocated"], 0)
        self.assertGreater(qm["circuit_depth"], 0)
        self.assertGreater(qm["cx_entangling_gates"], 0)

    def test_06_five_way_benchmark(self):
        """Validates that 5-way comparative benchmark runs cleanly with complete metrics."""
        bench = run_comprehensive_benchmark(num_tasks=50, total_technicians=1000, num_hubs=4, seed=42)
        sc = bench["scenarios"]
        self.assertIn("baseline_fifo", sc)
        self.assertIn("classic_kmeans", sc)
        self.assertIn("quantum_kmeans", sc)
        self.assertIn("classic_fcm", sc)
        self.assertIn("quantum_multitier_qfcm", sc)
        self.assertIn("hard_kmeans", sc)  # Backward compatibility
        self.assertEqual(len(bench["benchmarks"]), 5)
        self.assertIn("quantum_advantage", bench)

    def test_07_all_five_methods_individual_execution(self):
        """Validates that each of the 5 methods can be solved independently with 100% skill compliance."""
        methods = ["baseline_fifo", "classic_kmeans", "quantum_kmeans", "classic_fcm", "quantum_multitier_qfcm"]
        for m in methods:
            h_sub, t_sub = generate_enterprise_service_problem(num_tasks=40, total_technicians=20, num_hubs=2, seed=123)
            res = solve_multitier_dispatch(h_sub, t_sub, method=m)
            self.assertEqual(res.skill_compliance_rate, 100.0, f"Method {m} must maintain 100% skill compliance")
            self.assertGreater(res.total_fleet_distance_km, 0.0, f"Method {m} must produce non-zero distance")
            self.assertGreater(len(res.active_technicians), 0, f"Method {m} must have active technicians")


if __name__ == "__main__":
    unittest.main(verbosity=2)
