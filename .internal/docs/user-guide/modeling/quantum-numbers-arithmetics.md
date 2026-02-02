---
search:
    boost: 2.915
---

# Quantum Numbers and Arithmetics

## Introduction

Qmod allows modeling quantum data using typed variables that behave much like variables in classical programming languages: you declare them, allocate them, and then use them in arithmetic and logical expressions over them. In this guide, we focus on quantum numeric variables (for example, integers or fixed-point values represented on qubits) and how to use them in arithmetic expressions, such as addition, comparisons, and bitwise logic, to build useful subroutines for quantum algorithms.

A key motivation is that these expressions are not simply for “doing math”: they are a practical way to encode conditions over quantum states, which appear throughout quantum algorithms. For instance, many search and optimization-style algorithms require marking the states that satisfy a certain condition, often implemented as a phase oracle. In Qmod, such predicates can be written directly as a arithmetic or boolean expression, such as `x + y == target`. We therefore start with a minimal “a + b” example to build intuition about computation over values in superposition, and then expand toward expressing and combining conditions in a way that scales to real algorithmic use cases.

In this guide, you will find:

-   An introduction to **quantum numeric variables (`QNum`)** in Qmod and how they represent **integers or fixed-point values** stored on qubits.
-   An explanation of how to **declare and allocate quantum numbers**, including the meaning of `QNum[size, is_signed, fraction_digits]` and when its type attributes can be **inferred automatically**.
-   A walkthrough showing how **superposition affects arithmetic results**, and how computed outputs (e.g., `z = x + y`) become **correlated/entangled** with the input variables.
-   A description of **assignment** (`|=`) as the main way to compute expressions and store results in a target variable.
-   A clear distinction between **out-of-place** (`z |= x + y`) and **in-place** updates (`x += y`, `z ^= condition`), including when each is useful.
-   Examples of how to specify richer **quantum arithmetic and predicate expressions** using arithmetic, comparison, and bitwise operators to **mark target states** (as used in Grover-like algorithms).

## Quantum numeric variables

In Qmod, once a quantum variable is allocated, it references a quantum object stored on one or more qubits. Quantum variables are declared with a _quantum type_ that defines characteristics such as how many qubits are used and how the state is interpreted. In the case of a quantum number (`QNum`), the state is interpreted as an integer or a fixed-point real number.

When expressing algorithm logic, it is often useful to treat a quantum object as a number and write code that resembles classical numeric programming. However, the values stored in quantum variables may present quantum effects, such as entanglement and superposition. Before diving into how to use quantum numbers, consider the following quantum program:

```python
from classiq import *


@qfunc
def prepare_superposition(q: QArray[QBit]):
    H(q[1])


@qfunc
def main(
    x: Output[QNum[3, UNSIGNED, 0]], y: Output[QNum[3, UNSIGNED, 0]], z: Output[QNum]
):
    allocate(x)
    allocate(y)
    prepare_superposition(x)
    prepare_superposition(y)
    z |= x + y
```

At a high level, this quantum program:

1. Allocate two different quantum numbers, `x` and `y`.
2. Prepare the following superposition states by applying a Hadamard gate on different qubits using `prepare_superposition`:

$$\vert x \rangle = \frac{1}{\sqrt{2}}\left(\vert 0 \rangle + \vert 2 \rangle\right), \quad \vert y \rangle = \frac{1}{\sqrt{2}}\left(\vert 0 \rangle + \vert 2 \rangle\right).$$

3. Evaluate the arithmetic operation `x + y` and assign its result to the variable `z`.

A representative sample output may look like this (each outcome should be measured at a ~25% probability):

| x   | y   | z   | counts | probability | bitstring  |
| --- | --- | --- | ------ | ----------- | ---------- |
| 0   | 0   | 0   | 519    | 0.253417    | 0000000000 |
| 2   | 2   | 4   | 497    | 0.242675    | 0100010010 |
| 2   | 0   | 2   | 508    | 0.248046    | 0010000010 |
| 0   | 2   | 2   | 524    | 0.255859    | 0010010000 |

Since variables `x` and `y` are in superposition, the value of `z` will vary according to the values measured in `x` and `y`. Consequently, `z` is entangled with `x` and `y`.

### Declaring quantum numbers

Now, let’s dive into the declaration of the quantum numbers `x` and `y`. In the example above, they are declared using the type hint `Output[QNum[3, UNSIGNED, 0]]`. A type hint is an annotation next to a variable that specifies what kind of value it represents.

Here, `QNum` indicates that `x` and `y` represent numbers, and their type attributes specifies their numeric attributes:

-   3: the total number of qubits used to store the number (size)

-   `UNSIGNED`: the number has no sign (i.e., non-negative). This field is optional, and set to `UNSIGNED` by default.

-   0: the number has no fraction digits. This means the number is interpreted as an integer. If $\text{fraction_digits} > 0$, the value is interpreted as a fixed-point number, scaled by $2^{-\text{fraction_digits}}$. This field is optional, and set to 0 by default.

This matches the definition of a quantum number type in Qmod as:

<div style="text-align:center;">
QNum[size, is_signed, fraction_digits]
</div>

Here, `is_signed` is an optional field, set to `UNSIGNED` by default, and `fraction_digits` is an optional field set to 0.
It is also possible to use the booleans `False`/`True` instead of `SIGNED`/`UNSIGNED`.
A useful point when writing more general Qmod code is that the type attributes (such as `size`, `is_signed`, and `fraction_digits`) can also be used as Python expressions, which allows you to write code that adapts to the numeric configuration of a quantum variable.

<!-- prettier-ignore-start -->
!!! note
    `size` is an attribute accessible by every quantum type, not only quantum numbers.
<!-- prettier-ignore-end -->

### Omitting type attributes and inference

Note that `z` is declared as `Output[QNum]` without specifying numeric attributes. This is intentional: numeric attributes are optional, and when they are not provided, the Qmod compiler infers them upon the variable’s first initialization (including cases such as assignment). The use of this feature is restricted to when it is possible to infer the type attributes from the quantum number, otherwise the quantum program might raise errors. For instance, if `y` is not correctly declared in the above example, the following error will arise:

<div style="text-align:center;">
Could not infer the size of variable 'y'.
</div>

For a complete description of the numeric inference rules, check the [Language Reference](../../../qmod-reference/language-reference/quantum-types#numeric-inference-rules).

### Alternative: Providing type attributes in `allocate`

Instead of specifying numeric attributes in the type hint, you can provide them in the `allocate` call. The following two declarations are equivalent according to the numeric inference rules and initialization behavior:

```python
from classiq import *


@qfunc
def main(x: Output[QNum[3, SIGNED, 1]]):
    allocate(x)
```

```python
from classiq import *


@qfunc
def main(x: Output[QNum]):
    allocate(3, SIGNED, 1, x)
```

## Numeric assignment

Numeric assignment is the Qmod mechanism that lets you compute with quantum numbers using expressions that resemble classical code. Conceptually, you write an expression such as `x + y`, and the Qmod compiler synthesizes a gate-level description that computes the result in the computational basis, even when `x` and `y` are in superposition.

This can be written using `|=`. For example,
[comment]: DO_NOT_TEST

```python
z |= x + y
```

can be read as:

<div style="text-align:center;">
"Compute x + y and store the result in the variable z."
</div>

In the earlier example, `z` is declared as `Output[QNum]` without specifying how many qubits it uses. This works because Qmod can infer the right size when `z` is first initialized. In this case, `z` is a 4-qubit unsigned quantum number with 0 fraction digits.

This is why the assignment line is doing more than “just storing a value”: it is also the moment where `z` gets its final numeric attributes if you did not specify it explicitly.

### In-place and out-of-place assignment

When you compute something like x + y, you must determine where the result will be stored.

There are two options:

1. **Out-of-place**: write the result into a new variable (leave the inputs unchanged)

This is what happens with:
[comment]: DO_NOT_TEST

```python
z |= x + y
```

-   `x` and `y` remain the same variables, with the same qubits.

-   `z` is the output where the result is computed.

-   This typically creates or initializes storage for `z` (therefore it should not be initialized yet).

-   Quantum effect: if `x` and `y` are in superposition, `z` becomes correlated with them (often entangled), but `x` and `y` are not overwritten.

This is analogous to performing the following classical operation:
[comment]: DO_NOT_TEST

```python
z = x + y
```

This is called out-of-place because the result is written in an additional variable `z`.

2. **In-place**: write the result into the same variable (update an existing variable)

This is what happens with operators like += and ^=:
[comment]: DO_NOT_TEST

```python
x += y
```

-   The result is stored back into x.

-   `x` must already be allocated (because it is being modified).

-   `x` keeps the same number of qubits, so if the operation would need more bits, the result may wrap around (modulo $2^{\rm{size}}$).

This is called in-place because the computation updates the same storage in-place, instead of creating a new variable where the result is assigned.
You can think of this exactly as classical code `x+=y`.

### Two common in-place operators

1. `+=` **(add into the same variable)**

The in-place add can be used to increment a quantum variable's value. To better understand this, we can analyze the following example:

```python
from classiq import *


@qfunc
def main(x: Output[QNum[3]], y: Output[QNum[2]]):
    allocate(y)
    hadamard_transform(y)
    x |= 1
    x += y
```

Whose outputs are close to

| x   | y   | counts | probability | bitstring |
| --- | --- | ------ | ----------- | --------- |
| 4   | 3   | 508    | 0.258046    | 11100     |
| 3   | 2   | 513    | 0.250488    | 10011     |
| 2   | 1   | 522    | 0.254882    | 01010     |
| 1   | 0   | 505    | 0.256582    | 00001     |

This quantum program:

-   Initializes two quantum numbers, `x` and `y`
-   `x` is assigned the integer value 1, while `y` is in a superposition of the values in $[0, 1, 2, 3]$
-   Performs the quantum operation `x = x + y`, where `y` is in a superposition and, consequently, `x` becomes superposed as well.

This way, the variable `x` is always an increment of variable `y`.

2. `^=` **(in-place XOR)**

The bitwise XOR operator is a binary operation that compares the bitstrings of two numeric values and produces a result bit of 1 when the bits differ and 0 when they are the same. In Qmod, it is implemented by applying this rule between corresponding qubits (or between a qubit and a classical bit) across the operands. The in-place form `^=` computes the XOR and writes the result back into the left-hand variable.
In the example below, `x + y == 3` combines this value with `z` using XOR and writes the result back into `z`. This means that `z` is updated only when the condition evaluates to 1.

```python
from classiq import *


@qfunc
def main(x: Output[QNum[3]], y: Output[QNum[2]], z: Output[QBit]):
    allocate(y)
    allocate(z)
    hadamard_transform(y)
    x |= 1
    z ^= x + y == 3
```

Whose outputs are close to

| x   | y   | z   | counts | probability | bitstring |
| --- | --- | --- | ------ | ----------- | --------- |
| 1   | 0   | 0   | 503    | 0.255605    | 000001    |
| 1   | 1   | 0   | 517    | 0.252441    | 001001    |
| 1   | 2   | 1   | 532    | 0.259765    | 110001    |
| 1   | 3   | 0   | 496    | 0.242187    | 011001    |

This quantum program:

-   Initializes two quantum numbers, `x` and `y`, and a qubit `z`.
-   Assign the numeric value 1 to `x` and generates a uniform superposition in `y`.
-   Flips the state of `z` whenever `x + y == 3`.

This way, the in-place XOR operation serves as a powerful way of "marking" target states - a very important tool in search and optimization algorithms, such as [Simon's algorithm](../../../explore/algorithms/foundational/simon/simon).

## Quantum Arithmetics

Qmod supports quantum expressions, including arithmetic expressions, in a manner analogous to classical programming languages. Both quantum and classical expressions may appear on the right-hand side of assignment statements, and quantum expressions may also be used in other contexts, such as the conditions of control statements.

When a quantum expression is written, Qmod records the expression symbolically and translates it into a reversible quantum subroutine that implements the corresponding operation. This ensures that the resulting operation is unitary and can be applied to quantum variables.

### Writing Arithmetic Expressions

Qmod supports a wide range of arithmetic and logical operators inside expressions used for numeric assignment. In practice, this means you can write expressions such as:

-   Arithmetic: `+`, `-`, `*`

-   Comparisons (produce a boolean / predicate): `==`, `!=`, `<`, `<=`, `>`, `>=`

-   Bitwise logic: `&`, `|`, `^`, `~`

-   Boolean composition of predicates: `logical_and`, `logical_or`, `logical_not` (depending on the expression context)

A simple example using different arithmetics and boolean operations is:

```python
from classiq import *


@qfunc
def main(x: Output[QNum[2]], y: Output[QNum[2]], z: Output[QBit]):
    allocate(y)
    allocate(x)
    allocate(z)
    hadamard_transform(x)
    hadamard_transform(y)
    z ^= (x + y - 1) * (x - y + 1) == -1
```

This quantum program:

-   Allocates two quantum numbers `x` and `y`, and a qubit `z`
-   Puts the quantum numbers in superposition over all possible values
-   Computes the predicate

$$(x + y - 1) \cdot (x - y + 1) = -1$$

and conditionally modofies the state of `z` when the predicate is satisfied.

In this context, we are correlating the auxiliary qubit `z` with the values of `x` and `y`. The quantum numbers `x` and `y` themselves are not modified. Instead, `z` becomes entangled with them such that:

-   For basis states where the expression evaluates to -1, the state of `z` is changed to $\vert 1 \rangle$

-   For all other basis states, `z` remains $\vert 0 \rangle$

As a result, measuring `z` and obtaining 1 would collapse `x` and `y` into a superposition of only those value pairs that satisfy the equality.

A technical description of numeric assignment is available at the [Language Reference](../../../qmod-reference/language-reference/statements/assignment/).

## See also

For more information regarding quantum types, see [Quantum Types](../../../qmod-reference/language-reference/quantum-types).
