---
search:
    boost: 3.109
---

# Power

The _power_ statement applies the unitary operation raised to some integer power,
where the unitary is specified as a nested statement block.

## Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def power(exponent: CInt, stmt_block: QCallable) -> None:
        pass
    ```

=== "Native"

    **power** **(** _exponent_ **)** **{** _statements_ **}**

## Semantics

-   If the statement block specifies the unitary operation $U$ on some quantum object,
    _power_ applies $U^{exponent}$.
-   In the general case, the statement block is iterated over _exponent_ times, but in some important
    special cases the operation is implemented more efficiently.
-   Quantum variables declared outside the _power_ statement and used inside its nested
    block must be initialized prior to it and remain initialized subsequently.
-   Quantum variables declared inside the _power_ statement, including in
    nested function calls, must be uninitialized at the end of the statement.

## Examples

In the following example `power` is applied 3 times - to gate-level functions `H` and `RX`,
and to a user-defined function `foo`. It demonstrates both special and general treatment
of the _power_ operation.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def foo(p: CInt, q: QBit) -> None:
        power(p, lambda: H(q))
        power(p, lambda: PHASE(pi / 8, q))


    @qfunc
    def main() -> None:
        q = QBit()
        allocate(q)
        power(2, lambda: foo(5, q))
    ```

=== "Native"

    ```
    qfunc foo(p: int, q: qbit) {
      power (p) {
        H(q);
      }
      power (p) {
        PHASE(pi / 8, q);
      }
    }

    qfunc main() {
      q: qbit;
      allocate(q);
      power (2) {
        foo(5, q);
      }
    }
    ```

Synthesizing this model creates the quantum program shown below.
Because two consecutive applications of `H` cancel each other out, raising `H` to the power
of 5 is equivalent to applying `H` once. Raising `RX` with rotation angle $\pi / 8$ to the
power 5 is equivalent to applying `RX` with rotation angle $5 \times \pi / 8$. However, raising
`foo` to the power 2 requires 2 consecutive applications of `foo`.

![power.png](resources/power.png)
