# Uncomputation

<!-- cspell:ignore permutable, Toffoli -->

Uncomputation is the process of reversing the effects of quantum operations,
restoring the state of qubits to their initial $|0\rangle$ state. Failing to
properly uncompute intermediate results can lead to incorrect final measurement
results and wasted resources. In Qmod, intermediate results are typically
stored in local variables, which are scoped inside a function and are
inaccessible outside of it. Hence, local variables must be used in a way that
enables subsequent uncomputation. Specifically, their interactions with other
objects must be restrictive to be subsequently disentangled from them.

In order to enforce the restrictions, quantum variable use contexts are
classified. Also, explicit declarations are used to specify the intended use of
function parameters.

## Variable use classification

### Use categories

Quantum variables figure in expressions in different contexts. These contexts
determine whether and in which way the state of the object can change. There
are three use categories in this respect:

-   _mutable_ - the object's state may change arbitrarily.
-   _permutable_ - the object is mutable "classically" up to a phase, that is, its state may go through
    computational-basis permutations and phase shifts, but no superposition is
    introduced or destroyed.
-   _const_ - the object is immutable up to a phase, that is, its computational-basis state
    components remain constant in their magnitude, but their phases may shift.

### Use contexts

Following are the use categories of quantum variables in different constructs:

-   An argument in a function call is determined by the mutability modifier used in
    the parameter declaration (mutable by default, or using the keywords
    `permutable` and `const`, see more under [Function Declarations](functions.md)).
-   If multiple parameters of a function are declared `permutable`, their _combined_
    state may go through permutations. Specifically, swapping qubits
    between two permutable parameters is allowed.
-   Use as right-value quantum expression is _const_. Right-value expressions occur
    in the following contexts:
    -   On the right-hand side of a numeric-assignment and amplitude-encoding assignment.
    -   As the condition in _control_ statement.
    -   As the argument of _phase_ statement.
-   Use as left-value expression in numeric assignment (both out-of-place and
    in-place) is _permutable_.
-   Use as left-value in amplitude-encoding assignment is _mutable_ (introducing
    superposition into the state).
-   Use as the argument of _allocate_ statement is considered _permutable_.

### Enforcement of parameter restrictions

The parameters of a quantum function may be declared with the modifiers
`permutable` or `const`. Generally, a `const` parameter is restricted to
_const_ use contexts and a `permutable` parameter is restricted to either
_const_ or _permutable_ use contexts. Violation of these restrictions results
in a compilation error.

However, flexibility is often required in the implementation of lower-level
building blocks. The cumulative effect of the function on the quantum
parameters in these cases satisfies its declared restrictions, but individual
operations violate it. Well known examples are the implementation of Toffoli gate,
and arithmetic addition in the Fourier bases. Both are permutation-only operations
taken as a whole, but internally use Hadamard gates and rotations.

It is not scalable to validate the correct cumulative effect of a description
automatically in the general case. But you can suppress the fine-grained
enforcement of variable use with the `unchecked` specifier using the following
syntax:

=== "Native"

    **qfunc** _name_ **(** _parameters_ **)** **unchecked** **(** _unchecked_parameters_ **)** **{** _statements_ **}**

    _unchecked_parameters_ is a list of one or more comma-separated parameter names

=== "Python"

    The decorator `@qfunc` has the optional parameter `unchecked` declared thus -

      unchecked: Optional[list[str]] = None

    The argument list contains one or more names of the decorated function
    parameters

The compiler does not enforce use context restrictions on quantum parameters
listed as _unchecked_.

### Examples

#### Example 1 - Correct use of permutable and const parameters

In the example below, function `foo` has two parameters - `param1` is declared
`const`, and `param2` is declared `permutable`. Their use in `foo`'s body is
consistent with their declaration. Note that the restriction on `param2` is
carried over to its use in the lambda expression passed to `apply_to_all`. In
this case, the parameter of function `Z` is declared `const` since it is merely
a relative phase flip.

=== "Native"

    ```
    qfunc foo(const param1: qnum, permutable output param2: qnum) {
      param2 = param1 + 1;  // OK - assignment LHS is permutable and RHS is const
      apply_to_all(lambda(qb) {
        Z(qb);
      }, param2);  // OK - the parameter of 'Z' is const
    }
    ```

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def foo(param1: Const[QNum], param2: Output[Permutable[QNum]]):
        param2 |= param1 + 1  # OK - assignment LHS is permutable and RHS is const
        apply_to_all(lambda qb: Z(qb), param1)  # OK - the parameter of 'Z' is const
    ```

#### Example 2 - Incorrect use of permutable and const parameters

The example below demonstrates violations of the restrictions on the use of
parameters. Like in the previous example, function `foo` has two parameters -
`param1` is declared `const`, and `param2` is declared `permutable`. However,
the use of these parameters in both lines is inconsistent with their
declaration.

=== "Native"

    ```
    qfunc foo(const param1: qnum, permutable output param2: qnum) {
      param1 += 2;  // Error - LHS is permutable but 'param1' is const
      hadamard_transform(param2);  // Error - the parameter of 'hadamard_transform'
    }                              // is mutable but 'param2' is permutable
    ```

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def foo(param1: Const[QNum], param2: Output[Permutable[QNum]]):
        param1 += 2  # Error - LHS is permutable but 'param1' is const
        hadamard_transform(param2)  # Error - the parameter of 'hadamard_transform'
        # is mutable but 'param2' is permutable
    ```

#### Example 3 - Unchecked parameter

In the example below, function `my_cx` implements the CX operation using a
simple equivalence - applying phase flip in the Hadamard basis. The cumulative
operation on parameter `tgt` is a state permutation, but individual calls to
`H` are not. The `unchecked` specifier is used to suppress compiler errors in
this case.

=== "Native"

    ```
    qfunc my_cx(const ctrl: qbit, permutable tgt: qbit) unchecked (tgt) {
      H(tgt);
      CZ(ctrl, tgt);
      H(tgt);
    }
    ```

=== "Python"

    ```python
    from classiq import *


    @qfunc(unchecked=["tgt"])
    def my_cx(ctrl: Const[QBit], tgt: Permutable[QBit]):
        H(tgt)
        CZ(ctrl, tgt)
        H(tgt)
    ```

## Semantics of uncomputation

When a variable is initialized inside the _within_ block of a _within-apply_
statement, it is returned to its uninitialized state after the statement
completes. The newly allocated quantum object is uncomputed, and its qubits are
reclaimed by the compiler for subsequent use. Likewise, a variable declared locally
within a function is only accessible inside the function's scope. The quantum object
allocated inside the function may be uncomputed at some later point and its
qubits reclaimed. Uncomputation is forced when a function with a local variable
is called (directly or indirectly) from the _within_ block of a _within-apply_
statement. For more details on _within-apply_ see
[Within-apply](statements/within-apply.md).

Local variables are considered _uncomputation candidates_ if they remain initialized at the
end of the function scope in which they were declared. Variables initialized inside a
_within_ block of a _within-apply_ statement are also considered uncomputation candidates
in the scope of the statement.
following rules guarantee that uncomputation candidates can be handled
correctly:

-   An uncomputation candidate can only be used in either _permutable_ or _const_
    contexts.
-   A variable initialized inside a _within_ block of a _within-apply_ statement can
    only be used in _const_ contexts inside the _apply_ block.
-   A variable becomes a _dependency_ of an uncomputation candidate when used
    in an operation together with the candidate variable, and the latter is used in
    a non-_const_ context. From that point, the dependency variable is subject to
    the same rules as the candidate variable, while the latter is in scope.

Violating these rules will result in a compilation error.

### Examples

#### Example 1 - Correct uncomputation in within-apply

The example below demonstrates the use of a local variable initialized inside a
_within_ block of a _within-apply_ statement. Variable `aux` is initialized as
the left-value expression of an assignment statement, which is a _permutable_
context. In the _apply_ block, it is used as the condition of a _control_
statement, which is a _const_ context. Both uses are valid, and the variable is
uncomputed and freed correctly after the _within-apply_ statement.

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

#### Example 2 - Illegal use of local variable in within-apply

The code below is a modification of _Example 1_ above, with a couple of lines
added to demonstrate violations of the rules for correct use of a variable
initialized inside the _within_ block of a _within-apply_ statement. Here,
variable `aux` is also used as the argument of function `H` in the _within_
block. This is an arbitrarily mutable context (indeed `H` introduces
superposition between computational-basis states). In addition, `aux` is used
as the argument of function `X` in the _apply_ block, which is non-constant
context. Both uses are illegal, and both are reported as errors by the
compiler.

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

#### Example 3 - Illegal use of dependent variable in within-apply

The following example demonstrates a violation of the rules for correct use of
a dependent variable inside a _within-apply_ statement. Here, variable `aux` is
initialized inside a _within_ block, and is subsequently entangled with `q1`
which is not an uncomputation candidate. From that point, the same restrictions
that hold for `aux` apply to `q1`. Therefore, using it as an argument to
function `H` is illegal, and is reported as an error. Indeed, if `foo` would
execute as specified, `aux` would not be uncomputed correctly.

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

#### Example 4 - Illegal use of local variable in function

The example below demonstrates incorrect use of a local variable inside a
function. Function `rand_increment` initializes a local variable `temp` in a
superposition state, using `prepare_state`, and is subsequently entangled with
the parameter `qn`. This makes it impossible to uncompute `temp`. `temp` is a
local variable and therefore an uncomputation candidate. Passing it as argument
to `prepare_state` is flagged as an error, because the parameter is not
declared `permutable`. Note that if `rand_increment` would output `temp`
instead of declaring it as a local variable, the function would be legal.

=== "Native"

    ```
    qfunc rand_increment(qn: qnum) {
      temp: qnum;
      prepare_state([0, 0.8, 0.2, 0], 0, temp);
      qn += temp;
    }
    ```

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def rand_increment(qn: QNum):
        temp = QNum()
        prepare_state([0, 0.8, 0.2, 0], 0, temp)
        qn += temp
    ```
