---
search:
    boost: 2.251
---

# Quantum Program Synthesis

Quantum algorithm design is a complex task, and solutions based on the
approach of designing at the gate level are not scalable. Likewise, solutions based on
combining existing building blocks are very limited in their scope. The Classiq platform allows a high level
description of quantum algorithms at the functional level and automatically synthesizes a
corresponding quantum program. The synthesis process refines the functional requirements, then allocates and optimizes
available resources such as the number of qubits available and the quantum program depth.

The basic description of quantum algorithms in the Classiq platform is through quantum functions. A
quantum function can be implemented in multiple ways, each with different properties
such as number of qubits, number of auxiliary qubits, depth, and approximation level. You can define any level of refinement of the function, from the purely abstract to the fully
defined. The synthesis engine fills in the details to provide a concrete implementation satisfying all
your requirements.

Moreover, a complete quantum algorithm can be realized in multiple ways, utilizing different
design choices such as function implementations, placement, uncompute strategies,
qubit management, and wirings. The platform sifts through the design space and finds a
best realization given your requirements and resource constraints.

This section describes how to define your algorithm and synthesize a quantum program that implements it:

-   [Getting Started](getting-started.md)
-   [Constraints](constraints.md)
-   [Preferences](preferences.md)
