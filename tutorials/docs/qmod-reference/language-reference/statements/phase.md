---
search:
    boost: 1.5
---

# Phase

The _phase_ statement is used to encode in the phase of a quantum state the result of
some arithmetic computation. It applies a relative phase to computational-basis states of
variables, which is proportionate to the value of a specified expression over these variables.
_phase_ statements are often used to compute the cost of an optimization problem.

## Syntax

=== "Native"

    **phase** **(** _quantum-expression_ [ **,** _coefficient_ ] **)**

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def phase(expr: SymbolicExpr, coefficient: float = 1.0) -> None:
        pass
    ```

## Semantics

-   _quantum-expression_ consists of quantum scalar variables, numeric constant
    literals, and classical scalar variables, composed using arithmetic operators.
    See below the set of supported operators.
-   _coefficient_ expression is optional, and may include an execution
    parameter. Note that an execution parameter cannot occur in _quantum-expression_.
    If not provided, the default coefficient value is 1.0.
-   The operation rotates each computational basis state about the Z axis by an angle equal
    to the value of _quantum-expression_, multiplied by coefficient if specified.
-   For _quantum-expression_ over quantum variable $x_1, x_2, ... x_n$ that computes the
    function $f(x_1, x_2, ... x_n)$, and coefficient = $\theta$ the operation performed by
    the statement is -
    $|x\rangle \rightarrow e^{i \theta f(x_1, x_2, ... x_n)}|x\rangle$
-   The expression must be a polynomial in the quantum variables. It is compiled into an Ising-model
    Hamiltonian, which is evolved per the specified coefficient.

The following operators are supported:

-   Add: `+`
-   Subtract: `-` (binary)
-   Negate: `-` (unary)
-   Multiply: `*`
-   Divide: `/`
-   Power: `**` (quantum base, positive classical integer exponent)

Note that when the expression consists of a single one-qubit variable, _phase_ statement
is equivalent to the core-library function `PHASE()`.

## Examples

### Example 1

In the following model phase $x^2$ is applied to variable $x$ with the coefficient $\frac{\pi}{4}$.
$x$ is initialized to a superposition of the values 0, 1, 2, and 3. After the _phase_
statement, state 1 is in phase $\frac{\pi}{4}$ relative to state 0, state 2
is rotated $\pi$ relative to state 0. State 3 is rotated $\frac{\pi}{4}$,
which is a full $2\pi$ + $\frac{\pi}{4}$ rotation, that is, the same phase as state 1.

=== "Native"

    ```
    qfunc main(output x: qnum) {
      allocate(2, x);
      hadamard_transform(x);
      phase (x**2, pi/4);
    }
    ```

=== "Python"

    ```python
    from classiq import qfunc, Output, QNum, allocate, hadamard_transform, phase
    from classiq.qmod.symbolic import pi


    @qfunc
    def main(x: Output[QNum]):
        allocate(2, x)
        hadamard_transform(x)
        phase(x**2, pi / 4)
    ```

Visualizing the synthesized quantum program, you can see how Z-rotations and controlled
Z-rotations are used to achieve the required rotation.

![simple_phase_circuit.png](resources/simple_phase_circuit.png)

When executing this model using a state-vector simulator, the relative phases of the
different states can be observed. In

![simple_phase_exe_result.png](resources/simple_phase_exe_result.png)

### Example 2

The following example demonstrates the use of _phase_ statement to encode the cost of a
max-cut problem, as the implementation of the cost-layer in a QAOA ansatz. The qubit
array `v` represents the partition of the set of vertices in a graph into two, and
the expression inside the _phase_ statement computes the number of edges that cross the
partition. Executing this model with the right set of parameter values will yield with
high probability an optimal solution.

=== "Native"

    ```
    qfunc main(gammas: real[4], betas: real[4], output v: qbit[3]) {
      allocate(v);
      hadamard_transform(v);
      repeat (i: 4) {
        phase(
          (v[0] * (1 - v[1]) + v[1] * (1 - v[0]))  // edge 0-1
          + (v[0] * (1 - v[2]) + v[2] * (1 - v[0])),  // edge 0-2
          gammas[i]
        );
        apply_to_all(lambda(q) {
          RX(betas[i], q);
        }, v);
      }
    }
    ```

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(
        gammas: CArray[CReal, 4],
        betas: CArray[CReal, 4],
        v: Output[QArray[QBit, 3]],
    ):
        allocate(v)
        hadamard_transform(v)
        for i in range(4):
            phase(
                (v[0] * (1 - v[1]) + v[1] * (1 - v[0]))  # edge 0-1
                + (v[0] * (1 - v[2]) + v[2] * (1 - v[0])),  # edge 0-2
                gammas[i],
            )
            apply_to_all(lambda q: RX(betas[i], q), v)
    ```
