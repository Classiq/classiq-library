# Quantum-Inspired Markov Decision Process (QI-MDP) Multi-Agent Warehouse Simulator using Tensor Trains (MPS / MPO)

## 1. Executive Overview

In automated fulfillment centers, multi-agent automated guided vehicles (AGVs) must execute high-density routing without collisions. While macroscopic clustering algorithms (such as **Quantum Fuzzy C-Means**) partition pick orders into balanced batches, microscopic path execution requires resolving the **Multi-Agent Path Finding (MAPF)** problem on a shared 2D grid graph $G = (V, E)$.

The joint state space of $N$ AGVs scales exponentially:
$$|\mathcal{S}| = |V|^N \quad (e.g., 750^{10} \approx 5.63 \times 10^{28} \text{ states})$$

**Tensor QI-MDP** addresses this curse of dimensionality by factorizing the joint multi-agent value/policy wavefunction $|\Psi\rangle$ into a **Tensor Train (TT) / Matrix Product State (MPS)**:
$$\Psi(s_1, \dots, s_N) \approx \sum_{\alpha_0, \dots, \alpha_N} G^{(1)}_{\alpha_0, s_1, \alpha_1} G^{(2)}_{\alpha_1, s_2, \alpha_2} \dots G^{(N)}_{\alpha_{N-1}, s_N, \alpha_N}$$

By combining **Matrix Product Operator (MPO)** collision Hamiltonians with **Alternating Least Squares (ALS) / 2-site DMRG sweeps**, the computational complexity collapses from $\mathcal{O}(d^N)$ to strictly linear scaling in fleet size $\mathcal{O}(N \cdot d \cdot r^3)$, with collision-free joint actions sampled directly via **Born's Rule**.

---

## 2. Mathematical Formalism & Architecture

```mermaid
flowchart TD
    A[Warehouse Grid G = (V, E)\nDimensions W x H, Rack Obstacles] --> B[Multi-AGV Fleet States\ns = (s_1, ..., s_N)]
    B --> C[Matrix Product Operator (MPO) Hamiltonian\nH = H_target + \lambda_v H_vertex + \lambda_e H_edge]
    C --> D[Tensor Train Wavefunction |Psi>\nMPS Cores G^(1) ... G^(N)]
    D --> E[Alternating Least Squares (ALS) Sweep\nBellman Error Minimization]
    E --> F[Born's Rule Sampling\nP(a | s) \propto |<s, a | Psi>|^2 * exp(-H/T)]
    F --> G[Vectorized Simultaneous Step Resolution\nVertex & Edge Collision Clamping]
    G --> H[Collision-Free AGV Dispatch\nPNG / GIF / Interactive Visualizer]
```

### 2.1 Discrete Kinematics & Constraints
Each AGV $i \in \{1, \dots, N\}$ selects from 5 discrete spatial actions:
$$\mathcal{A}_i = \{\text{Wait}=(0,0),\, \text{Up}=(0,1),\, \text{Down}=(0,-1),\, \text{Left}=(-1,0),\, \text{Right}=(1,0)\}$$
Joint action $\mathbf{a} \in \mathcal{A} = \prod_i \mathcal{A}_i$ ($|\mathcal{A}| = 5^N$).

Strict physical constraints:
- **Vertex Collision**: $\sum_{i < j} \mathbf{1}(s_i^{(t+1)} = s_j^{(t+1)}) \cdot \infty$
- **Edge Swap Collision**: $\sum_{i < j} \mathbf{1}(s_i^{(t+1)} = s_j^{(t)} \land s_j^{(t+1)} = s_i^{(t)}) \cdot \infty$

### 2.2 Tensor Train Wavefunction & Entanglement Rank
The joint policy amplitude is factorized into $N$ local 3rd-order tensors:
- Core dimensions: $G^{(k)} \in \mathbb{R}^{r_{k-1} \times 5 \times r_k}$.
- Boundary conditions: $r_0 = r_N = 1$.
- Maximum entanglement rank: $r = \max_k r_k$ (bounded multi-agent correlation).

### 2.3 MPO Collision Hamiltonian
The interaction Hamiltonian $\hat{H}$ penalizes wall collisions, distance to targets, and inter-agent proximity:
$$\hat{H} = \hat{H}_{\text{target}} + \lambda_v \hat{H}_{\text{vertex}} + \lambda_e \hat{H}_{\text{edge}}$$

### 2.4 Born's Rule Action Sampling
Joint actions are sampled sequentially from marginal probabilities:
$$P(a_k | a_{<k}) \propto \|\text{carry} \cdot G^{(k)}[:, a_k, :]\|^2_F \cdot \exp\left(-\frac{\hat{H}(a_k)}{T}\right)$$

---

## 3. Comparative Evaluation (Tensor QI-MDP vs. CBS vs. MAPPO)

| Dimension | Tensor QI-MDP (MPS / TT) | Conflict-Based Search (CBS) | Multi-Agent PPO (MAPPO) |
| :--- | :--- | :--- | :--- |
| **Computational Complexity** | $\mathcal{O}(N \cdot d \cdot r^3)$ | $\mathcal{O}(2^C \cdot N \cdot |V| \log |V|)$ | $\mathcal{O}(N \cdot L \cdot d_{\text{nn}}^2)$ |
| **Collision Guarantee** | **Strict Hard Operator**: Divergent MPO penalty | **Strict Search Guarantee**: Resolves conflict tree | **Soft Empirical Penalty**: Frequent corner collisions |
| **Scalability ($N \to \infty$)** | **Linear $\mathcal{O}(N)$** for bounded rank $r$ | **Exponential Explosion** in dense traffic | **Polynomial**, but high gradient variance |
| **Parametric Stochasticity** | **Native**: Born's rule integrates probabilistic weights | **Fragile**: Requires replanning on variance | **Good**: Explores stochastic environments |
| **Optimal Use Case** | Dense warehouse fleets with aisle bottleneck corridors | Low-density fleets with static targets | Continuous navigation with soft margins |

---

## 4. Module Structure

```
applications/logistics/vehicle_routing_problem/
├── wms_tensor_qimdp.py           # Core Grid, Simulator, MPO, and TensorTrainRouter
├── test_tensor_qimdp.py          # Unit & integration tests for Tensor QI-MDP
├── wms_visual_simulator.py       # Updated with --tensor-routing and discrete grid plotting
├── QI-MDP_tensorprompt.md        # Mathematical prompt specification
├── Tensor_implementation.md      # Engineering implementation plan
├── wms_tensor_simulation.png     # Generated discrete multi-AGV collision-free grid plot
└── README_TENSOR_QIMDP.md        # This comprehensive documentation
```

---

## 5. Execution & Reproduction Guide

### 5.1 Run Automated Unit Tests (100% Pass Rate)
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" -m unittest applications/logistics/vehicle_routing_problem/test_tensor_qimdp.py
```
*Output:*
```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.073s

OK
```

### 5.2 Run Tensor Multi-AGV Simulation (Static Grid Plot)
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" applications\logistics\vehicle_routing_problem\wms_visual_simulator.py --tensor-routing --tensor-steps 35 --num-agvs 4 --output applications\logistics\vehicle_routing_problem\wms_tensor_simulation.png
```
*Execution Metrics:*
- **Fleet Size**: 4 AGVs traversing warehouse storage racks and cross aisles.
- **Discrete Steps**: 35 simultaneous steps.
- **Vertex Conflicts Resolved**: 0.
- **Edge Swaps Resolved**: 0.
- **Saved Output**: [wms_tensor_simulation.png](file:///c:/Users/vladimir.dobrouchkin/.gemini/antigravity-ide/scratch/classiq_env/classiq-library/applications/logistics/vehicle_routing_problem/wms_tensor_simulation.png).

### 5.3 Interactive Desktop Window Mode
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" applications\logistics\vehicle_routing_problem\wms_visual_simulator.py --tensor-routing --tensor-steps 40 --num-agvs 4 --gui
```
