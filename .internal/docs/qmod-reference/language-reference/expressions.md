---
search:
    boost: 1.0
---

# Expressions

Expressions in Qmod have syntax, semantics, and use, similar to expressions in
conventional programming languages.
They comprise literal values, variables, and operators applied to them.
However, Qmod is unique in that variables can be of either [classical](https://docs.classiq.io/latest/qmod-reference/api-reference/classical-types) or
[quantum](https://docs.classiq.io/latest/qmod-reference/language-reference/quantum-types) types, and quantum variables have states that can be a
superposition of values, entangled with the states of other variables.
Expressions over quantum variables evaluate to a superposition of correlated
values.
For example, if `x` is a [classical variable](https://docs.classiq.io/latest/qmod-reference/language-reference/classical-variables)
of type `CInt` (an integer), then `x + 1` is a classical expression of type
`CInt` comprising the operator `+` (plus) applied to `x` and the literal `1`.
Similarly, if `qarr` is a [quantum variable](https://docs.classiq.io/latest/qmod-reference/language-reference/quantum-variables)
of type `QArray[QNum[3]]`, then `qarr[0] > x` is a quantum expression of type
`QBit`.

_Unary operators_ are applied to a single operand. For instance, you can apply
the unary operator `~` (bitwise-invert) to variable `x` and get the expression
`~x`.
_Binary operators_ are applied to two operands. For example, the operator `>`
(greater-than) in the expression `qarr[0] > x` is applied to two operands,
`qarr[0]` and variable `x`.
The expression `qarr[0]` comprises the _subscript operator_ `[]` applied to
variable `qarr` and the literal `0`.
Applications of subscript (`[]`) and field-access (`.`) operators to classical
and quantum variables are called _path expressions_, since they point to a
partial section of the variable along a certain access path.
In our case, for instance, `qarr[0]` represents the first (0) element of the
array `qarr`.

## Qmod Operators

You can apply operators to operand expressions to create composite expressions.
If at least one of the operands is quantum then the expression is quantum as
well; Otherwise, it is classical.

Qmod supports the following operators:

### Arithmetic operators

You can apply arithmetic operators to classical numbers (`CInt` and `CReal`) and
quantum scalars (`QBit` and `QNum`) to create numeric expressions.

-   Add: +
-   Subtract: - (binary)
-   Negate: - (unary)
-   Multiply: \*
-   Power \*\* (quantum base, positive classical integer exponent)
-   Modulo: % limited for power of 2
-   Max: max (n>=2 arguments)
-   Min: min (n>=2 arguments)

### Bitwise operators

You can apply bitwise operators to classical numbers (`CInt` and `CReal`) and
quantum scalars (`QBit` and `QNum`) to create numeric expressions.

-   Bitwise Or: |
-   Bitwise And: &
-   Bitwise Xor: ^
-   Bitwise Invert: ~

### Relational operators

You can apply relational operators to classical numbers (`CInt` and `CReal`) and
quantum scalars (`QBit` and `QNum`) to create Boolean expressions (of types
`CBool` and `QBit`).

-   Equal: ==
-   Not Equal: !=
-   Greater Than: >
-   Greater Or Equal: >=
-   Less Than: <
-   Less Or Equal: <=

### Logic operators

You can apply logical operators to Boolean expressions (`CBool`, `QBit`, and
`QNum[1]`) to create Boolean expressions (of types `CBool` and `QBit`).

-   Logical And: `logical_and()` (in Qmod Native: and)
-   Logical Or: `logical_or()` (in Qmod Native: or)
-   Logical Not: `logical_not()` (in Qmod Native: not)

### Path operators

You can use path operators to access parts of classical and quantum variables of
aggregate types, namely, structs and arrays.

-   Field Access: _struct_ **.** _field-name_
-   Array Slice: _array_ **[** _start-index_ **:** _stop-index_ **]**
    -   In Python, _start-index_ and _stop-index_ may be omitted.
        If _start-index_ is omitted, a `0` will be placed in its stead.
        If _stop-index_ is omitted, `array.len` will be placed in its stead.
-   Array Subscript: _array_ **[** _index_ **]**
    -   The index of a quantum subscript expression must be an [unsigned quantum integer](https://docs.classiq.io/latest/qmod-reference/language-reference/quantum-types/#quantum-scalar-types) variable.
    -   In Python, if _array_ is a Python list and _index_ is a quantum variable, use the alternative syntax: **subscript(** _array_ **,** _index_ **)**
    -   Currently, quantum subscript expressions are not supported in [phase statements](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/phase/).

## Quantum Expressions

Quantum expressions are expressions that involve one or more quantum variables.
Quantum expressions can occur in the following contexts:

-   The right-value in [assignment](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/assignment) statements
-   The condition in [control](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/control) statements
-   The expression argument in [phase](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/phase) statements

During computation, the value(s) of an expression are coherently correlated to
the evaluation of the operators over the computational-basis values of the
quantum variables it comprises, which may be in any specific superpositions and
entanglement.
Quantum expressions may include any combination of operators on any
classical and quantum variables and literals, with the following exceptions:

-   All classical variables must be [compile-time](https://docs.classiq.io/latest/qmod-reference/language-reference/classical-variables/#semantics).
-   The right-hand side of the division (`/`) and power (`**`) operators must be
    a classical expression.

### Examples

The following model includes qubit `q` and quantum numeric `n` of size three.
It uses a `control` statement with a quantum expression `n > 4` to apply
`X` to `q` only when `n` is greater than four.

=== "Python"

    ```python
    from classiq import qfunc, Output, QBit, QNum, allocate, control, hadamard_transform


    @qfunc
    def main(n: Output[QNum[3]], q: Output[QBit]):
        allocate(n)
        hadamard_transform(n)
        allocate(q)
        control(n > 4, lambda: X(q))
    ```

=== "Native"

    ```
    qfunc main(output n: qnum<3>, output q: qbit) {
      allocate(n);
      hadamard_transform(n);
      allocate(q);
      control(n > 4) {
        X(q);
      }
    }
    ```

After executing this model, you get $q=0$ for $n\in\{0, 1, 2, 3, 4\}$ and
$q=1$ for $n\in\{5, 6, 7\}$.

See [additional examples](https://docs.classiq.io/latest/qmod-reference/language-reference/statements/assignment/#examples)
on the Assignment documentation page.

## Classical Expressions

Classical expressions are expressions that involve classical variables and
constant literals, but no quantum variables.
Classical variables may have known values at [compile time, link time, or runtime]](https://docs.classiq.io/latest/qmod-reference/language-reference/classical-variables/#semantics).
Classical expressions with only compile-time variables are evaluated and
simplified during compilation.
This applies sub-expressions of quantum expressions too.
Qmod supports several built-in classical [constants and functions](https://docs.classiq.io/latest/qmod-reference/api-reference/symbolic-functions/),
such as `pi` and `sin`.

### Example

In the following model, function `foo` accepts quantum numeric `n` and a
classical integer `x`, and perform the in-place xor operation `n ^= x + 1`.
Function `foo` is called twice, once with `x=1` and once with `x=-1`.

=== "Python"

    ```python
    from classiq import qfunc, CInt, Output, QNum


    @qfunc
    def foo(n: QNum, x: CInt):
        n ^= x + 1


    @qfunc
    def main(n: Output[QNum]):
        n |= 1
        foo(n, 1)  # n ^= 2
        foo(n, -1)  # n ^= 0
    ```

=== "Native"

    ```
    qfunc foo(n: qnum, x: int) {
      n ^= x + 1;
    }

    qfunc main(output n: qnum) {
      n = 1;
      foo(n, 1);  // n ^= 2;
      foo(n, -1); // n ^= 0;
    }
    ```

On the first call to `foo`, the Qmod compiler assigns `x=1` and simplifies the
expression `x + 1` into `2`.
Therefore, the first `foo` call applies a constant-value xor `n ^= 2`.
On the second call to `foo`, the expression `x + 1` is simplified to `0`.
Since the assignment `n ^= 0` has no effect, the Qmod compiler removes it from
the model.
