# Quantum Differential Equation Solvers

Differential equations are ubiquitous in many fields of science and technology, such as physics, biology, and economics. These equations usually involve many degrees of freedom, requiring efficient numerical methods to obtain accurate dynamical solutions.
The folder presents quantum algorithms for solving differential equations,
demonstrating how linear systems and dynamical evolution problems can be mapped to quantum circuits.
The examples highlight both stationary and time-dependent formulations, leveraging block-encoding
techniques and well-known quantum linear system methods to construct efficient implementations.
Together, they illustrate the potential of quantum computation for scientific and engineering
applications involving partial and ordinary differential equations.

- **Discrete Poisson solver** - Quantum solver for the discrete Poisson equation, a partial differential equation
  (PDE) widely used in physics and engineering. The equation models the distribution of a potential field due
  to a prescribed source term. The problem is reformulated as a system of linear equations and solved using
  the HHL algorithm. Leveraging quantum cosine and sine transforms from the open library enables a concise
  implementation that can be generalized to higher dimensions.

- **Time marching** - A method for solving linear differential equations, by integrating the dynamics in small discrete steps.
  Given an equation of the form $\frac{d|\psi(t)\rangle}{dt} = A(t) |\psi(t)\rangle$, the algorithm utilizes a block-encoding
  of the time-dependent matrix $A(t)$ to solve for $|\psi(t)\rangle$.
