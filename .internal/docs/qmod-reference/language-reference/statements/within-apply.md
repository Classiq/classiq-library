---
search:
    boost: 2.541
---

# Within-apply

The _within-apply_ statement performs the common quantum pattern $U^{\dagger} V U$. It
operates on two nested statement blocks, the _within_ block and the _apply_ blocks,
and evaluates the sequence - _within_, _apply_, and _invert(within)_. Under conditions
described below, quantum objects that are allocated and prepared by the _within_ block
are subsequently uncomputed and released.

## Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def within_apply(within: Callable, apply: Callable) -> None:
        pass
    ```

=== "Native"

    **within** **{** _within-statements_ **}** **apply** **{** _apply-statements_ **}**

## Semantics

-   Unlike the case with other statements, the nested blocks of _within-apply_ may initialize
    outer context variables.
-   Variables that are initialized inside the _within_ block of a _within-apply_ statement,
    are returned to their uninitialized state after the statement completes.
-   All quantum objects allocated directly or indirectly under the _within_ block
    are uncomputed, and their qubits are reclaimed for subsequent use after the statement
    completes.
-   In addition to the general restriction of local variables to _permutable_ use contexts,
    variables initialized inside the _within_ block and their dependents can only be
    used in _const_ contexts inside the _apply_ block. See more on uncomputation rules
    under [Uncomputation](../uncomputation.md).
-   The application of the _within_ block and its inverse are not subjected to redundant control logic in
    the case where the _within-apply_ statement as a whole is subject to control.
-   The application of the _within_ block and its inverse are guaranteed to be strictly equivalent, including
    in the case where _within_ block involves non-deterministic implementation decisions by the
    synthesis engine.

## Examples

### Example 1

The following example demonstrates how auxiliary qubits get used, uncomputed, and reused
at different steps of a computation, when scoped inside a _within-apply_ statement.
Actual reuse is a decision the synthesis engine takes to satisfy width constraints.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(res: Output[QBit]):
        allocate(res)
        ctrl = QNum()
        within_apply(lambda: assign(3, ctrl), lambda: CCX(ctrl, res))
        within_apply(lambda: assign(2, ctrl), lambda: CCX(ctrl, res))
    ```

=== "Native"

    ```
    qfunc main(output res: qbit) {
      allocate(res);
      ctrl: qnum;
      within {
        ctrl = 3;
      } apply {
        CCX(ctrl, res);
      }
      within {
        ctrl = 2;
      } apply {
        CCX(ctrl, res);
      }
    }
    ```

Note how variable `ctrl` is initialized in the
_within_ block, prior to being used for the `CCX` in the _apply_ block.
Outside the _within-apply_ statement the variable is reset to its uninitialized state,
and used again in the same way.

Visualizing the resulting quantum program, you can see how the same two auxiliary
qubits are reused across the two steps of the circuit, because of width optimization.

![within_apply.png](resources/within_apply.png)

### Example 2

The code snippet below demonstrates the implementation of the phase kickback pattern
for an arbitrary quantum predicate. Function `my_phase_oracle` takes as parameter a
function that flips a qubit on the states of interest. Variable `aux` is prepared
in the $|1\rangle$ state and passed as the target to function `my_cond_phase_flip`. The
cumulative effect of `my_cond_phase_flip` is a conditional $\pi$ phase on `target`, controlled
on the states of interest. Since `aux` is subsequently uncomputed and released, a
relative $\pi$ phase remains between the states of interest and all others in the
superposition.

=== "Python"

    ```python
    from classiq import *


    @qperm(disable_perm_check=True, disable_const_checks=True)
    def my_cond_phase_flip(predicate: QPerm[QBit], target: Const[QBit]):
        H(target)
        predicate(target)
        H(target)


    @qperm
    def my_phase_oracle(predicate: QPerm[QBit]):
        aux = QBit()
        within_apply(
            lambda: (allocate(aux), X(aux)), lambda: my_cond_phase_flip(predicate, aux)
        )
    ```

=== "Native"

    ```
    @disable_perm_check
    @disable_const_checks
    qperm my_cond_phase_flip(predicate: qperm (qbit), const target: qbit) {
      H(target);
      predicate(target);
      H(target);
    }

    qperm my_phase_oracle(predicate: qperm (qbit)) {
      aux: qbit;
      within {
        allocate(aux);
        X(aux);
      } apply {
        my_cond_phase_flip(predicate, aux);
      }
    }
    ```

Note that `my_cond_phase_flip` declares parameter `target` as `const` because, taken as
a whole, the function only applies phase changes to it. But because the implementation
uses non-cost operations, `target` is specified as `unchecked`. For more on enforcement
of parameter restrictions see [Uncomputation](../uncomputation.md).

### Example 3

The code snippet below demonstrates the use of _within-apply_ to define the Grover operator,
avoiding redundant control logic when called in higher-level contexts (for example, when
used as the unitary operand in a phase-estimation flow):

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def my_grover_operator(
        oracle: QCallable[QArray[QBit]],
        space_transform: QCallable[QArray[QBit]],
        target: QArray[QBit],
    ):
        oracle(target)
        within_apply(
            lambda: invert(lambda: space_transform(target)),
            lambda: reflect_about_zero(target),
        )
    ```

=== "Native"

    ```
    qfunc my_grover_operator(oracle: qfunc (qbit[]), space_transform: qfunc (qbit[]), target: qbit[]) {
      oracle(target);
      within {
        invert {
          space_transform(target);
        }
      } apply {
        reflect_about_zero(target);
      }
    }
    ```
