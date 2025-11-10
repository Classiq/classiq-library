# Quantum Linear Solvers for CFD matrices

This directory contains quantum linear solvers developed for **computational fluid dynamics (CFD)** applications.
The solvers are designed to integrate with **hybrid classical–quantum** workflows,
such as the segregated SIMPLE solver and the implicit coupled solver in the [qc-cfd repository](https://github.com/rolls-royce/qc-cfd/tree/main/1D-Nozzle).
The code was developed in collaboration with Leigh Lapworth of **Rolls-Royce plc**, as part of a joint project.

## Solvers

- **Quantum Singular Value Transformation (QSVT)** for matrix inversion
- **Linear Combination of Unitaries (LCU)** of a Chebyshev polynomial approximation

The code provides two block-encoding implementations for the CFD matrices:

- **LCU for Pauli decomposition**, using a Graycode approach
- **LCU for banded diagonals** according to [Lapworth & S&uuml;nderhauf](https://arxiv.org/abs/2502.20908)

## Notebooks

1. `verify_block_encoding.ipynb` shows how to call and run the block-encoding qfunc for a given matrix.
2. `chebyshev_approximation.ipynb` demonstrates how the Chebyshev approximation for the inversion function is define.
3. `qls_qsvt` and `qls_chebyshev_lcu`, define the generic quantum solvers that can be plugged into the hybrid code.
4. The main **classical** and **quantum** functions are implemented in **separate Python modules** for clarity and reuse.
