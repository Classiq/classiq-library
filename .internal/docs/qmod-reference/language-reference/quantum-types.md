---
search:
    boost: 3.650
---

# Quantum Types

<!-- cspell:ignore qbit, qnum, structs -->

Once initialized, Qmod variables reference a quantum object in some state. Quantum types
determine the overall number of qubits used to store the object, as well as the
interpretation of its state. For example, a quantum object stored on 4 qubits can represent an
array of 4 bits, an integer number in the domain 0 to 15, or an array of two fixed-point
numbers in the domain [-1.0, -0.5, 0, -0.5]. The type determines which interpretation
is the intended one, for example, when evaluating quantum operators.

Qmod has two categories of quantum scalar types - bits and numbers. Qmod also supports
quantum array and struct types, which can be arbitrarily nested.

Certain quantum type attributes can be retrieved using field access:
_var_._attr-name_.
For example, the total number of qubits referenced by variable `my_var` is
obtained by writing `my_var.size`.
The attributes associated with each quantum type are listed below.

## Quantum Scalar Types

In Qmod, there are two kinds of scalar quantum types:

-   `qbit` represents the states $|0\rangle$, $|1\rangle$, or a superposition of the two
-   `qnum` represents numbers in some discrete domain - integers or fixed-point reals

When declaring a `qnum` variable, you can optionally specify its numeric attributes -
overall size in bits, whether it is signed, and the number of binary fraction digits.

### Syntax

=== "Python"

    In Python the classes `QBit` and `QNum` are used as type hints in the declaration of arguments:

    _name_ **:** **QBit**

    _name_ **:** **QNum** [ **[** _size-int-expr_ [ **,** _sign-bool-expr_ **,** _frac-digits-int-expr_ ] **]** ]

    The same classes are used to declare local variables:

    _name_ =  **QBit** **( "** _local_name_ **" )**

    _name_ = **QNum** **( "** _name_ **" ,** [ [ **size =** ] _size-int-expr_ **,** [ [ **is_signed =** ] _sign-bool-expr_ **,** [ [ **fraction_digits =** ] _frac-digits-int-expr_ ] **)**

=== "Native"

    **qbit**

    **qnum** [ **<** _size-int-expr_ [ **,** _sign-bool-expr_ **,** _frac-digits-int-expr_ ] **>** ]

It is recommended to use the `SIGNED` and `UNSIGNED` built-in constants instead
of `True` and `False` respectively when specifying the _sign-bool-expr_ `qnum`
property.

### Semantics

-   Computational-basis encoding of numeric types is big-endian (the most significant bit has
    the highest index).
-   _size-int-expr_ determines the overall number of qubits used to store the number, including
    sign and fraction where applicable.
-   If _sign-bool-expr_ is `True` (`SIGNED`), two's complement is used to represent signed numbers, utilizing the most-significant bit for sign.
-   _frac-digits-int-expr_ determines the number of least-significant bits representing binary fraction digits.
-   When only _size-int-expr_ is specified and _sign-bool-expr_ and
    _frac-digits-int-expr_ are left out, the later two are set to `UNSIGNED` and
    `0` (integer) respectively.

### Attributes

-   `qbit`:
    -   `size`: The total number of qubits (always 1).
-   `qnum`:
    -   `size`: The total number of qubits (including the fraction digits and the sign bit).
    -   `is_signed`: Whether the number is signed.
    -   `fraction_digits`: The number of fraction digits.

### Examples

In the following example, two 4-qubit numeric variables, `x` and `y`, are prepared to store the
bit string `1101`. `x` is declared with no sign bit and no fraction digits, and therefore
its state represents the number 13. `y` is declared to be signed and have one fraction-digit, and
thus, the same bit-level state represents the number -1.5.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def prepare_1101(qba: Output[QArray[QBit]]):
        allocate(4, qba)
        X(qba[0])
        X(qba[2])
        X(qba[3])


    @qfunc
    def main(x: Output[QNum[4]], y: Output[QNum[4, SIGNED, 1]]):
        prepare_1101(x)
        prepare_1101(y)
    ```

=== "Native"

    ```
    qfunc prepare_1101(output qba: qbit[]) {
      allocate(4, qba);
      X(qba[0]);
      X(qba[2]);
      X(qba[3]);
    }

    qfunc main(output x: qnum<4>, output y: qnum<4, SIGNED, 1>) {
      prepare_1101(x);
      prepare_1101(y);
    }
    ```

## Numeric Inference Rules

Numeric representation modifiers are optional in the declaration. When left out, the
representation attributes of a `qnum` variable are determined upon its first initialization.
Following are the inference rules for these cases:

-   When the varialbe is initialized with `allocate`, the size is determined by
    the `num_qubits` argument, while sign and fraction-digits are either explicitly
    specified or default to `False` (`UNSIGNED`) and 0 respectively.
-   When the variable is passed to a function as its output argument with declared type `qbit[]`,
    the size is determined by the actual array size, while sign and fraction-digits default to
    `False` (`UNSIGNED`) and 0 respectively.
-   When the variable is passed to a function as its output argument with declared type
    `qnum`, the size is determined by the actual size, sign, and fraction-digits of the
    function's output.
-   When the variable is initialized on the left of an out-of-place assignment `=`, the domain
    of the expression determines its representation properties.
-   Variables retain their type, including the representation attributes, even after being
    un-initialized (for example, when occurring on the left side of a _bind_ statement).
    Subsequent initializations must agree with the specific `qnum` type.
-   On the right side of a _bind_ statement (`->`) the representation attributes of `qnum`
    variables must already be known either through declaration, or by previous initialization
    (and subsequent un-initialization).

### Examples

The following example demonstrates the default and explicit numeric interpretation of
quantum states. Two variables, `a` and `b`, are initialized to some quantum state.
`a` is left with the default unsigned integer interpretation. `b` is initialized to a
superposition of the bit strings 01 and 10 interpreted with a sign bit and one
fraction digit. This implies that its domain is [-1.0, -0.5, 0, 0.5] and its value
is in a superposition of -1.0 and 0.5. `res` is accordingly uniformly distributed on the 8
possible addition values.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(a: Output[QNum], b: Output[QNum[2, SIGNED, 1]], res: Output[QNum]) -> None:
        allocate(2, a)  # 'a' is a 2 qubit unsigned int in the domain [0, 1, 2, 3]
        hadamard_transform(a)  # 'a' is in a superposition of all values in its domain
        prepare_state([0, 0.5, 0.5, 0], 0, b)  # 'b' is in superposition of 01 and 10
        res |= a + b
    ```

=== "Native"

    ```
    qfunc main(output a: qnum, output b: qnum<2, SIGNED, 1>, output res: qnum) {
      allocate(2, a);
      hadamard_transform(a);
      prepare_state([0, 0.5, 0.5, 0], 0, b);
      res = a + b;
    }
    ```

## Rounding a `qnum` in Qmod

QNum variables may occasionally be declared with too few qubits to represent their intended values. This can occur, for example, when a variable is the result of an arithmetic operation.
In such cases, Qmod automatically resolves the issue by adjusting the variable’s possible outcomes. Specifically, it rounds down the numeric values to fit within the allocated number of qubits.

### Examples

The following example shows that when allocating a `qnum` and then performing some arithmetic operation,
the values are rounded down:

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(x: Output[QNum[3, False, 1]], y: Output[QNum[4, False, 2]]):
        allocate(
            x
        )  # Allocate x as a quantum number with 3 qubits, no sign and 1 fraction digit
        allocate(
            y
        )  # Allocate y as a quantum number with 4 qubits, no sign and 1 fraction digit
        hadamard_transform(x)  # Create a superposition of all possible numbers of x
        y ^= 1.4 * x  # Evaluate y = 1.4 * x
    ```

=== "Native"

    ```
    qfunc main(output x: qnum<3, False, 1>, output y: qnum<4, False, 2>) {
        allocate(x);
        allocate(y);
        hadamard_transform(x);
        y ^= 1.4 * x;
    }
    ```

Output measurements:

    state=[{'x': 1.0, 'y': 1.25}: 268,
            {'x': 1.5, 'y': 2.0}: 262,
            {'x': 2.5, 'y': 3.25}: 261,
            {'x': 0.0, 'y': 0.0}: 260,
            {'x': 2.0, 'y': 2.75}: 255,
            {'x': 3.5, 'y': 0.75}: 253,
            {'x': 0.5, 'y': 0.5}: 251,
            {'x': 3.0, 'y': 0.0}: 238]

Notice, for instance, when `x = 1.0`, the exact product 1.4 is rounded down to 1.25 to fit into `y`'s available qubits.

## Quantum arrays

A quantum array is an object that supports indexed access to parts of its state - its
elements. Elements are interpreted as values of the specified array element type. A
quantum array is one object with respect to its lifetime. Elements of an array cannot
be initialized separately or bound separately to other variables. Also, an array's length
(the number of elements it represents) is fixed at the time of its initialization and
remains constant throughout its lifetime.

### Syntax

=== "Python"

    In Python the class `QArray` is used as type hints in the declaration of arguments:

    _name_ **:** **QArray** [ **[** _element-type_ [ **,** _length-expr_ ] **]** ]

    The same class is used to declare local variables:


    _name_ = **QArray** **( "** _name_ **"** [ **,** _element-type_ [ **,** _length-expr_ ] ] **)**

=== "Native"

    _element-type_ **[** [ _length-expr_ ] **]**

### Semantics

-   _element_type_ optionally determines the type of the array elements. Arrays are homogenous,
    that is, all elements are of the same type. When left unspecified, the type defaults to
    `qbit`.
-   _length-expr_ optionally determines the number of elements in the array. The overall size
    of the array is its length multiplied by the size of the element type. When the length is
    unspecified, it is determined upon initialization based on the element size. Similarly,
    when the size of the element type is not specified, it is inferred upon initialization
    based on the length. Either the length, or the size of the element type, must be specified
    in the declaration
-   The length cannot change throughout the lifetime of an array.

Expressions of quantum array type support the following operations:

-   Subscript: _array-expression_ **[** _index-expression_ **]**
-   Slice: _array-expression_ **[** _from-index-expression_ : _to-index-expression_ **]**
-   Length: _array-expression_ **.** **len**

### Attributes

-   `size`: The total number of qubits (= length &times; element size).
-   `len`: The number of array elements.

### Examples

In the following example, a Boolean expression of a 3-SAT formula is evaluated over
the elements of a qubit array, which is prepared in the state of uniform superposition.
Note that bitwise operators are used in this case, but equivalent logical operators
`and`, `or`, and `not` (and their respective Python counterparts in package `qmod.symbolic`)
are also supported.

=== "Python"

    ```python
    from classiq import qfunc, Output, QArray, QBit, hadamard_transform, bind


    @qfunc
    def main(x: Output[QArray[QBit, 3]], res: Output[QBit]) -> None:
        allocate(x)
        hadamard_transform(x)
        res |= (x[0] | ~x[1] | ~x[2]) & (~x[0] | x[1] | ~x[2])
    ```

=== "Native"

    ```
    qfunc main(output x: qbit[3], output res: qbit) {
      allocate(x);
      hadamard_transform(x);
      res = (x[0] | ~x[1] | ~x[2]) & (~x[0] | x[1] | ~x[2]);
    }
    ```

The next example demonstrates the initialization of a numeric array using the _bind_
statement (`->`). Two numeric variables are declared and initialized separately and
subsequently bound together to initialize the array. The declared type of these
variables is an unsigned integer, but the declared element type of the array is signed. Hence,  
the values 6 and 7 are interpreted as -2 and -1, respectively. When executing the resulting
quantum program, `res` is sampled with the value -3 (with probability 1).

=== "Python"

    ```python
    from classiq import qfunc, Output, QArray, QNum, SIGNED, bind


    @qfunc
    def main(res: Output[QNum]) -> None:
        n0 = QNum("n0", 3)
        n0 |= 6
        n1 = QNum("n1", 3)
        n1 |= 7

        n_arr = QArray("n_arr", QNum[3, SIGNED, 0])
        bind([n0, n1], n_arr)

        res |= n_arr[0] + n_arr[1]
    ```

=== "Native"

    ```
    qfunc main(output res: qnum) {
      n0: qnum<3>;
      n0 = 6;
      n1: qnum<3>;
      n1 = 7;
      n_arr: qnum<3, SIGNED, 0>[];
      {n0, n1} -> n_arr;
      res = n_arr[0] + n_arr[1];
    }
    ```

## Quantum structs

A quantum struct is an object that supports named access to parts of its state - its
fields. Each field corresponds to a slice of the overall object, interpreted according
to its declared type. A quantum struct is one object with respect to its lifetime. Fields
of a struct cannot be initialized separately or bound separately to other variables.

Quantum structs are typically used to pack and unpack multiple variables, that is, to
switch between contexts that treat the object in a generic way (as a qubit array) and
in a problem-specific way (to capture expressions over fields).

### Syntax

The following syntax is used to define a quantum struct type -

=== "Python"

    A quantum struct type in Python is defined using a Python class derived from the
    class `QStruct`. Fields are declared with type hints, similar to how member variables
    are declared in a Python `dataclass`.

=== "Native"

    **qstruct** _name_ **{** _field_declarations_ **}**

    _field-declarations_ is a list of one or more field declarations in the form - _name_ **:** _quantum-type_ **;**.

### Semantics

-   Only quantum types are allowed as field types in a quantum struct.
-   Quantum structs may be arbitrarily nested, that is, a field of a struct may itself be a
    struct or a struct array. However, recursive struct types are not allowed.
-   The overall size of a struct (the number of qubits used to store it) must be known upon
    declaration. This means that the size of all fields, except at most one, must be fully
    specified.

Expressions of quantum struct type support field-access operation in the form - _struct-expression_ **.** _field-name_.

### Attributes

-   `size`: The total number of qubits (= the sum of field sizes).

In Qmod's Python embedding, the quantum struct's total number of qubits can be
retrieved using the `num_qubits` class attribute.

### Examples

In the following example, quantum struct `MyQStruct` is defined and subsequently initialized
and prepared in a specific state in function `main`.

=== "Python"

    ```python
    from classiq import *


    class MyQStruct(QStruct):
        a: QBit
        b: QNum[3]


    @qfunc
    def main(s: Output[MyQStruct]) -> None:
        allocate(s)
        H(s.a)
        s.b ^= 6
    ```

=== "Native"

    ```
    qstruct MyQStruct {
      a: qbit;
      b: qnum<3>;
    }

    qfunc main(output s: MyQStruct) {
    allocate(s);
    H(s.a);
    s.b ^= 6;
    }
    ```

The example below demonstrates the common situation where an algorithm alternates between
the two views of a quantum state - the structured view with partition into problem variables,
and the unstructured view as an array of qubits. The example defines a constraint over
two variables, `a` and `b`, of different numeric types. It uses Grover-search to find a
solution. In the Grover-search algorithm, encapsulated by the function `grover_search`, the
oracle application uses the structured view of the state to evaluate the constraint, while the
diffuser is defined in a generic way and uses the qubit array view of the state.

=== "Python"

    ```python
    from classiq import *


    class MyProblem(QStruct):
        a: QNum[2, UNSIGNED, 2]
        b: QNum[3, UNSIGNED, 3]


    @qfunc
    def my_problem_constraint(p: Const[MyProblem], res: Permutable[QBit]) -> None:
        res ^= p.a + p.b == 0.625


    @qfunc
    def main(p: Output[MyProblem]) -> None:
        allocate(p)
        grover_search(2, lambda p: phase_oracle(my_problem_constraint, p), p)
    ```

=== "Native"

    ```
    qstruct MyProblem {
      a: qnum<2, UNSIGNED, 2>;
      b: qnum<3, UNSIGNED, 3>;
    }

    qfunc my_problem_constraint(const p: MyProblem, permutable res: qbit) {
      res ^= (p.a + p.b) == 0.625;
    }

    qfunc main(output p: MyProblem) {
      allocate(p);
      grover_search(2, lambda(p) {
        phase_oracle(my_problem_constraint, p);
      }, p);
    }
    ```

Executing this model will sample a state representing a solution to the problem in
very high probability. This is an example of an output. Here is an output example:

    state={'p': {'a': 0.0, 'b': 0.625}} shots=350
    state={'p': {'a': 0.25, 'b': 0.375}} shots=344
    state={'p': {'a': 0.5, 'b': 0.125}} shots=306

In Qmod's Python embedding, the size of `MyProblem` is given by
`MyProblem.num_qubits`:
[comment]: DO_NOT_TEST

```python
print(MyProblem.num_qubits)  # 5
```
