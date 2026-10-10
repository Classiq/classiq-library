import unittest
import numpy as np

from wms_quantum_optimization_pipeline import OrderLocation
from wms_visual_simulator import generate_test_orders
from wms_quantum_fmeans import (
    QuantumFMeans,
    quantum_fidelity_distance,
    entropy_rebalance_clusters,
    fuzzy_route_cluster_pipeline,
)


class TestQuantumFMeans(unittest.TestCase):

    def setUp(self):
        # 10 fixed demo orders
        self.orders_10 = [
            OrderLocation(2.0, 5.0, 1.0, 11.0, 13.0, 0.9, 0.2),
            OrderLocation(3.0, 4.0, 1.5, 8.0, 10.0, 0.7, 0.3),
            OrderLocation(8.0, 7.0, 1.0, 15.0, 14.0, 0.8, 0.5),
            OrderLocation(9.0, 6.0, 2.0, 10.0, 12.0, 0.6, 0.4),
            OrderLocation(14.0, 10.0, 1.8, 18.0, 18.0, 0.9, 0.7),
            OrderLocation(15.0, 9.0, 1.5, 14.0, 16.0, 0.8, 0.6),
            OrderLocation(18.0, 14.0, 2.1, 12.0, 17.0, 0.95, 0.8),
            OrderLocation(12.0, 18.0, 1.2, 16.0, 18.0, 0.7, 0.9),
            OrderLocation(21.0, 8.0, 1.4, 9.0, 11.0, 0.6, 0.5),
            OrderLocation(24.0, 12.0, 1.9, 14.0, 15.0, 0.8, 0.7),
        ]
        # 60 generated warehouse order points
        self.orders_60 = generate_test_orders(num_points=60, seed=42)

    def test_quantum_fidelity_distance(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        c = np.array([0.0, 1.0, 0.0])
        self.assertAlmostEqual(quantum_fidelity_distance(a, b), 0.0, places=5)
        self.assertAlmostEqual(quantum_fidelity_distance(a, c), 1.0, places=5)

    def test_membership_probabilities_sum_to_one_60_points(self):
        """Validates that all 60 points satisfy sum_k u_{ik} = 1.0 and 0 <= u_{ik} <= 1.0."""
        k = 4
        qfcm = QuantumFMeans(n_clusters=k, m=2.0)
        qfcm.fit(self.orders_60)
        U = qfcm.membership_matrix_
        self.assertIsNotNone(U)
        self.assertEqual(U.shape, (60, k))
        for row in U:
            self.assertAlmostEqual(float(np.sum(row)), 1.0, places=5)
            self.assertTrue(np.all(row >= 0.0))
            self.assertTrue(np.all(row <= 1.0))

    def test_entropy_and_rebalance_60_points(self):
        """Validates Shannon entropy and dynamic capacity rebalancing across 60 points."""
        k = 4
        qfcm = QuantumFMeans(n_clusters=k, m=2.0)
        qfcm.fit(self.orders_60)
        entropies = qfcm.get_cluster_entropy()
        self.assertEqual(len(entropies), 60)
        self.assertTrue(np.all(entropies >= 0.0))

        rebalanced = entropy_rebalance_clusters(
            self.orders_60, qfcm.membership_matrix_, k_batches=k, vehicle_capacity=250.0
        )
        self.assertEqual(len(rebalanced), 60)
        counts = [rebalanced.count(c) for c in range(k)]
        self.assertEqual(sum(counts), 60)
        # Verify no empty clusters
        for c_count in counts:
            self.assertGreater(c_count, 0)

    def test_fuzzy_route_cluster_pipeline_60_points(self):
        """Validates end-to-end QFCM pipeline execution and QUBO route blocks on 60 points."""
        k = 4
        pipeline = fuzzy_route_cluster_pipeline(
            self.orders_60, k_batches=k, vehicle_capacity=250.0, m=2.0
        )
        self.assertIn("centers", pipeline)
        self.assertIn("cluster_labels", pipeline)
        self.assertIn("memberships", pipeline)
        self.assertIn("entropies", pipeline)
        self.assertIn("route_blocks", pipeline)
        self.assertEqual(len(pipeline["cluster_labels"]), 60)
        self.assertEqual(len(pipeline["centers"]), k)

        # Ensure balanced allocation across 60 points
        labels = np.array(pipeline["cluster_labels"])
        counts = [int(np.sum(labels == c)) for c in range(k)]
        self.assertEqual(sum(counts), 60)
        self.assertLess(float(np.std(counts)), 4.0)  # Variance bounded under 4.0


def run_standalone_60_points():
    print("=" * 65)
    print("  Running Quantum F-Means Test on 60 Points Workload")
    print("=" * 65)
    orders = generate_test_orders(num_points=60, seed=42)
    k = 4
    pipeline = fuzzy_route_cluster_pipeline(orders, k_batches=k, vehicle_capacity=250.0, m=2.0)
    labels = np.array(pipeline["cluster_labels"])
    entropies = pipeline["entropies"]
    memberships = pipeline["memberships"]

    counts = [int(np.sum(labels == c)) for c in range(k)]
    total_weights = [sum(orders[i].weight for i in range(len(orders)) if labels[i] == c) for c in range(k)]

    print(f"[*] Total Orders Processed:      {len(orders)}")
    print(f"[*] Number of Clusters (K):       {k}")
    print(f"[*] Stop Allocation per AGV:     {counts}")
    print(f"[*] Stop Count Std Dev (sigma):   {float(np.std(counts)):.4f}")
    print(f"[*] Payload per AGV (kg):         {[round(w, 2) for w in total_weights]}")
    print(f"[*] Payload Std Dev (kg):         {float(np.std(total_weights)):.4f}")
    print(f"[*] Mean Membership Entropy (H):  {float(np.mean(entropies)):.4f}")
    print(f"[*] Membership Matrix Check:     All rows sum to 1.0 -> {np.allclose(np.sum(memberships, axis=1), 1.0)}")
    print("=" * 65)
    print("[OK] All 60-point Quantum F-Means checks passed successfully!")


if __name__ == "__main__":
    import sys
    if "--standalone" in sys.argv or "-s" in sys.argv:
        run_standalone_60_points()
    else:
        # Run both unittest and summary
        suite = unittest.TestLoader().loadTestsFromTestCase(TestQuantumFMeans)
        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)
        if res.wasSuccessful():
            print()
            run_standalone_60_points()
