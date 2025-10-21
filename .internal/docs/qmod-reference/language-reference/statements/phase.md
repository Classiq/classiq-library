---
search:
    boost: 2.927
---

# Phase

The _phase_ statement is used to compute and encode the result of some
arithmetic computation in the phase of the respective quantum states. It applies
a relative phase to computational-basis states of quantum variables proportional
to the value of a specified expression over these variables. The _phase_
statement can also specify a fixed rotation angle, i.e., a "global" phase, using
an expression with no quantum variables. When a fixed phase rotation occurs
under a controlled context, it affects only the controlling states. Otherwise, a
fixed _phase_ statement is undetectable.

_phase_ statements with a quantum expression are often used to compute the cost
of an optimization problem. Applying a fixed _phase_ is useful in expressing
phase oracles and reflections.

## Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def phase(phase_expr: SymbolicExpr, coefficient: float = 1.0) -> None:
        pass
    ```

=== "Native"

    **phase** **(** _phase-expression_ [ **,** _coefficient_ ] **)**

## Semantics

-   _phase-expression_ may consist of quantum scalar variables, numeric constant
    literals, and classical scalar variables, composed using arithmetic operators.
    See below the set of supported operators.
-   The _coefficient_ expression is optional, and may include an execution
    parameter. Note that an execution parameter cannot occur in _phase-expression_ if it
    contains quantum variables.
    If not provided, the default coefficient value is 1.0.
-   The operation rotates each computational basis state about the Z axis by an angle equal
    to the value of _phase-expression_, multiplied by _coefficient_ if specified.
-   For _phase-expression_ over quantum variable $x_1, x_2, \ldots, x_n$ that computes the
    function $f(x_1, x_2, \ldots, x_n)$ and _coefficient_ $=\theta$, the operation performed by
    the statement is $|x\rangle \rightarrow e^{i\theta f(x_1, x_2, \ldots, x_n)} |x\rangle$.
-   For _phase-expression_ without quantum variables that evaluates to $\theta$, the operation
    performed by the statement is $|x\rangle \rightarrow e^{i\theta} |x\rangle$.
-   The expression must be a polynomial in the quantum variables. It is compiled into an Ising-model
    Hamiltonian, which is evolved per the specified coefficient.

The following operators are supported:

-   Add: `+`
-   Subtract: `-` (binary)
-   Negate: `-` (unary)
-   Multiply: `*`
-   Divide: `/` (by a classical value)
-   Power: `**` (quantum base, positive classical integer exponent)

The following operators are supported only when applied to `QBit`, `QNum[1]`,
and the classical integers `0` and `1`:

-   Bitwise Or: `|`
-   Bitwise And: `&`
-   Bitwise Xor: `^`
-   Bitwise Not: `~`

Note that when the expression consists of a single one-qubit variable, _phase_ statement
is equivalent to the core-library function `PHASE()`.

## Examples

### Example 1

In the following model phase $x^2$ is applied to variable $x$ with the coefficient $\frac{\pi}{4}$.
$x$ is initialized to a superposition of the values 0, 1, 2, and 3. After the _phase_
statement, state 1 is in phase $\frac{\pi}{4}$ relative to state 0, state 2
is rotated $\pi$ relative to state 0. State 3 is rotated $\frac{\pi}{4}$,
which is a full $2\pi$ + $\frac{\pi}{4}$ rotation, that is, the same phase as state 1.

=== "Python"

    ```python
    from classiq import *
    from classiq.qmod.symbolic import pi


    @qfunc
    def main(x: Output[QNum]):
        allocate(2, x)
        hadamard_transform(x)
        phase(x**2, pi / 4)
    ```

=== "Native"

    ```
    qfunc main(output x: qnum) {
      allocate(2, x);
      hadamard_transform(x);
      phase (x**2, pi/4);
    }
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

### Example 3

The following model applies `phase` with an angle specified as a classical
expression, thus inserting a fixed phase under controlled contexts. In each
case, the states that satisfy the control condition rotate by $\frac{\pi}{4}$
relative to those that do not.

=== "Python"

    ```python
    from classiq import *
    from classiq.qmod.symbolic import pi


    @qfunc
    def main(qarr: Output[QArray[QBit, 2]]):
        allocate(qarr)
        hadamard_transform(qarr)
        control(qarr[0], lambda: phase(pi / 4))
        control(qarr, lambda: phase(pi / 4))
    ```

=== "Native"

    ```
    qfunc main(output qarr: qbit[2]) {
      allocate(qarr);
      hadamard_transform(qarr);
      control (qarr[0]) {
        phase (pi / 4);
      }
      control (qarr) {
        phase (pi / 4);
      }
    }
    ```

The cumulative result of both statements revealed by running a state-vector
simulation is a uniform superposition of the four states with the following
phases:

$$
\begin{aligned}
  |[0,0]\rangle&: 0 \\
  |[0,1]\rangle&: 0 \\
  |[1,0]\rangle&: \frac{\pi}{4} \\
  |[1,1]\rangle&: \frac{\pi}{2} \\
\end{aligned}
$$
