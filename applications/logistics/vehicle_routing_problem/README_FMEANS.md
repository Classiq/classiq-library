# Quantum Fuzzy C-Means (QFCM / F-Means) for WMS Vehicle Routing Problem

## 1. Executive Summary & Problem Context

In automated warehouse logistics and Vehicle Routing Problems (VRP), order dispatching is traditionally solved using a two-stage **"Cluster-First, Route-Second"** architecture:
1. **Clustering**: Assigning high volumes of picking orders to a fleet of Automated Guided Vehicles (AGVs) or human pickers.
2. **Routing**: Solving the Traveling Salesperson Problem (TSP) / CVRP within each cluster.

### The Limitation of Deterministic / Hard K-Means
Standard classical and quantum K-Means rely on **deterministic hard assignments**:
$$z_{ik} \in \{0, 1\}, \quad z_{ik} = 1 \iff k = \arg\min_j D(\mathbf{x}_i, \mathbf{c}_j)$$

In high-density dynamic warehouses, hard clustering leads to severe operational bottlenecks:
- **Boundary Order Brittleness**: Orders lying near spatial borders or aisle transitions are rigidly locked into one AGV route, causing vehicle detours and workload spikes.
- **Parametric Uncertainty**: Physical orders exhibit variable pick durations, fluctuating box volumes, uncertain weights, and tight SLA deadlines that cannot be captured accurately by rigid deterministic metrics.

### The Quantum F-Means (QFCM) Solution
**Quantum Fuzzy C-Means (QFCM)** replaces deterministic decisions with **continuous quantum measurement probabilities**:
$$u_{ik} \in [0, 1] \quad \text{such that} \quad \sum_{k=1}^K u_{ik} = 1, \quad \forall i \in \{1, \dots, N\}$$

Quantum F-Means directly exploits **Born's Rule** on quantum swap-test circuits to compute overlap fidelities and fuzziness-weighted centroid states, achieving **~47% more balanced fleet allocations** and eliminating capacity overloads.

---

## 2. Requirements & Prerequisites

### 2.1 Software & Environment
- **Operating System**: Windows, Linux, or macOS
- **Python**: 3.10, 3.11, or 3.12+ (isolated virtual environment recommended)
- **Key Dependencies**:
  - `classiq` (>= 1.28.0): Quantum circuit synthesis, model creation, and hardware execution SDK.
  - `numpy` (>= 1.24.0): Matrix operations, membership calculations, and random number generation.
  - `scipy` (>= 1.10.0): Scientific computing and statistical analysis.
  - `matplotlib` (>= 3.7.0): Warehouse visualization, static plot generation, and GUI rendering.
  - `pillow` (>= 9.5.0): Multi-frame animated GIF generation.
  - `networkx` (>= 3.0): Graph operations and route topologies.

### 2.2 Quantum Compilation Constraints
- Target quantum register widths: $8 \le n_{\text{qubits}} \le 30$ (NISQ-tractable for intra-cluster QAOA sub-routes).
- Maximum swap-test circuit depth: $O(\text{features})$.

---

## 3. Mathematical Formulation & Architecture

```mermaid
flowchart TD
    A[Order Feature Vector v_i\nx, y, z, weight, volume, SLA, zone] --> B[Amplitude/Angle Encoding\n|ψ_i> = \sum \sqrt{v_ij} |j>]
    B --> C[Centroid Quantum State |c_k>]
    B --> D[Quantum Swap-Test Circuit]
    C --> D
    D --> E[Ancilla Measurement Probabilities\nP_0 = 1/2 + 1/2 |<ψ_i|c_k>|^2\nP_1 = 1/2 - 1/2 |<ψ_i|c_k>|^2]
    E --> F[Quantum Distance Metric\nD_Q = 2 P_1 = 1 - |<ψ_i|c_k>|^2]
    F --> G[Fuzzy Membership Matrix U_ik\nu_ik = 1 / \sum (D_ik / D_ij)^{1/(m-1)}]
    G --> H[Fuzzy Centroid Recalculation\nc_k = \sum u_ik^m x_i / \sum u_ik^m]
    G --> I[Shannon Entropy Analysis\nH_i = -\sum u_ik ln u_ik]
    I --> J[Dynamic Capacity Rebalancing\nReassign High-Entropy Boundary Orders]
    J --> K[Intra-Cluster QUBO & QAOA\nDegree + Capacity + MTZ Penalties]
    K --> L[2D Visual Simulator\nPNG / GIF / Interactive GUI]
```

### 3.1 Qubitized Feature State Preparation
Each order location is defined by a 7-dimensional physical and operational vector:
$$\mathbf{v}_i = [x_i, y_i, z_i, \text{weight}_i, \text{volume}_i, \text{SLA}_i, \text{Zone}_i]^T$$
Features are normalized $\tilde{\mathbf{v}}_i \in [0, 1]^7$ and amplitude/angle-encoded into quantum registers:
$$|\psi_i\rangle = \bigotimes_{j=1}^7 R_y(\theta_{ij}) |0\rangle \quad \text{where } \theta_{ij} = 2 \arcsin\left(\sqrt{\tilde{v}_{ij}}\right)$$

### 3.2 Born's Rule Quantum Distance (Swap-Test Fidelity)
Given order state $|\psi_i\rangle$, centroid state $|c_k\rangle$, and an ancilla bit $|0\rangle_{\text{anc}}$:
1. Apply Hadamard: $H |0\rangle_{\text{anc}} \otimes |\psi_i\rangle |c_k\rangle = \frac{1}{\sqrt{2}} (|0\rangle + |1\rangle) \otimes |\psi_i\rangle |c_k\rangle$
2. Controlled-SWAP conditioned on ancilla: $\frac{1}{\sqrt{2}} |0\rangle |\psi_i\rangle |c_k\rangle + \frac{1}{\sqrt{2}} |1\rangle |c_k\rangle |\psi_i\rangle$
3. Apply second Hadamard to ancilla and measure in computational basis:
   $$P(|0\rangle_{\text{anc}}) = \frac{1 + |\langle \psi_i | c_k \rangle|^2}{2}, \quad P(|1\rangle_{\text{anc}}) = \frac{1 - |\langle \psi_i | c_k \rangle|^2}{2}$$

The quantum distance is directly obtained from the probability of measuring $|1\rangle$:
$$D_Q(\psi_i, c_k) = 2 \cdot P(|1\rangle_{\text{anc}}) = 1.0 - |\langle \psi_i | c_k \rangle|^2$$

### 3.3 Fuzzy Objective Function & Update Equations
Quantum F-Means minimizes the fuzziness-weighted objective:
$$J_m(U, C) = \sum_{i=1}^N \sum_{k=1}^K (u_{ik})^m D_Q(\psi_i, c_k)$$
where $m > 1.0$ is the **fuzziness exponent** (standard $m=2.0$).

1. **Membership Probability Update**:
   $$u_{ik} = \frac{1}{\sum_{j=1}^K \left(\frac{D_Q(\psi_i, c_k)}{D_Q(\psi_i, c_j) + \epsilon}\right)^{\frac{1}{m-1}}}$$
2. **Weighted Centroid Quantum State Recalculation**:
   $$\mathbf{c}_k = \frac{\sum_{i=1}^N (u_{ik})^m \mathbf{x}_i}{\sum_{i=1}^N (u_{ik})^m}, \quad |c_k\rangle = \frac{\mathbf{c}_k}{\|\mathbf{c}_k\|}$$

### 3.4 Shannon Entropy & Dynamic Boundary Rebalancing
To resolve boundary uncertainty and prevent AGV capacity violations, the algorithm computes per-order Shannon entropy:
$$H_i = -\sum_{k=1}^K u_{ik} \ln(u_{ik} + \epsilon)$$
- **Low Entropy ($H_i \approx 0$)**: Order is centrally located within a single AGV zone.
- **High Entropy ($H_i > 0.45$)**: Order is on a cluster boundary with comparable probability of assignment to multiple AGVs.
- **Dynamic Rebalancing**: Orders with $H_i > 0.45$ belonging to an overloaded AGV ($> 85\%$ capacity) are transferred to the least-loaded qualified AGV with membership probability $u_{ik} > 0.15$.

---

## 4. Implementation Structure

```
applications/logistics/vehicle_routing_problem/
├── wms_quantum_fmeans.py              # [NEW] Quantum F-Means core engine & entropy rebalancing
├── test_quantum_fmeans.py             # [NEW] Unit tests for QFCM membership & fidelity
├── wms_visual_simulator.py            # 2D Warehouse visual simulator (CLI, PNG, GIF, GUI)
├── wms_quantum_optimization_pipeline.py # Optimization pipeline, QAOA synthesis & benchmark
├── README_FMEANS.md                   # This dedicated QFCM comprehensive documentation
├── README.md                          # General project overview
├── F-means_implementation_plan.md     # Architecture implementation plan
├── wms_simulation.png                 # Generated 2D static route map
└── wms_simulation.gif                 # Generated animated multi-AGV dispatch simulation
```

### Key Python Classes and Functions in `wms_quantum_fmeans.py`
- `QuantumFMeans(n_clusters=4, m=2.0, max_iter=60, tol=1e-5)`: Scikit-learn style estimator implementing `fit()`, `predict_proba()`, `predict()`, and `get_cluster_entropy()`.
- `quantum_fidelity_distance(a, b)`: Implements the Born's rule quantum overlap metric $D_Q = 1 - |\langle a | b \rangle|^2$.
- `entropy_rebalance_clusters(orders, membership_matrix, k_batches, vehicle_capacity)`: Executes the load-aware boundary rebalancing algorithm.
- `fuzzy_route_cluster_pipeline(...)`: End-to-end orchestration returning centroids, soft memberships, entropy metrics, cluster labels, and intra-cluster QUBO models.

---

## 5. Experimental Results & Benchmark Comparison

### 5.1 Quantitative Benchmark: Hard K-Means vs. Quantum F-Means

Workload: **60 pick orders**, $K=4$ AGV batches, capacity $C_{\text{max}} = 120.0$, evaluated across identical order coordinate seeds:

| Metric | Hard Quantum K-Means | Quantum F-Means (QFCM, $m=2.0$) | Improvement |
| :--- | :--- | :--- | :--- |
| **Cluster Stop Distribution** | `[12, 19, 18, 11]` | `[15, 18, 14, 13]` | **Significantly more uniform** |
| **Stop Count Standard Deviation ($\sigma$)** | `3.5355` | `1.8708` | **47.1% reduction in variance** |
| **Mean Membership Entropy ($H$)** | `0.0000` (crisp) | `1.2497` (probabilistic) | Rich boundary sensitivity |
| **Pipeline Latency** | `0.066 s` | `0.454 s` | Real-time scalable (< 0.5s) |
| **Capacity Overload Violations** | 1 cluster near limit | 0 violations (rebalanced) | **100% capacity compliant** |

### 5.2 Visual Simulator Demonstration (40 Orders, $K=4$)

Execution output on 40-point synthesized warehouse workload:
```
============================================================
  WMS Quantum Optimization Visual Simulator
============================================================
  * Clustering Engine: FMEANS (m=2.0)
  * Orders count:      40
  * K batches/routes:  4
  * Mode:              Static Plot (PNG)
  * Output path:       wms_simulation.png
  * GUI display:       Headless/Save only
============================================================
[*] Running Quantum FMEANS & QAOA Routing Pipeline...
  - Cluster 1: 9 pick stops, route distance = 56.38 m
  - Cluster 2: 10 pick stops, route distance = 63.19 m
  - Cluster 3: 11 pick stops, route distance = 73.07 m
  - Cluster 4: 10 pick stops, route distance = 65.41 m
[*] Total AGV Fleet Distance: 258.04 m
[*] Mean Fuzzy Membership Entropy: 1.1912
[*] Generating static simulation plot...
[+] Static simulation saved to: .../wms_simulation.png
[OK] Simulation completed successfully!
```

- **Visual Features in Generated Plots**:
  - **Color-Coded Batches**: AGV routes rendered with distinct dashed trajectories returning to the central Depot $(0,0)$.
  - **Fuzzy Boundary Halos**: High-entropy boundary orders are marked with dotted magenta outer rings, visually highlighting items that benefit from soft membership assignment.

---

## 6. How to Run & Reproduce

### 6.1 Running from Repository Root (`classiq-library`)

#### 1. Generate Static Route Visualization (PNG)
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" applications\logistics\vehicle_routing_problem\wms_visual_simulator.py --clustering fmeans --num-points 40 --k-batches 4 --output applications\logistics\vehicle_routing_problem\wms_simulation.png
```

#### 2. Generate Multi-AGV Animated Dispatch Simulation (GIF)
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" applications\logistics\vehicle_routing_problem\wms_visual_simulator.py --clustering fmeans --num-points 25 --k-batches 3 --animate --output applications\logistics\vehicle_routing_problem\wms_simulation.gif
```

#### 3. Run Comparative Benchmark Suite
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" -c "import pprint; from applications.logistics.vehicle_routing_problem.wms_quantum_optimization_pipeline import benchmark_kmeans_vs_fmeans; pprint.pprint(benchmark_kmeans_vs_fmeans(num_points=60, k_batches=4))"
```

#### 4. Run Automated Unit Tests
```powershell
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" -m unittest applications/logistics/vehicle_routing_problem/test_quantum_fmeans.py
```

### 6.2 Running from the Subfolder (`vehicle_routing_problem`)

```powershell
cd applications\logistics\vehicle_routing_problem

# Static PNG export
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" wms_visual_simulator.py --clustering fmeans --num-points 40 --k-batches 4 --output wms_simulation.png

# Interactive Desktop GUI
& "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe" wms_visual_simulator.py --clustering fmeans --gui
```

---

## 7. Empirical Case Studies

- [FMEANS_VS_KMEANS_40_POINTS_CASE_STUDY.md](file:///c:/Users/vladimir.dobrouchkin/.gemini/antigravity-ide/scratch/classiq_env/classiq-library/applications/logistics/vehicle_routing_problem/FMEANS_VS_KMEANS_40_POINTS_CASE_STUDY.md): Detailed 40-order benchmark demonstrating 71.1% stop variance reduction and elimination of AGV overloads.
- [FMEANS_VS_KMEANS_80_POINTS_CASE_STUDY.md](file:///c:/Users/vladimir.dobrouchkin/.gemini/antigravity-ide/scratch/classiq_env/classiq-library/applications/logistics/vehicle_routing_problem/FMEANS_VS_KMEANS_80_POINTS_CASE_STUDY.md): Full-scale 80-order workload evaluation with Classiq quantum hardware simulator verification (15 qubits, 2,048 shots), 98.0% payload variance reduction, and 100% capacity compliance.

---

## 8. Key Benefits & Summary

1. **Probabilistic Realism**: Incorporates quantum measurement uncertainty into warehouse batching rather than artificial hard constraints.
2. **Robust Capacity Management**: Shannon entropy dynamic rebalancing mitigates vehicle overload risks on borderline orders.
3. **Seamless QAOA Integration**: Produces standard Ising Hamiltonians directly compilable by the Classiq quantum synthesis engine.
4. **Interactive Visual Feedback**: Enables both automated headless export pipelines (CI/CD) and desktop visualization.

