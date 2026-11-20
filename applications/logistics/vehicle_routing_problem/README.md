# Warehouse Management System (WMS) Quantum Vehicle Routing Problem (VRP) & Visual Simulator

## 1. Project Overview

This project implements a hybrid **Quantum-Classical Warehouse Management System (WMS)** optimization pipeline and visual simulator for the **Capacitated Vehicle Routing Problem (CVRP)** and **Batch Picking / Automated Guided Vehicle (AGV) Routing**.

The system addresses large-scale warehouse order fulfilment by decomposing the combinatorial NP-hard VRP problem into two coordinated stages:
1. **Quantum Fuzzy C-Means (QFCM / F-Means) & K-Means Clustering**: Partitions multi-dimensional warehouse pick orders ($x, y, z$, weight, volume, SLA urgency, zone class) into $K$ balanced batches using continuous membership probabilities $u_{ik} \in [0, 1]$ and quantum state fidelity derived from Born's rule measurement probabilities.
2. **Entropy-Based Dynamic Capacity Rebalancing**: Identifies boundary orders situated across cluster transitions via Shannon entropy $H_i = -\sum_k u_{ik} \ln u_{ik}$ and redistributes them to prevent AGV overload.
3. **QAOA & QUBO Route Optimization**: Formulates intra-cluster AGV pick sequences as a Quadratic Unconstrained Binary Optimization (QUBO) problem with Miller-Tucker-Zemlin (MTZ) subtour elimination constraints and maps them to an Ising Hamiltonian for Quantum Approximate Optimization Algorithm (QAOA) execution.
4. **Visual Simulator**: A high-resolution 2D warehouse simulator supporting static plot exports, animated multi-AGV GIF simulations, boundary halo indicators, and real-time interactive desktop GUI navigation.

---

## 2. Architecture & Mathematical Formulation

```mermaid
flowchart TD
    A[Raw Warehouse Orders\nx, y, z, weight, volume, SLA, zone] --> B[Qubitized Feature Encoding]
    B --> C[Quantum Swap-Test Circuit\nAncilla Measurement Probabilities]
    C --> D[Quantum Fidelity Metric\nD_Q = 1 - |<ψ|c>|^2 = 2 P_1]
    D --> E[Fuzzy Membership Matrix U_ik\nwith Fuzziness Parameter m]
    E --> F[Shannon Entropy Calculation\n& Dynamic AGV Load Rebalancing]
    F --> G[K Balanced Batches / AGV Allocations]
    G --> H[QUBO Intra-Cluster Formulation\nDegree + Capacity + MTZ Penalties]
    H --> I[Ising Hamiltonian Mapping\nx -> (1-z)/2]
    I --> J[Classiq QAOA Synthesis\nParameterized Ansatz & Circuit Execution]
    J --> K[AGV Dispatch Routes]
    K --> L[WMS Visual Simulator\nPNG / GIF / Interactive GUI]
```

### 2.1 Feature Vector Representation
Each order is characterized by a 7-dimensional physical and operational vector:
$$\mathbf{v}_i = [x_i, y_i, z_i, w_i, v_i, \text{SLA}_i, \text{Zone}_i]^T$$
Features are normalized and amplitude/angle-encoded into quantum registers:
$$|\psi_i\rangle = \sum_{j=1}^7 \sqrt{\tilde{v}_{ij}} |j\rangle \quad \text{or} \quad R_y(\theta_j)|0\rangle \quad \text{where } \theta_j = 2 \arcsin\left(\sqrt{\tilde{v}_{ij}}\right)$$

### 2.2 Quantum Distance Metric via Born's Rule Probability
Using an ancilla qubit initialized in $|0\rangle$, a swap-test between order state $|\psi_i\rangle$ and centroid state $|c_k\rangle$ produces measurement probabilities:
$$P(|0\rangle_{\text{ancilla}}) = \frac{1 + |\langle \psi_i | c_k \rangle|^2}{2}, \quad P(|1\rangle_{\text{ancilla}}) = \frac{1 - |\langle \psi_i | c_k \rangle|^2}{2}$$
The quantum distance is directly proportional to the probability of measuring $|1\rangle$:
$$D_Q(\psi_i, c_k) = 2 \cdot P(|1\rangle_{\text{ancilla}}) = 1.0 - |\langle \psi_i | c_k \rangle|^2$$

### 2.3 Quantum Fuzzy C-Means (QFCM) Engine
- **Objective Function**:
  $$J_m(U, C) = \sum_{i=1}^N \sum_{k=1}^K (u_{ik})^m D_Q(\psi_i, c_k)$$
- **Fuzzy Membership Update** ($m > 1.0$, default $m=2.0$):
  $$u_{ik} = \frac{1}{\sum_{j=1}^K \left(\frac{D_Q(\psi_i, c_k)}{D_Q(\psi_i, c_j) + \epsilon}\right)^{\frac{1}{m-1}}}$$
- **Centroid Vector Recalculation**:
  $$\mathbf{c}_k = \frac{\sum_{i=1}^N (u_{ik})^m \mathbf{x}_i}{\sum_{i=1}^N (u_{ik})^m}, \quad |c_k\rangle = \frac{\mathbf{c}_k}{\|\mathbf{c}_k\|}$$

### 2.4 Shannon Entropy & Dynamic Boundary Rebalancing
For each order $i$, its cluster assignment uncertainty is measured by Shannon entropy:
$$H_i = -\sum_{k=1}^K u_{ik} \ln(u_{ik} + \epsilon)$$
Orders with high entropy ($H_i > 0.45$) situated on geographical/capacity boundaries are dynamically reassigned to the least-loaded candidate AGV batch, minimizing overall fleet variance and preventing vehicle capacity overflow.

### 2.5 Intra-Cluster VRP QUBO & QAOA Ising Mapping
For each cluster with $N$ nodes (including depot $0$), binary variables $x_{ij} \in \{0, 1\}$ represent traversal from $i$ to $j$:
$$\min \sum_{i,j} d_{ij} x_{ij} + \alpha_{\text{deg}} H_{\text{degree}} + \alpha_{\text{cap}} H_{\text{capacity}} + \alpha_{\text{mtz}} H_{\text{subtour}}$$
Mapping $x_i = \frac{1 - z_i}{2}$ creates the Ising cost Hamiltonian for QAOA:
$$H_C = \sum_i h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + \text{offset}$$

---

## 3. Project Structure & Files

```
applications/logistics/vehicle_routing_problem/
├── README.md                                  # This comprehensive project documentation
├── F-means_implementation_plan.md             # Detailed architecture and implementation plan
├── wms_quantum_fmeans.py                      # Quantum Fuzzy C-Means (QFCM) engine & entropy rebalancing
├── wms_quantum_optimization_pipeline.py       # Core quantum pipeline (K-Means, QAOA synthesis, Benchmarks)
├── wms_visual_simulator.py                    # 2D Warehouse simulator (CLI, PNG, GIF, Interactive GUI)
├── test_quantum_fmeans.py                     # Unit tests for Quantum F-Means
├── vehicle_routing_problem.ipynb              # Interactive Jupyter tutorial notebook
├── vehicle_routing_problem.qmod               # Native Classiq QMOD model file
├── vehicle_routing_problem.metadata.json      # Classiq library registry metadata
├── vehicle_routing_problem.synthesis_options.json # Synthesis compiler preferences
├── wms_simulation.png                         # Generated static routing map (with fuzzy boundary rings)
└── wms_simulation.gif                         # Generated animated multi-AGV dispatch simulation
```

---

## 4. Installation & Environment Setup

### 4.1 Prerequisites
- Python 3.10 - 3.12 (or Windows Python 3.12+ in virtual environment)
- Active virtual environment (e.g. `classiq_env`)

### 4.2 Required Packages
```bash
pip install classiq numpy scipy matplotlib pillow networkx
```

---

## 5. Usage & Execution Guide

### 5.1 Running the Visual Simulator (`wms_visual_simulator.py`)

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--clustering` | Clustering algorithm (`fmeans` or `kmeans`) | `fmeans` |
| `--fuzziness-m` | Fuzziness exponent $m$ for Quantum F-Means | `2.0` |
| `--num-points` | Number of synthesized order locations (`0` for fixed 10-point demo) | `100` |
| `--k-batches` | Number of AGV pick clusters / fleet size | `4` |
| `--animate` | Generate frame-by-frame animated dispatch sequence (GIF) | `False` |
| `--output` | Destination path (`.png` or `.gif`) | `wms_simulation.png` / `.gif` |
| `--seed` | Random generator seed for repeatable order coordinates | `42` |
| `--gui`, `--interactive` | Launch interactive desktop window (`TkAgg` backend) | `False` |

#### Mode 1: Static Route Map with Quantum F-Means (PNG)
```powershell
python wms_visual_simulator.py --clustering fmeans --num-points 40 --k-batches 4 --output wms_simulation.png
```
*Console Output Example:*
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

#### Mode 2: Animated Multi-AGV Simulation (GIF)
```powershell
python wms_visual_simulator.py --clustering fmeans --num-points 25 --k-batches 3 --animate --output wms_simulation.gif
```

#### Mode 3: Interactive GUI Desktop Window
```powershell
python wms_visual_simulator.py --clustering fmeans --num-points 30 --k-batches 3 --gui
```

---

### 5.2 Comparative Benchmarking (K-Means vs F-Means)

Run the built-in benchmark to compare hard vs. soft quantum clustering:

```powershell
python -c "import pprint; from wms_quantum_optimization_pipeline import benchmark_kmeans_vs_fmeans; pprint.pprint(benchmark_kmeans_vs_fmeans(num_points=60, k_batches=4))"
```

*Benchmark Output:*
```python
{
  'fmeans': {
    'counts': [15, 18, 14, 13],
    'std_dev': 1.8708,
    'latency_seconds': 0.4539,
    'mean_entropy': 1.2497
  },
  'kmeans': {
    'counts': [12, 19, 18, 11],
    'std_dev': 3.5355,
    'latency_seconds': 0.0662
  }
}
```
*Key Finding*: Quantum F-Means reduces cluster count standard deviation by **~47%**, ensuring significantly more balanced fleet workload.

---

### 5.3 Multi-Depot Field-Technician Dispatch (9-Method Framework)

For the complete architectural guide, mathematical formulations, and comparative benchmarks of all 9 dispatch paradigms (including Quantum-Inspired Genetic Algorithms, Hierarchical K-Means + GA, and MCDA multi-criteria winner scoring), see:
- 📖 **[Comprehensive Algorithms Reference Manual (`ALGORITHMS.md`)](ALGORITHMS.md)**

---

### 5.4 Running Unit Tests

```powershell
python -m unittest test_quantum_fmeans.py
python -m unittest test_multitier_dispatch.py
```
