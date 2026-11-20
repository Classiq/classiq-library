import unittest
import numpy as np

from wms_tensor_qimdp import (
    WarehouseGrid,
    WarehouseSimulator,
    AGVState,
    CollisionMPO,
    TensorTrainRouter,
    run_tensor_qimdp_simulation,
    ACTIONS,
)


class TestTensorQIMDP(unittest.TestCase):

    def setUp(self):
        self.grid = WarehouseGrid(width=10, height=10, obstacles=[(3, 3), (3, 4)])

    def test_grid_boundaries_and_obstacles(self):
        self.assertTrue(self.grid.in_bounds(0, 0))
        self.assertTrue(self.grid.in_bounds(9, 9))
        self.assertFalse(self.grid.in_bounds(-1, 0))
        self.assertFalse(self.grid.in_bounds(10, 5))
        self.assertFalse(self.grid.in_bounds(3, 3))  # Obstacle
        self.assertFalse(self.grid.in_bounds(3, 4))  # Obstacle

    def test_coord_index_conversion(self):
        x, y = 4, 7
        idx = self.grid.coord_to_index(x, y)
        self.assertEqual(idx, 7 * 10 + 4)
        conv_x, conv_y = self.grid.index_to_coord(idx)
        self.assertEqual((conv_x, conv_y), (x, y))

    def test_vertex_conflict_resolution(self):
        # Two AGVs starting adjacent and attempting to step into the SAME cell (1, 1)
        agv0 = AGVState(id=0, x=1, y=0, target_x=1, target_y=5)
        agv1 = AGVState(id=1, x=0, y=1, target_x=5, target_y=1)
        sim = WarehouseSimulator(grid=self.grid, agvs=[agv0, agv1])

        # Action for agv0: UP (to 1, 1). Action for agv1: RIGHT (to 1, 1)
        actual_pos, rewards, done, info = sim.step([1, 4])

        self.assertEqual(info["vertex_conflicts"], 1)
        # One AGV got the cell, the other stayed in previous position
        self.assertNotEqual(actual_pos[0], actual_pos[1])
        self.assertTrue(actual_pos[0] == (1, 1) or actual_pos[1] == (1, 1))

    def test_edge_swap_conflict_resolution(self):
        # Two AGVs swapping cells: AGV0 at (1, 1), AGV1 at (1, 2)
        agv0 = AGVState(id=0, x=1, y=1, target_x=1, target_y=5)
        agv1 = AGVState(id=1, x=1, y=2, target_x=1, target_y=0)
        sim = WarehouseSimulator(grid=self.grid, agvs=[agv0, agv1])

        # Action for agv0: UP (towards 1, 2). Action for agv1: DOWN (towards 1, 1)
        actual_pos, rewards, done, info = sim.step([1, 2])

        self.assertEqual(info["edge_conflicts"], 1)
        # Both should be held in original positions
        self.assertEqual(actual_pos[0], (1, 1))
        self.assertEqual(actual_pos[1], (1, 2))

    def test_tensor_train_router_structure(self):
        router = TensorTrainRouter(num_agents=4, max_rank=3)
        self.assertEqual(len(router.cores), 4)
        self.assertEqual(router.cores[0].shape[0], 1)   # r_0 = 1
        self.assertEqual(router.cores[-1].shape[2], 1)  # r_N = 1

        # Wavefunction evaluation produces a scalar
        val = router.evaluate_wavefunction([0, 1, 2, 3])
        self.assertIsInstance(val, float)

    def test_born_rule_sampling_and_als_sweep(self):
        agvs = [
            AGVState(id=0, x=0, y=0, target_x=5, target_y=5),
            AGVState(id=1, x=9, y=9, target_x=2, target_y=2),
        ]
        router = TensorTrainRouter(num_agents=2, max_rank=2)
        mpo = CollisionMPO(grid=self.grid, num_agents=2)

        actions = router.sample_joint_action_born_rule(agvs, self.grid, mpo=mpo)
        self.assertEqual(len(actions), 2)
        for a in actions:
            self.assertIn(a, [0, 1, 2, 3, 4])

        # ALS sweep does not error and updates cores
        core0_before = router.cores[0].copy()
        router.als_bellman_sweep(actions, total_reward=5.0)
        self.assertFalse(np.allclose(core0_before, router.cores[0]))

    def test_full_simulation_run(self):
        res = run_tensor_qimdp_simulation(num_agvs=3, steps=10, grid_width=15, grid_height=15)
        self.assertEqual(res["total_steps"], 10)
        self.assertIn("history", res)
        self.assertIn("total_rewards", res)


if __name__ == "__main__":
    unittest.main()
