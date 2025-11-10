---
search:
    boost: 3.163
---

# Uncomputation

<!-- cspell:ignore Toffoli -->

Uncomputation is the process of reversing the effects of quantum operations,
restoring the state of qubits to their initial $|0\rangle$ state and
disentangling them from other qubits. Failing to
properly uncompute intermediate results can lead to incorrect final measurement
results and wasted resources. In Qmod, intermediate results are typically
stored in local variables, which are scoped inside a function and are
inaccessible outside of it. Hence, local variables must be used in a way that
enables subsequent uncomputation. Specifically, their interactions with other
objects must be restrictive to be subsequently disentangled from them.

In Qmod, local variables are **automatically uncomputed**, lifting the burden
of manually uncomputing intermediate results. When finer-grained control is
required, allocate the variable inside the _within_ block of a
[_within-apply_](statements/within-apply.md) statement. Such variables are
subject to strict rules that guarantee their correct uncomputation.
In this way, Qmod abstracts away the implementation details of efficient quantum
storage management and prevents a class of functional bugs that are very
difficult to detect.
A fully manual uncomputation can be achieved by using [free](quantum-variables.md#free),
as variables which are explicitly freed are not subject to these rules.

To enable these capabilities, quantum operations are classified into arbitrary
functions and _permutation_-only functions. In addition, each of an operation's
parameters is classified as either _const_ or _non-const_.

-   **permutation**: A quantum operation is a _permutation_ if it maps
    computational-basis states to computational-basis states (with possible
    phase shifts). Such an operation neither introduces nor destroys quantum
    superpositions, and its computation can be described classically.
-   **const**: A parameter of a quantum operation is constant if it is
    immutable up to a phase. That is, the magnitudes of its computational-basis
    state components remain unchanged, while their phases may shift.

_permutation_ functions are explicity declared using the keyword
`qperm`. _const_ parameters are explicity declared using the keyword
`const`. See more under [Function Declarations](functions.md).

??? Examples

    - `Z` is a _permutation_ and its parameter is _const_ as it merely flips the phase
      of the $|1\rangle$ state.
    - `X` is a _permutation_ but its parameter is not _const_ as it flips between
      $|0\rangle$ and $|1\rangle$.
    - `H` is not a _permutation_ and its parameter is not _const_, as it
      introduces superposition.
    - `SWAP` is a _permutation_ but its two parameters are not _const_, as it
      swaps between $|01\rangle$ and $|10\rangle$.

## Quantum operations classification

Each quantum operation is classified as either an arbitrary mutation of the quantum
state or strictly a _permutation_ of computational-basis states, according to the
following rules:

-   A function call is a _permutation_ if the callee is declared as `qperm`.
-   A numeric assignment (both out-of-place and in-place) is a _permutation_.
-   Amplitude-encoding assignment is _non-permutation_.
-   Phase statement is a _permutation_.
-   A compound statement is a _permutation_ if its body contains only _permutation_
    operations. For example, a _control_ statement is a _permutation_ if all
    statements inside its _then_ and _else_ clauses are _permutations_.
-   Bind statement is considered a _permutation_, as are `allocate` and
    `free`.

In addition, each use of a quantum variable is classified as either _const_ or
_non-const_:

-   An argument in a function call is classified according to the modifier used
    in the matching parameter declaration.
-   Use as right-value quantum expression is _const_. Right-value expressions
    occur in the following contexts:
    -   On the right-hand side of a numeric assignment or amplitude-encoding assignment.
    -   As the condition in a _control_ statement.
    -   As the argument of a _phase_ statement.
-   Use as left-value expression in numeric assignments (both out-of-place and
    in-place) and amplitude-encoding assignments is _non-const_.
-   Arguments to a _bind_ statement are treated specially: they are not
    immediately classified, but are instead bound together and assigned a
    joint classification of either _const_ or _non-const_.

### Enforcement of function classification

Generally, a `qperm` function is restricted to use only _permutation_
operations, and a `const` parameter is restricted to _const_ use contexts.
Violation of these restrictions results in a compilation error.

However, flexibility is often required in the implementation of lower-level
building blocks. The cumulative effect of the function on the quantum
parameters in these cases satisfies its declared restrictions, but individual
operations violate it. Well known examples are the implementation of Toffoli gate,
and arithmetic addition in the Fourier bases. Both are permutation-only operations
taken as a whole, but internally use Hadamard gates and rotations.

It is not scalable to validate the correct cumulative effect of a description
automatically in the general case. However, you can suppress the fine-grained
enforcement of function classification with the `disable_perm_check` and
`disable_const_checks` specifiers using the following syntax:

=== "Python"

    The decorators `@qfunc` and `@qperm` have the optional parameters
    `disable_perm_check` and `disable_const_checks` declared thus -

      disable_perm_check: bool = False

      disable_const_checks: Union[list[str], bool] = False

    `disable_const_checks` may contain a list of parameter names, or a boolean
    to disable the checks for all _const_ parameters.

=== "Native"

    Before a function definition you may specify the following decorators:

    **@disable_perm_check**

    **@disable_const_checks** [ **(** _parameters_ **)** ]

    Where _parameters_ is an optional list of comma-separated parameter names (if
    the list is omitted, the checks are disabled for all _const_ parameters).

When `disable_perm_check` is used, the compiler does not enforce the usage of
_non-permutation_ operations. When `disable_const_checks` is used, the compiler
does not enforce use context restrictions on the listed parameters (or all
parameters if none specified).

### Examples

#### Example 1 - Correct use of permutation and const parameters

In the example below, function `foo` is declared `qperm`, and its first
parameter `param1` is declared `const`. The definition of `foo` is consistent
with these declarations. Note that the restriction on `param1` is carried over
to its use in the lambda expression passed to `apply_to_all`.

=== "Python"

    ```python
    from classiq import *


    @qperm
    def foo(param1: Const[QNum], param2: Output[QNum]):
        param2 |= param1 + 1  # OK - assignment is a permutation and RHS is const
        apply_to_all(lambda qb: Z(qb), param1)  # OK - the parameter of 'Z' is const
    ```

=== "Native"

    ```
    qperm foo(const param1: qnum, output param2: qnum) {
      param2 = param1 + 1;  // OK - assignment is a permutation and RHS is const
      apply_to_all(lambda(qb) {
        Z(qb);
      }, param1);  // OK - the parameter of 'Z' is const
    }
    ```

#### Example 2 - Incorrect use of permutation and const parameters

The example below demonstrates violations of the restrictions on the use of
parameters and operations. As in the previous example, the function `foo` is
declared `qperm` and its first parameter `param1` is declared `const`. However,
the use of `param1` violates the restriction, and the function uses a
_non-permutation_ operation as well.

=== "Python"

    ```python
    from classiq import *


    @qperm
    def foo(param1: Const[QNum], param2: Output[QNum]):
        param1 += 2  # Error - LHS is non-const
        hadamard_transform(param2)  # Error - 'hadamard_transform' is non-permutation
    ```

=== "Native"

    ```
    qperm foo(const param1: qnum, output param2: qnum) {
      param1 += 2;  // Error - LHS is non-const
      hadamard_transform(param2);  // Error - 'hadamard_transform' is non-permutation
    ```

#### Example 3 - Disabling permutation check

In the example below, function `my_cx` implements the CX operation using a
simple equivalence - applying phase flip in the Hadamard basis. The cumulative
operation on the quantum state is a _permutation_, but individual calls to `H` are
not. The `disable_perm_check` is used to suppress compiler errors in this case.

=== "Python"

    ```python
    from classiq import *


    @qperm(disable_perm_check=True)
    def my_cx(ctrl: Const[QBit], tgt: QBit):
        H(tgt)
        CZ(ctrl, tgt)
        H(tgt)
    ```

=== "Native"

    ```
    @disable_perm_check
    qperm my_cx(const ctrl: qbit, tgt: qbit) {
      H(tgt);
      CZ(ctrl, tgt);
      H(tgt);
    }
    ```

#### Example 4 - Disabling permutation check and const checks

In the example below, function `my_z` implements the Z operation using a
simple equivalence - applying bit flip in the Hadamard basis. The cumulative
operation on the quantum state is a _permutation_, but individual calls to `H` are
not. Also, the cumulative operation on the `tgt` is _const_, but individual
calls are not.
The `disable_perm_check` and `disable_const_checks` are used to suppress
compiler errors in this case.

=== "Python"

    ```python
    from classiq import *


    @qperm(disable_perm_check=True, disable_const_checks=True)
    def my_z(tgt: Const[QBit]):
        H(tgt)
        X(tgt)
        H(tgt)
    ```

=== "Native"

    ```
    @disable_perm_check
    @disable_const_checks
    qperm my_z(const tgt: qbit) {
      H(tgt);
      X(tgt);
      H(tgt);
    }
    ```

## Semantics of uncomputation

When a variable is initialized inside the _within_ block of a [_within-apply_](statements/within-apply.md)
statement, it is returned to its uninitialized state after the statement
completes. The newly allocated quantum object is uncomputed, and its qubits are
reclaimed by the compiler for subsequent use. Likewise, a variable declared locally
within a function is only accessible inside the function's scope. The quantum object
allocated inside the function may be uncomputed at some later point and its
qubits reclaimed.

Local variables are considered _uncomputation candidates_ if they remain initialized at the
end of the function scope in which they were declared. Variables initialized inside a
_within_ block of a _within-apply_ statement are also considered uncomputation candidates
in the scope of the statement.
The following rules guarantee that uncomputation candidates can be handled
correctly:

-   An uncomputation candidate must not be used in a _non-permutation_ operation.
-   A variable becomes a _dependency_ of an uncomputation candidate when used
    in an operation together with the candidate variable, and the latter is used in
    a _non-const_ context. From that point, the dependency variable is subject to
    the same rules as the candidate variable, while the latter is in scope.
-   An auto-uncomputation candidate must not be used in an operation together
    with a non-local variable if both use contexts are _non-const_.
-   An auto-uncomputation candidate must not become a _dependency_
    of any variable that already (directly or indirectly) depends on it &mdash;
    that is, circular dependencies are not allowed.
-   A variable initialized inside a _within_ block of a _within-apply_ statement can
    only be used in _const_ contexts inside the _apply_ block.

Violating these rules will result in a compilation error.

!!! Note

    The operations [`free`](../quantum-variables/#free) and
    [`drop`](../quantum-variables/#drop) return the variable to its
    uninitialized state, so it is consequently not considered an uncomputation
    candidate and therefore does not undergo automatic uncomputation or any
    uncomputation validation.

### Examples

#### Example 1 - Automatic uncomputation

The example below demonstrates the use of a local variable and its automatic uncomputation.
Variable `aux` is initialized as the left-value expression of an assignment statement, which is a _permutation_
operation. Subsequently, it is used as the condition of a _control_
statement, which is a _const_ context. Both uses are valid, and the variable is
automatically uncomputed and freed correctly at the end of the function.

=== "Python"

    ```python
    from classiq import *


    @qperm
    def foo(qn: QNum, res: QBit):
        aux = QBit()
        aux |= qn > 1
        control(aux, lambda: X(res))


    @qfunc
    def main(qn: Output[QNum], res: Output[QBit]):
        allocate(2, qn)
        hadamard_transform(qn)
        allocate(res)
        foo(qn, res)
        foo(qn, res)
    ```

=== "Native"

    ```
    qperm foo(qn: qnum, res: qbit) {
      aux: qbit;
      aux = qn > 1;
      control(aux) {
        X(res);
      }
    }

    qfunc main(output qn: qnum, output res: qbit) {
      allocate(2, qn);
      hadamard_transform(qn);
      allocate(1, res);
      foo(qn, res);
      foo(qn, res);
    }
    ```

In the synthesized quantum program, variable `aux` is uncomputed and reused across the multiple calls to `foo`,
as can be seen in the visualization:

![auto_uncomputation](../resources/auto_uncomputation.png)

#### Example 2 - Illegal use of local variable

The example below demonstrates illegal use of a local variable in a function
which outputs only one qubit of a Bell pair, making it impossible to uncompute
the other qubit. Specifically, the local variable `q2` undergoes a _non-permutation_
operation, which is flagged as an error.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(q1: Output[QBit]):
        q2 = QBit()
        allocate(q1)
        allocate(q2)
        H(
            q2
        )  # Error - The computation sequence of the local variable 'q2' includes a non-permutation operation
        CX(q2, q1)
    ```

=== "Native"

    ```
    qfunc main(output q1: qbit) {
      q2: qbit;
      allocate(q1);
      allocate(q2);
      H(q2); // Error - The computation sequence of the local variable 'q2' includes a non-permutation operation
      CX(q2, q1);
    }
    ```

#### Example 3 - Illegal use of local variable due to parameter mutation

The example below demonstrates an illegal use of a local variable `aux`, as it is used as an argument
in a call to function `x_transform` together with the variable `p`, where both parameters
of `x_transform` are declared _non-const_.

=== "Python"

    ```python
    from classiq import *


    @qperm
    def x_transform(q1: QBit, q2: QBit):
        X(q1)
        X(q2)


    @qfunc
    def main(p: Output[QBit]):
        aux = QBit()
        allocate(p)
        allocate(aux)
        x_transform(
            p, aux
        )  # Error - The computation sequence of the local variable 'aux' includes an operation which mutates the parameter 'p'
    ```

=== "Native"

    ```
    qperm x_transform(q1: qbit, q2: qbit) {
      X(q1);
      X(q2);
    }

    qfunc main(output p: qbit) {
      aux: qbit;
      allocate(p);
      allocate(aux);
      x_transform(p, aux); // Error - The computation sequence of the local variable 'aux' includes an operation which mutates the parameter 'p'
    }
    ```

#### Example 4 - Illegal use of local variable due to circular dependency

The example below demonstrates an illegal use of the local variable `aux`, as
the two calls to the function `CX` create a circular dependency between it and
the variable `p`.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(p: Output[QBit]) -> None:
        aux = QBit()
        allocate(p)
        allocate(aux)
        CX(
            p, aux
        )  # Error - The computation sequence of the local variable 'aux' includes a circular dependency with the variable 'p'
        CX(aux, p)
    ```

=== "Native"

    ```
    qfunc main(output p: qbit) {
      aux: qbit;
      allocate(p);
      allocate(aux);
      CX(p, aux); // Error - The computation sequence of the local variable 'aux' includes a circular dependency with the variable 'p'
      CX(aux, p);
    }
    ```

#### Example 5 - Correct uncomputation in within-apply

The example below demonstrates the use of a local variable initialized inside a
_within_ block of a _within-apply_ statement. Variable `aux` is initialized as
the left-value expression of an assignment statement, which is a _permutation_
operation. In the _apply_ block, it is used as the condition of a _control_
statement, which is a _const_ context. Both uses are valid, and the variable is
uncomputed and freed correctly after the _within-apply_ statement.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(qn: Output[QNum], res: Output[QBit]):
        allocate(2, qn)
        hadamard_transform(qn)
        allocate(res)
        aux = QBit()
        within_apply(
            within=lambda: assign(qn > 1, aux), apply=lambda: control(aux, lambda: X(res))
        )
    ```

=== "Native"

    ```
    qfunc main(output qn: qnum, output res: qbit) {
      allocate(2, qn);
      hadamard_transform(qn);
      allocate(1, res);
      aux: qbit;
      within {
        aux = qn > 1;
      } apply {
        control (aux) {
          X(res);
        }
      }
    }
    ```

#### Example 6 - Illegal use of local variable in within-apply

The code below is a modification of _Example 1_ above, with a couple of lines
added to demonstrate violations of the rules for correct use of a variable
initialized inside the _within_ block of a _within-apply_ statement. Here,
variable `aux` is also used as the argument of function `H` in the _within_
block. This is an arbitrarily _non-permutation_ operation (indeed `H` introduces
superposition between computational-basis states). In addition, `aux` is used
as the argument of function `X` in the _apply_ block, which is _non-const_
context. Both uses are illegal, and both are reported as errors by the
compiler.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(qn: Output[QNum], res: Output[QBit]):
        allocate(2, qn)
        hadamard_transform(qn)
        allocate(res)
        aux = QBit()
        within_apply(
            within=lambda: (
                assign(qn > 1, aux),
                H(aux),
            ),
            apply=lambda: (
                control(aux, lambda: X(res)),
                X(aux),
            ),
        )
    ```

=== "Native"

    ```
    qfunc main(output qn: qnum, output res: qbit) {
      allocate(2, qn);
      hadamard_transform(qn);
      allocate(1, res);
      aux: qbit;
      within {
        aux = qn > 1;
        H(aux);
      } apply {
        control (aux) {
          X(res);
        }
        X(aux);
      }
    }
    ```

#### Example 7 - Illegal use of dependent variable in within-apply

The following example demonstrates a violation of the rules for correct use of
a dependent variable inside a _within-apply_ statement. Here, variable `aux` is
initialized inside a _within_ block, and is subsequently entangled with `q1`
which is not an uncomputation candidate. From that point, the same restrictions
that hold for `aux` apply to `q1`. Therefore, using it as an argument to
function `H` is illegal, and is reported as an error. Indeed, if `foo` would
execute as specified, `aux` would not be uncomputed correctly.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def foo(q1: QBit, q2: QBit):
        aux = QBit()
        within_apply(
            within=lambda: (
                allocate(aux),
                CX(q1, aux),
                H(q1),
            ),
            apply=lambda: (CX(aux, q2), Z(q1)),
        )
    ```

=== "Native"

    ```
    qfunc foo(q1: qbit, q2: qbit) {
      aux: qbit;
      within {
        allocate(1, aux);
        CX(q1, aux);
        H(q1);
      } apply {
        CX(aux, q2);
        Z(q1);
      }
    }
    ```
