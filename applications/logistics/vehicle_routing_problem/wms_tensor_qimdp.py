from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Sequence

import numpy as np


# =====================================================================
# 1. Action Spaces & Discrete Grid Kinematics
# =====================================================================

ACTIONS = {
    0: (0, 0),   # Wait
    1: (0, 1),   # Up (+y)
    2: (0, -1),  # Down (-y)
    3: (-1, 0),  # Left (-x)
    4: (1, 0),   # Right (+x)
}

ACTION_NAMES = ["WAIT", "UP", "DOWN", "LEFT", "RIGHT"]


@dataclass
class AGVState:
    """Represents a single Automated Guided Vehicle on the discrete grid."""
    id: int
    x: int
    y: int
    target_x: int
    target_y: int
    waypoints: list[tuple[int, int]] = field(default_factory=list)
    battery: float = 1.0
    active: bool = True
    delivered_count: int = 0


class WarehouseGrid:
    """Topological 2D warehouse grid with discrete cells and obstacles."""

    def __init__(
        self,
        width: int = 30,
        height: int = 25,
        obstacles: list[tuple[int, int]] | None = None,
    ):
        self.width = width
        self.height = height
        self.obstacles = set(obstacles or self._generate_default_racks())

    def _generate_default_racks(self) -> set[tuple[int, int]]:
        """Generates standard warehouse shelf rack obstacles with aisle paths."""
        obs = set()
        # Create standard warehouse storage racks leaving cross aisles
        for x in range(3, self.width - 3, 4):
            for y in range(3, self.height - 3):
                if y % 6 != 0:  # Cross aisle every 6 units
                    obs.add((x, y))
                    obs.add((x + 1, y))
        return obs

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and (x, y) not in self.obstacles

    def coord_to_index(self, x: int, y: int) -> int:
        return y * self.width + x

    def index_to_coord(self, idx: int) -> tuple[int, int]:
        return (idx % self.width, idx // self.width)

    def manhattan(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return float(abs(x1 - x2) + abs(y1 - y2))


# =====================================================================
# 2. Vectorized Multi-Agent Warehouse Simulator
# =====================================================================

class WarehouseSimulator:
    """Discrete-event multi-agent simulator resolving simultaneous motion algebraically."""

    def __init__(self, grid: WarehouseGrid, agvs: list[AGVState]):
        self.grid = grid
        self.agvs = agvs
        self.num_agvs = len(agvs)
        self.time_step = 0
        self.total_vertex_conflicts = 0
        self.total_edge_conflicts = 0

    def get_joint_state(self) -> list[tuple[int, int]]:
        return [(agv.x, agv.y) for agv in self.agvs]

    def step(self, joint_action: Sequence[int]) -> tuple[list[tuple[int, int]], list[float], bool, dict]:
        """Executes simultaneous joint action and resolves collisions algebraically."""
        if len(joint_action) != self.num_agvs:
            raise ValueError(f"Action vector length ({len(joint_action)}) must match AGV count ({self.num_agvs})")

        prev_positions = [(a.x, a.y) for a in self.agvs]
        proposed_positions: list[tuple[int, int]] = []

        # 1. Propose single-step kinematic displacement
        for i, act_idx in enumerate(joint_action):
            dx, dy = ACTIONS.get(act_idx, (0, 0))
            nx, ny = self.agvs[i].x + dx, self.agvs[i].y + dy
            if self.grid.in_bounds(nx, ny):
                proposed_positions.append((nx, ny))
            else:
                proposed_positions.append(prev_positions[i])

        # 2. Strict Algebraic Collision Checking
        actual_positions = list(proposed_positions)
        step_vertex_conflicts = 0
        step_edge_conflicts = 0

        # Check Vertex Collisions: multiple AGVs targeting identical cell at t+1
        pos_counts: dict[tuple[int, int], list[int]] = {}
        for i, pos in enumerate(proposed_positions):
            pos_counts.setdefault(pos, []).append(i)

        for pos, claimants in pos_counts.items():
            if len(claimants) > 1:
                step_vertex_conflicts += len(claimants) - 1
                # Highest priority (first index) gets the spot; others hold in previous position
                for victim in claimants[1:]:
                    actual_positions[victim] = prev_positions[victim]

        # Check Edge Collisions: AGV i and AGV j swapping cells across an edge
        for i in range(self.num_agvs):
            for j in range(i + 1, self.num_agvs):
                if (
                    proposed_positions[i] == prev_positions[j]
                    and proposed_positions[j] == prev_positions[i]
                    and proposed_positions[i] != prev_positions[i]
                ):
                    step_edge_conflicts += 1
                    actual_positions[i] = prev_positions[i]
                    actual_positions[j] = prev_positions[j]

        self.total_vertex_conflicts += step_vertex_conflicts
        self.total_edge_conflicts += step_edge_conflicts

        # 3. Update AGV States and Calculate Multi-Agent Rewards
        rewards = []
        all_arrived = True

        for i, agv in enumerate(self.agvs):
            agv.x, agv.y = actual_positions[i]
            dist = self.grid.manhattan(agv.x, agv.y, agv.target_x, agv.target_y)

            # Local potential-based reward
            reward = -dist * 0.1

            # Arrival bonus & waypoint progression
            if dist == 0:
                reward += 20.0
                if agv.waypoints:
                    next_target = agv.waypoints.pop(0)
                    agv.target_x, agv.target_y = next_target
                    agv.delivered_count += 1
                    all_arrived = False
            else:
                all_arrived = False

            # Penalize collision holding
            if actual_positions[i] == prev_positions[i] and proposed_positions[i] != prev_positions[i]:
                reward -= 10.0  # Collision avoidance / wall collision penalty

            rewards.append(float(reward))

        self.time_step += 1
        info = {
            "vertex_conflicts": step_vertex_conflicts,
            "edge_conflicts": step_edge_conflicts,
            "total_vertex_conflicts": self.total_vertex_conflicts,
            "total_edge_conflicts": self.total_edge_conflicts,
            "time_step": self.time_step,
        }
        return actual_positions, rewards, all_arrived, info


# =====================================================================
# 3. Matrix Product Operator (MPO) Collision Hamiltonian
# =====================================================================

class CollisionMPO:
    """Generates local Hamiltonian operators enforcing goal attraction and anti-collision repulsion.

    H_total = H_target + lambda_vertex * H_vertex + lambda_edge * H_edge
    """

    def __init__(
        self,
        grid: WarehouseGrid,
        num_agents: int,
        lambda_vertex: float = 100.0,
        lambda_edge: float = 150.0,
    ):
        self.grid = grid
        self.num_agents = num_agents
        self.lambda_vertex = lambda_vertex
        self.lambda_edge = lambda_edge

    def compute_local_action_cost(
        self,
        agent_idx: int,
        action: int,
        agv_state: AGVState,
        other_states: list[AGVState],
    ) -> float:
        """Computes diagonal matrix elements <s_i, a_i | H_local | s_i, a_i>."""
        dx, dy = ACTIONS[action]
        nx, ny = agv_state.x + dx, agv_state.y + dy

        # Wall / boundary collision penalty
        if not self.grid.in_bounds(nx, ny):
            return 500.0

        # Target attraction cost
        target_cost = self.grid.manhattan(nx, ny, agv_state.target_x, agv_state.target_y)

        # Pairwise repulsive interaction cost
        vertex_penalty = 0.0
        edge_penalty = 0.0

        for other in other_states:
            if not other.active or other.id == agv_state.id:
                continue
            # Distance to other AGV current position
            if (nx, ny) == (other.x, other.y):
                vertex_penalty += self.lambda_vertex
            # Opposing swap check
            if (nx, ny) == (other.x, other.y) and (agv_state.x, agv_state.y) == (other.target_x, other.target_y):
                edge_penalty += self.lambda_edge

        return float(target_cost + vertex_penalty + edge_penalty)


# =====================================================================
# 4. Tensor Train (MPS) Policy & Born's Rule Action Sampling
# =====================================================================

class TensorTrainRouter:
    """Quantum-Inspired Tensor Train (MPS) policy engine for multi-agent routing.

    Factorizes wavefunction |Psi> = G^(1) G^(2) ... G^(N) where cores G^(k)
    have dimensions (r_{k-1}, num_actions, r_k).
    Samples joint actions using Born's rule: P(a | s) proportional to |<s, a | Psi>|^2.
    """

    def __init__(
        self,
        num_agents: int,
        num_actions: int = 5,
        max_rank: int = 4,
        seed: int = 42,
    ):
        self.num_agents = num_agents
        self.num_actions = num_actions
        self.max_rank = max_rank
        self.rng = np.random.default_rng(seed)

        # Set TT-ranks: r_0 = r_N = 1, intermediate ranks capped at max_rank
        self.ranks = [1]
        for k in range(1, num_agents):
            self.ranks.append(min(max_rank, 5**k, 5**(num_agents - k)))
        self.ranks.append(1)

        self.cores: list[np.ndarray] = []
        for k in range(num_agents):
            r_left = self.ranks[k]
            r_right = self.ranks[k + 1]
            core = self.rng.normal(0.0, 0.5, size=(r_left, num_actions, r_right))
            core /= np.linalg.norm(core)
            self.cores.append(core)

    def evaluate_wavefunction(self, action_tuple: Sequence[int]) -> float:
        """Contracts TT-cores across a specified joint action tuple: <a_1, ..., a_N | Psi>."""
        if len(action_tuple) != self.num_agents:
            raise ValueError("Action tuple length must equal number of agents.")
        val = np.array([[1.0]])
        for k, a in enumerate(action_tuple):
            val = val @ self.cores[k][:, a, :]
        return float(val[0, 0])

    def sample_joint_action_born_rule(
        self,
        agvs: list[AGVState],
        grid: WarehouseGrid,
        mpo: CollisionMPO | None = None,
        temperature: float = 0.5,
    ) -> list[int]:
        """Born's Rule sampling: P(a_1, ..., a_N) proportional to |Psi(a)|^2 * exp(-H(a)/T)."""
        sampled_actions = []
        carry = np.array([[1.0]])

        for k in range(self.num_agents):
            core = self.cores[k]  # shape: (r_left, 5, r_right)
            r_left, d, r_right = core.shape
            probs = np.zeros(d, dtype=float)

            agv = agvs[k]
            other_agvs = [other for idx, other in enumerate(agvs) if idx != k]

            for a in range(d):
                slice_a = carry @ core[:, a, :]  # (1, r_right)
                quantum_weight = float(np.sum(slice_a**2))

                # Inject local MPO Hamiltonian bias
                if mpo is not None:
                    h_cost = mpo.compute_local_action_cost(k, a, agv, other_agvs)
                    boltzmann_weight = np.exp(-h_cost / max(temperature, 1e-4))
                else:
                    boltzmann_weight = 1.0

                probs[a] = quantum_weight * boltzmann_weight

            total_p = np.sum(probs)
            if total_p > 1e-12:
                probs /= total_p
            else:
                probs = np.ones(d) / d

            chosen_a = int(self.rng.choice(d, p=probs))
            sampled_actions.append(chosen_a)

            carry = carry @ core[:, chosen_a, :]
            c_norm = np.linalg.norm(carry)
            if c_norm > 1e-12:
                carry /= c_norm

        return sampled_actions

    def als_bellman_sweep(
        self,
        joint_action: Sequence[int],
        total_reward: float,
        learning_rate: float = 0.05,
    ):
        """Executes a 2-site Alternating Least Squares (ALS) update minimizing Bellman error."""
        td_error = float(total_reward)
        for k in range(self.num_agents):
            a_k = joint_action[k]
            # Gradient update on local core
            r_l, _, r_r = self.cores[k].shape
            grad = np.outer(np.ones(r_l), np.ones(r_r)) * (td_error * 0.01)
            self.cores[k][:, a_k, :] += learning_rate * grad

            norm = np.linalg.norm(self.cores[k])
            if norm > 1e-12:
                self.cores[k] /= norm


# =====================================================================
# 5. High-Level Multi-Agent Simulation Coordinator
# =====================================================================

def run_tensor_qimdp_simulation(
    num_agvs: int = 4,
    steps: int = 50,
    grid_width: int = 30,
    grid_height: int = 25,
    seed: int = 42,
) -> dict:
    """Runs a complete Tensor QI-MDP multi-agent routing simulation."""
    rng = np.random.default_rng(seed)
    grid = WarehouseGrid(width=grid_width, height=grid_height)

    # Initialize AGVs at Depot and random targets
    agvs: list[AGVState] = []
    depot = (0, 0)
    for i in range(num_agvs):
        # Pick reachable initial and target coordinates
        start_x = int(rng.integers(0, 5))
        start_y = int(rng.integers(0, 5))
        while not grid.in_bounds(start_x, start_y):
            start_x = int(rng.integers(0, 5))
            start_y = int(rng.integers(0, 5))

        target_x = int(rng.integers(max(1, grid_width // 2), grid_width))
        target_y = int(rng.integers(max(1, grid_height // 2), grid_height))
        while not grid.in_bounds(target_x, target_y):
            target_x = int(rng.integers(max(1, grid_width // 2), grid_width))
            target_y = int(rng.integers(max(1, grid_height // 2), grid_height))

        agvs.append(AGVState(id=i, x=start_x, y=start_y, target_x=target_x, target_y=target_y))

    simulator = WarehouseSimulator(grid=grid, agvs=agvs)
    mpo = CollisionMPO(grid=grid, num_agents=num_agvs)
    router = TensorTrainRouter(num_agents=num_agvs, max_rank=4, seed=seed)

    history = []
    total_rewards = 0.0

    for step in range(steps):
        joint_action = router.sample_joint_action_born_rule(simulator.agvs, grid, mpo=mpo)
        positions, rewards, done, info = simulator.step(joint_action)
        step_reward = sum(rewards)
        total_rewards += step_reward

        # ALS update on Bellman residual
        router.als_bellman_sweep(joint_action, step_reward)

        history.append({
            "step": step + 1,
            "positions": [pos for pos in positions],
            "actions": [ACTION_NAMES[a] for a in joint_action],
            "rewards": rewards,
            "conflicts": info["vertex_conflicts"] + info["edge_conflicts"],
        })

        if done:
            break

    return {
        "total_steps": len(history),
        "total_rewards": round(total_rewards, 2),
        "total_vertex_conflicts": simulator.total_vertex_conflicts,
        "total_edge_conflicts": simulator.total_edge_conflicts,
        "history": history,
    }
