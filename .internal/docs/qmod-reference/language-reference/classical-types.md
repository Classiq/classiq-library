---
search:
    boost: 2.823
---

# Classical Types

<!-- cspell:ignore struct, structs, subclassing -->

Classical types in Qmod are not very different from classical types in conventional
programming languages. There are scalar types like `int` and `bool`, and aggregate
types, such as arrays and structs.

Classical types are used to declare classical function arguments, and global constants.
Variables and literal values of classical types can be used in expressions, and support
the conventional set of operators commonly available in conventional programming languages.

## Scalar Types

In Qmod, scalar types represent numeric values, Boolean values, and Pauli base elements.

### Syntax

=== "Python"

    Python Classes are used to represent scalar types

    - `CInt` represents integers
    - `CReal` represents real numbers (using floating point encoding)
    - `CBool` represents the Boolean values `False` and `True`
    - `Pauli` represents the Pauli base elements using the symbols `Pauli.I`, `Pauli.X`, `Pauli.Y`, and `Pauli.Z` (with the integer values 0, 1, 2, 3 respectively)

=== "Native"

    - `int` represents integers
    - `real` represents real numbers (using floating point encoding)
    - `bool` represents the Boolean values `false` and `true`
    - `Pauli` represents the Pauli base elements using the symbols `Pauli::I`, `Pauli::X`, `Pauli::Y`, and `Pauli::Z` (with the integer values 0, 1, 2, 3 respectively)

## Arrays

Arrays are homogenous collections of scalars or structs with random access.

### Syntax

=== "Python"

    Array types are represented with the generic class `CArray`. Arguments are declared with the type hint in the form:

    _name_ **:** **CArray** [ **[** _element-type_ [ **,** _length_expression_ ] **]** ]

=== "Native"

    Array types have the form - _element-type_ **[** [ _length_expression_ ] **]**

### Semantics

_element-type_ is any scalar, array, or struct type.
_length_expression_ is optional, determining the length of the array. When left out, the length is determined upon
variable initialization.

Expressions of array type support the following operations:

-   Subscript: _array-expression_ **[** _index-expression_ **]**
-   Slice: _array-expression_ **[** _from-index-expression_ : _to-index-expression_ **]**
-   Length: _array-expression_ **.** **len**

Literal array values are expressed in the form - **[** _values_ **]**, where _values_
is a list of zero or more comma-separated expressions of the same type.

### Example

The following example demonstrates the use of classical arrays in Qmod. Function `foo`
takes an array of reals, and uses the `.len` attribute and array subscripting to access
the elements of the array. Note that index -1 signifies the last element in an array
(similar to Python).

=== "Python"

    ```python
    from classiq import qfunc, CArray, CReal, QBit, RX, allocate, if_


    @qfunc
    def foo(arr: CArray[CReal], qb: QBit) -> None:
        if_(arr.len > 2, lambda: RX(arr[-1], qb), lambda: RX(arr[0], qb))


    @qfunc
    def main() -> None:
        q0 = QBit()
        allocate(q0)
        foo([0.5, 1.0, 1.5], q0)
    ```

=== "Native"

    ```
    qfunc foo(arr: real[], qb: qbit) {
      if (arr.len > 2) {
        RX(arr[-1], qb);
      } else {
        RX(arr[0], qb);
      }
    }

    qfunc main() {
      q0: qbit;
      allocate(q0);
      foo([0.5, 1.0, 1.5], q0);
    }
    ```

## Structs

Structs are aggregates of variables, called _fields_, each with its own name and type.

=== "Python"

    A Qmod classical struct is defined with a Python data class: A class decorated with
    `@dataclasses.dataclass`.

    Fields need to be declared with type-hints like classical arguments of functions.
    Fields are initialized and accessed like attributes of Python object.

=== "Native"

    Structs are declared in the form - **struct** **{** _field-declarations_ **}**, where
    _field-declarations_ is a list of one or more field declarations in the form - _name_ **:** _classical-type_ **;**.

    Expressions of struct type support the field-access operation in the form - _struct-expression_ **.** _field-name_.

    Literal struct values are expressed in the form - _struct-name_ **{** _field-value-list_ **}**. where
    _field-value-list_ is a list of zero or more comma-separated field initializations in the form -
    _name_ **=** _expression_.

### Example

In the following example a struct type called `MyStruct` is defined. Function `foo`
takes an argument of this type and accesses its fields. Function `main` instantiates
and populates `MyStruct` in its call to `foo`.

=== "Python"

    ```python
    from classiq import *
    from dataclasses import dataclass


    @dataclass
    class MyStruct:
        loop_counts: CArray[CInt]
        angle: CReal


    @qfunc
    def foo(ms: MyStruct, qv: QArray[QBit, 2]) -> None:
        H(qv[0])
        repeat(
            count=ms.loop_counts[1],
            iteration=lambda index: PHASE(ms.angle + 0.5, qv[1]),
        )


    @qfunc
    def main() -> None:
        qba = QArray()
        allocate(2, qba)
        foo(MyStruct(loop_counts=[1, 2], angle=0.1), qba)
    ```

=== "Native"

    ```
    struct MyStruct {
      loop_counts: int[];
      angle: real;
    }

    qfunc foo(ms: MyStruct, qv: qbit[2]) {
      H(qv[0]);
      repeat (index: ms.loop_counts[1]) {
        PHASE(ms.angle + 0.5, qv[1]);
      }
    }

    qfunc main() {
      qba: qbit[];
      allocate(2, qba);
      foo(MyStruct {
        loop_counts = [1, 2],
        angle = 0.1
      }, qba);
    }
    ```

## Hamiltonians

Qmod's Python embedding offers a specialized syntax for creating
[sparse Hamiltonian](https://docs.classiq.io/latest/qmod-reference/api-reference/classical-types/#classiq.qmod.builtins.structs.SparsePauliOp)
objects.
Calling a
[Pauli](https://docs.classiq.io/latest/qmod-reference/api-reference/classical-types/#classiq.qmod.builtins.enums.Pauli)
enum value (e.g., `Pauli.X`) with an index (e.g., `Pauli.X(3)`) creates a
single-qubit Pauli operator.
The multiplication of single-qubit Pauli operators (e.g.,
`Pauli.X(1) * Pauli.Y(2)`) constructs the tensor product of these operators on
the respective qubits.
These can be linearly combined in a sum, each optionally
with a scalar coefficient (e.g., `0.5 * Pauli.X(2) + Pauli.Y(0)*Pauli.Z(2)`).

### Example

The Hamiltonian specified by the Pauli strings `XYZ` and `IXI` with coefficients
`0.5` and `0.8` respectively is specified in the standard struct literal syntax
as follows:
[comment]: DO_NOT_TEST

```python
H = SparsePauliOp(
    terms=[
        SparsePauliTerm(
            paulis=[
                IndexedPauli(pauli=Pauli.Z, index=0),
                IndexedPauli(pauli=Pauli.Y, index=1),
                IndexedPauli(pauli=Pauli.X, index=2),
            ],
            coefficient=0.5,
        ),
        SparsePauliTerm(
            paulis=[
                IndexedPauli(pauli=Pauli.X, index=1),
            ],
            coefficient=0.8,
        ),
    ],
    num_qubits=3,
)
```

You can specify the same Hamiltonian using the specialized Hamiltonian syntax as
follows:
[comment]: DO_NOT_TEST

```python
H = 0.5 * Pauli.Z(0) * Pauli.Y(1) * Pauli.X(2) + 0.8 * Pauli.X(1)
```
