---
search:
    boost: 3.365
---

# Invert

The _invert_ statement applies the adjoint (conjugate transpose) of the unitary operation
specified as a nested statement block. If the nested block specifies the unitary operation
$U$, _invert_ applies $U^{\dagger}$.

## Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def invert(stmt_block: QCallable) -> None:
        pass
    ```

=== "Native"

    **invert** **{** _statements_ **}**

## Semantics

-   The _invert_ statement applies the adjoint of the operations specified in the nested
    block, equivalent to the adjoint of each nested statement in reverse order.
-   Quantum variables declared outside the _invert_ statement and used inside its nested
    block must be initialized prior to it and remain initialized subsequently.
-   Quantum variables declared inside the _invert_ statement, including in
    nested function calls, must be uninitialized at the end of the statement.

## Example

The following example demonstrates the use of `invert` applied to a single gate-level
function call, and to a statement block in which a user-defined function `foo` is called twice.

=== "Python"

    ```python
    from classiq.qmod.symbolic import pi
    from classiq import *


    @qfunc
    def foo(target: QBit) -> None:
        H(target)
        X(target)


    @qfunc
    def main() -> None:
        qba = QArray()
        allocate(2, qba)
        invert(lambda: RX(pi / 2, qba[0]))
        invert(lambda: [foo(qba[0]), foo(qba[1])])
    ```

=== "Native"

    ```
    qfunc foo(target: qbit) {
      H(target);
      X(target);
    }

    qfunc main() {
      qba: qbit[];
      allocate(2, qba);
      invert {
        RX(pi / 2, qba[0]);
      }
      invert {
        foo(qba[0]);
        foo(qba[1]);
      }
    }
    ```

Synthesizing this model creates the quantum program shown below. The inversion of
`RX` is simply negating the rotation angle. In the second `invert` statement each call to
`foo` is inverted, applying the gate-level functions in reverse but unchanged (as they
are hermitian).

![invert.png](resources/invert.png)
