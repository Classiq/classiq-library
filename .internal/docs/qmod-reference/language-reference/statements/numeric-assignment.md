---
search:
    boost: 2.230
---

# Numeric Assignment

Scalar quantum variables (`qnum` and `qbit`) can be assigned the result of arithmetic/logical
expressions over other scalar variables using computational basis arithmetic. Expressions
comprise conventional arithmetic operators, numeric constants, and quantum scalar variables.

Numeric assignment statements in the computational basis take two forms - out-of-place
and in-place. When assigning the result of an expression out-of-place, a new quantum
object is allocated to store the result. For in-place assignment, the result
of the operation is stored back in the target variable.

## Syntax

=== "Python"

    <!-- cspell:ignore inplace_xor,inplace_add -->

    _target-var_ **|=** _quantum-expression_ <br/>
    OR <br/>
    **assign(**_quantum-expression_**,** _target-var_**)**

    _target-var_ **^=** _quantum-expression_ <br/>
    OR <br/>
    **inplace_xor(**_quantum-expression_**,** _target-var_**)**

    _target-var_ **+=** _quantum-expression_ <br/>
    OR <br/>
    **inplace_add(**_quantum-expression_**,** _target-var_**)**

    #### Notes

    * The operator `|=` is used to represent the native `=` since the operator
      `=` cannot be overloaded in Python.
    * The operator syntax and the function call syntax are equivalent. The
      operator syntax is typically easier to read, but it cannot be used
      directly in lambda expressions, where the function call syntax should be
      used.

=== "Native"

    _target-var_ **=** _quantum-expression_

    _target-var_ **^=** _quantum-expression_

    _target-var_ **+=** _quantum-expression_

## Semantics

-   _quantum-expression_ consists of quantum scalar variables, numeric constant
    literals, and classical scalar variables, composed using arithmetic operators.
    See below the set of supported operators.
-   The quantum variables occurring in the expression can subsequently be used, with their
    states unmodified.

### Out-of-place assignment (`=`/`|=`)

-   _target-var_ must be uninitialized prior to the assignment and is
    subsequently initialized.
-   The size and numeric attributes of _target-var_ are computed to tightly
    fit the range of possible result values of _quantum-expression_, based on variable sizes,
    constants, and operators.
-   The numeric attributes of _target-var_ must be left unspecified in the declaration or
    otherwise be compatible with the computed numeric attributes of _quantum-expression_,
    that is, fit the entire range of possible expression values.

### In-place XOR (`^=`)

-   _target-var_ must be initialized prior to the assignment.
-   Each bit in _target-var_ is xor-ed with the
    respective bit in the result of _quantum-expression_ if any, or otherwise left
    unchanged.
-   Bits in the result of _quantum-expression_ with no counterpart in _target-var_ are ignored.

### In-place add (`+=`)

<!-- cspell:ignore underflows -->

-   _target-var_ must be initialized prior to the assignment.
-   The result of _quantum-expression_ is added to the numeric value of
    _target-var_ according to the
    [two's complement](https://en.wikipedia.org/wiki/Two%27s_complement)
    method.
-   Superfluous fraction digits in _quantum-expression_ are ignored.
    Superfluous fraction digits in _target-var_ remain untouched.
-   When _target-var_ overflows or underflows, its value is wrapped-around the
    integer part (including the sign bit) without incurring additional qubits,
    following the two's complement method.

### Supported arithmetic operators

#### Arithmetic operators

-   Add: +
-   Subtract: - (binary)
-   Negate: - (unary)
-   Multiply: \*
-   Power \*\* (quantum base, positive classical integer exponent)
-   Modulo: % limited for power of 2
-   Max: max (n>=2 arguments)
-   Min: min (n>=2 arguments)

#### Bitwise operators

-   Bitwise Or: |
-   Bitwise And: &
-   Bitwise Xor: ^
-   Bitwise Invert: ~

#### Relational operators

-   Equal: ==
-   Not Equal: !=
-   Greater Than: >
-   Greater Or Equal: >=
-   Less Than: <
-   Less Or Equal: <=

#### Logic operators

-   Logical And: and (in Python `logical_and()`)
-   Logical Or: or (in Python `logical_or()`)
-   Logical Not: not (in Python `logical_not()`)

#### Path operators

-   Field Access: _struct_ **.** _field-name_
-   Array Slice: _array_ **[** _start-index_ **:** _stop-index_ **]**
-   Array Subscript: _array_ **[** _index_ **]**
    -   The index of a quantum subscript expression must be an [unsigned quantum integer](https://docs.classiq.io/latest/qmod-reference/language-reference/quantum-types/#quantum-scalar-types) variable.
    -   In Python, if _array_ is a Python list and _index_ is a quantum variable, use the alternative syntax: **subscript(** _array_ **,** _index_ **)**
    -   Currently, quantum subscript expressions are not supported in [phase statements](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/phase/).

## Examples

### Example 1: Out-of-place assignment

The following is a model that computes the result of the expression `a + 2 * b + 3`,
with `a` initialized to 3 and `b` initialized to a superposition of 1 and 2.
The output is a superposition of 8 and 10.

=== "Python"

    ```python
    from classiq import Output, QBit, QNum, QArray, qfunc


    @qfunc
    def main(res: Output[QNum]) -> None:
        a = QNum()
        b = QNum()
        a |= 3
        prepare_state([0, 0.5, 0.5, 0], 0, b)  # 'b' is in superposition of 1 and 2
        res |= a + 2 * b + 3  # 'res' is in superposition of 8 and 10
    ```

=== "Native"

    ```
    qfunc main(output res: qnum) {
      a: qnum;
      b: qnum;
      a = 3;
      prepare_state([0, 0.5, 0.5, 0], 0, b); // 'b' is in superposition of 1 and 2
      res = a + 2 * b + 3;  // 'res' is in superposition of 8 and 10
    }
    ```

Note that the output size is 4 qubits, since the maximum value of this expression
is 15, given that `a` and `b` are two-qubit variables. Any other size declared for `res`
will result in an error.

### Example 2: In-place XOR assignment

In the next example, the relational expression `a + 2 * b + 3 == 8` is computed, with
`a` initialized to 3 and `b` initialized to 1. Calling function `foo` will flip the
single variable `res`, because the expression evaluates to 1, that is, true.

=== "Python"

    ```python
    from classiq import QNum, qfunc, QBit


    @qfunc
    def foo(res: QBit) -> None:
        a = QNum()
        b = QNum()
        a |= 3
        b |= 1
        res ^= a + 2 * b + 3 == 8  # expression is true so 'res' is flipped
    ```

=== "Native"

    ```
    qfunc foo(res: qbit) {
      a: qnum;
      b: qnum;
      a = 3;
      b = 1;
      res ^= (a + 2 * b + 3 == 8);  // expression is true so 'res' is flipped
    }
    ```

### Example 3: In-place assignment of a logical expression

In the example below, function `my_oracle` serves as a quantum oracle that marks all states
satisfying the logical expression `(x0 and x1) or (x2 and x3)` with a minus phase.

=== "Python"

    ```python
    from classiq import QBit, qfunc, allocate, X, H, within_apply
    from classiq.qmod.symbolic import logical_or, logical_and


    @qfunc
    def my_oracle(x0: QBit, x1: QBit, x2: QBit, x3: QBit) -> None:
        aux = QBit()
        allocate(aux)

        def assignment_stmt(var: QBit) -> None:
            var ^= logical_or(logical_and(x0, x1), logical_and(x2, x3))

        within_apply(lambda: (X(aux), H(aux)), lambda: assignment_stmt(aux))
    ```

    Note that in Python, assignment statements are not allowed directly as lambda expressions.
    Therefore, in this example the `^=` is factored out to an inner Python function.

=== "Native"

    ```
    qfunc my_oracle(x0: qbit, x1: qbit, x2: qbit, x3: qbit) {
      aux: qbit;
      allocate(aux);
      within {
        X(aux);
        H(aux);
      } apply {
        aux ^= (x0 and x1) or (x2 and x3);
      }
    }
    ```

### Example 4: In-place add assignment

The following model initializes two quantum numeric variables `n` and `m`.

=== "Python"

    ```python
    from classiq import SIGNED, Output, QNum, X, allocate, apply_to_all, qfunc


    @qfunc
    def main(m: Output[QNum[3, SIGNED, 2]], n: Output[QNum[3, SIGNED, 1]]) -> None:
        allocate(m)
        apply_to_all(X, m)
        allocate(n)
        n += m
    ```

=== "Native"

    ```
    qfunc main(output m: qnum<3, SIGNED, 2>, output n: qnum<3, SIGNED, 1>) {
      allocate(m);
      apply_to_all(X, m);
      allocate(n);
      n += m;
    }
    ```

Variable `m` has three qubits, of which one is a sign qubit and two are fraction
digits.
By applying `X` (not) to `m`'s qubit, we set its value to `-0.25`.
When adding `m` to `n` (`n += m`), the variables do not align since variable `n`
has one less fraction digit than `m`:

```
n = 00.0
m =  1.11
```

First, we ignore the last fraction digit of `m`:

```
n = 00.0
m =  1.1
```

Then, we extend `m` to the size of `n` (3) by duplicating the sign bit in
accordance with the two's complement method:

```
n = 00.0
m = 11.1
```

Finally, adding `m` to `n` sets `n`'s state to `111`, whose interpretation is
the numeric value `-0.5`.

### Example 5: Overflowing in-place add assignment

The following model demonstrates what happens to the target variable when its
value overflows, i.e., extends beyond the variable domain.

=== "Python"

    ```python
    from classiq import SIGNED, UNSIGNED, Output, QNum, allocate, qfunc


    @qfunc
    def main(n: Output[QNum[3, UNSIGNED, 1]], m: Output[QNum[3, SIGNED, 1]]) -> None:
        allocate(n)  # n = 0
        n += 3.5  # n = 3.5
        n += 1  # n = 0.5, n still has 3 qubits
        allocate(m)  # m = 0
        m += 1.5  # m = 1.5
        m += 1  # m = -1.5, m still has 3 qubits
    ```

=== "Native"

    ```
    qfunc main(output n: qnum<3, UNSIGNED, 1>, output m: qnum<3, SIGNED, 1>) {
      allocate(n);  // n = 0
      n += 3.5;  // n = 3.5
      n += 1;  // n = 0.5, n still has 3 qubits
      allocate(m);  // m = 0
      m += 1.5;  // m = 1.5
      m += 1;  // m = -1.5, m still has 3 qubits
    }
    ```

### Example 6: Quantum subscript expression

The following model demonstrate quantum subscript expression over a classical
list `[7, 3, 6, 2]` and a quantum variable `index`.
The quantum `index` is in superposition over the indices 0 (10%), 1 (20%), 2
(30%), and 3 (40%).
The quantum subscript expression `[7, 3, 6, 2][index]` is in superposition over the
items `[7, 3, 6, 2]` entangled to `index`.
Overall, the output variable `n` evaluates to 7 (10%), 3 (20%), 6 (30%), or 2
(40%).

=== "Python"

    ```python
    from classiq import qfunc, Output, QNum, allocate, prepare_state
    from classiq.qmod.symbolic import subscript


    @qfunc
    def main(n: Output[QNum]) -> None:
        index = QNum()
        prepare_state([0.1, 0.2, 0.3, 0.4], 0, index)
        n |= subscript(
            [7, 3, 6, 2], index
        )  # n is 7, 3, 6, or 2 with increasing probability
    ```

=== "Native"

    ```
    qfunc main(output n: qnum) {
      index: qnum;
      prepare_state([0.1, 0.2, 0.3, 0.4], 0, index);
      n = [7, 3, 6, 2][index];  // n is 7, 3, 6, or 2 with increasing probability
    }
    ```
