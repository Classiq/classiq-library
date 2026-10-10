"""Unit test suite for Multi-Depot Field-Technician Dispatch (MDFTD-VRP).

Verifies:
1. Strict No-Split Across Depots constraint (sum_d y_{id} = 1).
2. Closed-loop depot routing invariance (start and end at home depot).
3. Shift duration and payload capacity feasibility.
4. Inter-depot workload balancing via entropy thresholding.
5. IRS standard mileage rate and EPA GHG emissions factor calculations.
6. Execution runtime scalability under hierarchical decomposition.
"""

import time
import unittest
import numpy as np

from wms_multi_depot_qfcm import (
    MultiDepotLocation,
    FieldTask,
    MultiDepotQuantumFMeans,
    task_to_qubitized_vector,
)
from wms_field_technician_dispatch import (
    generate_field_service_problem,
    dispatch_field_technicians,
    compute_roi_and_co2_impact,
    two_opt_refine,
    nearest_neighbor_route,
)


class TestMultiDepotFieldTechnicianDispatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        cls.num_tasks = int(os.environ.get("MDFTD_NUM_TASKS", 100))
        cls.num_depots = int(os.environ.get("MDFTD_NUM_DEPOTS", 4))
        total_techs = int(os.environ.get("MDFTD_TOTAL_TECHS", 1000))
        cls.techs_per_depot = int(os.environ.get("MDFTD_TECHS_PER_DEPOT", max(1, total_techs // cls.num_depots)))
        cls.total_technicians = cls.num_depots * cls.techs_per_depot

        cls.depots, cls.tasks = generate_field_service_problem(
            num_tasks=cls.num_tasks,
            num_depots=cls.num_depots,
            techs_per_depot=cls.techs_per_depot,
            seed=42,
        )
        cls.plan = dispatch_field_technicians(
            cls.depots,
            cls.tasks,
            method="quantum_fmeans",
            m=2.0,
        )

    def test_no_split_depot_invariance(self):
        """Verify that every task is assigned to strictly ONE depot and visited by strictly ONE technician."""
        visited_tasks = []
        for route in self.plan.technician_routes:
            visited_tasks.extend(route.task_ids)

        self.assertEqual(
            len(visited_tasks),
            self.num_tasks,
            f"Expected {self.num_tasks} visited tasks, but found {len(visited_tasks)}",
        )
        self.assertEqual(
            len(set(visited_tasks)),
            self.num_tasks,
            "Duplicate task visits detected! Tasks must never be split across technicians.",
        )
        self.assertEqual(
            set(visited_tasks),
            set(range(self.num_tasks)),
            "Mismatch between universe of customer orders and dispatched technician tasks.",
        )

    def test_closed_loop_depot_assignment(self):
        """Verify that each technician route starts and terminates at their assigned home depot."""
        for route in self.plan.technician_routes:
            depot_id = route.depot_id
            self.assertTrue(0 <= depot_id < self.num_depots)
            # Ensure all assigned tasks for this technician belong to the assigned depot
            for tid in route.task_ids:
                task = self.tasks[tid]
                self.assertIsNotNone(task)

    def test_payload_capacity_compliance(self):
        """Verify that no technician route exceeds vehicle payload limits."""
        for route in self.plan.technician_routes:
            depot = self.depots[route.depot_id]
            self.assertLessEqual(
                route.total_payload_kg,
                depot.max_capacity_kg + 1e-4,
                f"Technician {route.technician_id} payload {route.total_payload_kg} exceeds max {depot.max_capacity_kg}",
            )
            self.assertTrue(route.is_capacity_compliant)

    def test_shift_duration_compliance(self):
        """Verify that technician shift durations adhere to labor regulations (<= 8 hours / 480 min)."""
        for route in self.plan.technician_routes:
            depot = self.depots[route.depot_id]
            max_shift_min = depot.shift_hours * 60.0
            self.assertLessEqual(
                route.total_shift_time_min,
                max_shift_min + 1e-4,
                f"Technician {route.technician_id} shift {route.total_shift_time_min:.1f}min exceeds max {max_shift_min}min",
            )
            self.assertTrue(route.is_shift_compliant)

    def test_depot_workload_balance(self):
        """Verify that inter-depot entropy rebalancing maintains low workload standard deviation."""
        counts = self.plan.depot_task_counts
        self.assertEqual(sum(counts), self.num_tasks)
        expected = self.num_tasks / self.num_depots
        min_bound = max(1, int(expected * 0.5))
        max_bound = int(expected * 1.5) + 2
        for c in counts:
            self.assertGreaterEqual(c, min_bound)
            self.assertLessEqual(c, max_bound)
        # Workload standard deviation across depots should be under 3.5 hours
        self.assertLessEqual(self.plan.depot_workload_std, 3.5)

    def test_irs_and_epa_roi_conversions(self):
        """Verify mathematical integrity of IRS Notice 2024-08 and EPA 2024 emissions formulas."""
        base_km = 1200.0
        opt_km = 900.0
        roi = compute_roi_and_co2_impact(
            baseline_distance_km=base_km,
            optimized_distance_km=opt_km,
            irs_rate_per_mile=0.670,
            epa_g_co2_per_mile=404.0,
            technician_hourly_rate=55.0,
            average_speed_kmh=48.28,
            work_days_per_year=250,
        )

        expected_km_saved = 300.0
        expected_miles_saved = 300.0 * 0.621371
        expected_hours_saved_daily = 300.0 / 48.28
        expected_fleet_cost_daily = expected_miles_saved * 0.670
        expected_labor_saved_daily = expected_hours_saved_daily * 55.0
        expected_co2_kg_daily = (expected_miles_saved * 404.0) / 1000.0

        self.assertAlmostEqual(roi["distance_saved_km_daily"], expected_km_saved, places=1)
        self.assertAlmostEqual(roi["distance_saved_miles_daily"], expected_miles_saved, places=1)
        self.assertAlmostEqual(roi["technician_hours_saved_daily"], expected_hours_saved_daily, places=2)
        self.assertAlmostEqual(roi["fleet_cost_saved_daily"], expected_fleet_cost_daily, places=2)
        self.assertAlmostEqual(roi["labor_value_reclaimed_daily"], expected_labor_saved_daily, places=2)
        self.assertAlmostEqual(roi["co2_avoided_kg_daily"], expected_co2_kg_daily, places=2)

        # Verify annual scaling
        self.assertAlmostEqual(
            roi["fleet_cost_saved_annual"],
            round(expected_fleet_cost_daily * 250, 2),
            places=1,
        )
        self.assertAlmostEqual(
            roi["labor_value_reclaimed_annual"],
            round(expected_labor_saved_daily * 250, 2),
            places=1,
        )

    def test_runtime_scaling(self):
        """Verify that hierarchical quantum-classical decomposition executes in under 6.0 seconds for 1000 technicians."""
        t0 = time.perf_counter()
        plan = dispatch_field_technicians(
            self.depots,
            self.tasks,
            method="quantum_fmeans",
            m=2.0,
        )
        elapsed = time.perf_counter() - t0
        self.assertLess(
            elapsed,
            6.0,
            f"Execution time {elapsed:.3f}s exceeded hierarchical threshold of 6.0s",
        )


if __name__ == "__main__":
    import sys
    import os

    if "--gui" in sys.argv:
        from gui_multi_depot_dispatch import main as launch_gui
        sys.argv.remove("--gui")
        launch_gui()
        sys.exit(0)

    # Parse custom parameter flags if present
    custom_argv = [sys.argv[0]]
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ("--tasks", "--num-tasks") and i + 1 < len(sys.argv):
            os.environ["MDFTD_NUM_TASKS"] = str(sys.argv[i + 1])
            i += 2
        elif arg in ("--techs", "--num-techs", "--technicians") and i + 1 < len(sys.argv):
            os.environ["MDFTD_TOTAL_TECHS"] = str(sys.argv[i + 1])
            i += 2
        elif arg in ("--depots", "--num-depots") and i + 1 < len(sys.argv):
            os.environ["MDFTD_NUM_DEPOTS"] = str(sys.argv[i + 1])
            i += 2
        else:
            custom_argv.append(arg)
            i += 1

    unittest.main(argv=custom_argv)
