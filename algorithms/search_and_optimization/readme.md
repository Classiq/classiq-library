# Search and Optimization

The folder presents quantum algorithms for search and combinatorial optimization,
illustrating both exact and approximate solution strategies. The implementations range from
Grover’s amplitude amplification for unstructured search to structured optimization methods such
as Decoded Quantum Interferometry and hybrid variational approaches like QAOA and its Grover-based
mixer variants. Together, these examples demonstrate how quantum interference, amplitude
amplification, and parameterized circuit optimization can be applied to SAT variants, Max-Cut,
Knapsack, XORSAT, and other discrete optimization problems.

- **Decoded Quantum Interferometry** - A quantum algorithm for combinatorial optimization problems. Given a matrix, $B$, with indicies
  belonging to a finite field $\mathbb{F}$, and an optimization function, $f(x)$, depending on $B$ and an input vector $x\in \mathbb{F}^n$,
  the algorithm produces optimal input, maximizing $f$. Shown to give a quantum advantage in Optimal Polynomial Intersection problem.
  In the present notebook, a simplified version of the problem called max-XORSAT, is utilized to demonstrate the key algorithmic steps.
- **Grover** - A canonical quantum algorithms, providing the solution of an unstructured search problem.
  A general routine is defined and then applied to generic use cases, including the 3-SAT problem and the Max-Cut problem on a graph.
  The use of the phase_oracle quantum function from the Classiq open library, together with the Qmod language for high-level
  arithmetic operations, helps avoid the low-level implementation details typically required on other platforms.

- **Grover Mixers for QAOA** - A variant of QAOA in which the standard mixer Hamiltonian is replaced by a parameterized
  Grover diffuser constructed over the equal superposition of all feasible solutions.
  This modification makes the algorithm particularly suitable for constrained optimization problems,
  where conventional QAOA may struggle to maintain feasibility throughout the evolution. In essence, the approach shifts
  the implementation complexity from designing problem-specific mixers to preparing the feasible-state superposition
  with sufficient accuracy.
- **Quantum Approximate Optimization Algorithm (QAOA)** -
  A hybrid quantum–classical framework for solving combinatorial optimization problems. The algorithm prepares a parameterized
  quantum state through an alternating sequence of two operators: a problem unitary that encodes the objective (cost) function, and a mixing unitary that redistributes amplitudes across candidate solutions.
  After measuring the circuit, a classical optimizer updates the parameters to maximize the expected objective value.
  This iterative loop continues until high-quality solutions are obtained.
  QAOA is particularly attractive for near-term quantum hardware due to its shallow circuit structure,
  while its approximation quality can be systematically improved by increasing the number of alternating layers (depth).
  We illustrate the method through the Max-Cut and Knapsack problems, representing unconstrained and constrained optimization
  settings, respectively.
