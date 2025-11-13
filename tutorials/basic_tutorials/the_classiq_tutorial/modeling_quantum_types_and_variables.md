# Hands-on Tutorial: Quantum Types and Variables

This tutorial walks through Qmod quantum types and how to use variables of these types in code.

It assumes:

- You already have the Classiq Python SDK installed.
- You know how to run a synthesized model and inspect measurement results.

---

## Setup

Through this tutorial, you should import Classiq before using it:

```python
from classiq import *
```

After creating a quantum program defined by a function `main`, follow the minimal workflow pattern for each example:

```python
qprog = synthesize(main)
show(qprog)               # view the synthesized circuit

with ExecutionSession(qprog) as es:
    res = es.sample()

display(res.dataframe)  # inspect results in a dataframe table
```

flowchart LR
    A[High-Level description] --> B[Synthesis]
    B --> C[Quantum circuit]
    C --> D[Execution]
    D --> E[Measurement Outcomes]


## 1. Concepts: quantum objects, types, and variables

Before anything, it is important to know there are three concepts we need to understand:

- **Quantum object**  
  The actual state stored on one or more qubits (e.g., a single qubit or an integer encoded in several qubits).

- **Quantum type**  
  The combination of the quantum object and classical metadata. Which allows the synthesis engine to know:
  - How a set of qubits are used.
  - How to interpret their state (e.g., a particular set of qubits represents the number 3,125. How does the quantum algorithm knows this? Answer: By defining the quantum type correctly).
  - Any extra attributes, such as signedness or fractional bits for numbers.

- **Quantum variable**  
  A named handle that refers to a quantum object of a given type.  
  Variables are introduced as:
  - Function parameters.
  - Local quantum variables inside a [Quantum Function](https://docs.classiq.io/latest/qmod-reference/language-reference/functions).

Once a variable is initialized, it is bound to a specific quantum object.

|                      | # of qubits | Interpretation                                               | Example Values                                                                     |
|----------------------|-------------|--------------------------------------------------------------|------------------------------------------------------------------------------------|
| `QBit`               | 1           | Single qubit                                                 | Any superposition between $\vert 0\rangle$ and $\vert 1\rangle$                    |
| `QNum[3, SIGNED, 1]` | 3           | Signed number with a fraction digit                          | States of 3 qubits that represent a signed number with a fraction digit            |
| `QArray[QBit, 4]`    | 4           | Set of 4 qubits                                              | Any superposition of 4 qubits                                                      |
| `QStruct`            |             | A quantum structure that may contain different quantum types | A single qubit in one field and a quantum number in another field of the `QStruct` |

## 2. `QBit`: the single-qubit type

### 2.1 Declaring and allocating a single qubit

```python
from classiq import *

@qfunc
def main(q: Output[QBit]):
    allocate(q)      # q refers to a fresh qubit in |0>
    H(q)             # put q in superposition
```

Key points:

- `Output[QBit]` means `q` is uninitialized at the function entry.
- `allocate(q)` binds `q` to a fresh qubit in the $\vert 0 \rangle$ state.
- `H(q)` applies a Hadamard gate, creating a superposition of $\vert 0 \rangle$ and $\vert 1 \rangle$.

### 2.2 Exercise 1: Prepare $\vert + \rangle$ and inspect results

**Goal**: Confirm that measuring $\vert + \rangle$ yields $\vert 0 \rangle$ and $\vert 1 \rangle$ with roughly equal probability.

```python
@qfunc
def main(q: Output[QBit]):
    allocate(q)
    H(q)

qprog = synthesize(main)
show(qprog)

with ExecutionSession(qprog) as es:
    res = es.sample()

display(res.dataframe)
```

What to inspect:

- **Circuit**: A single qubit with an H gate.
- **Measurement histogram**: Approximately 50% probability for `0` and 50% for `1`.

---

## 3. `QArray[QBit]`: arrays of qubits

A quantum array is a fixed-size collection of elements of the same quantum type:

- `QArray[QBit]` → array of individual qubits.
- `QArray[QNum]` → array of quantum numbers.

### 3.1 Declaring and allocating an array of qubits

```python
@qfunc
def main(arr: Output[QArray[QBit]]):
    allocate(5, arr)          # 5 qubits: arr[0] ... arr[4]
    hadamard_transform(arr)   # apply H to all five qubits
```

Key points:

- `allocate(5, arr)` allocates 5 qubits to the quantum array `arr`.
- `hadamard_transform(arr)` is shorthand for applying H to each element of `arr`.

### 3.2 Indexing, slicing, and using gates

```python
@qfunc
def array_indexing_demo(arr: Output[QArray[QBit]]):
    allocate(5, arr)

    hadamard_transform(arr[0:3])   # act on arr[0], arr[1], arr[2]
    CX(arr[2], arr[3])             # control = arr[2], target = arr[3]
```

Notes:

- `arr[i]` behaves like a `QBit`.
- `arr[start:stop]` behaves like a quantum array.

### 3.3 Exercise 2: Bell state in a `QArray[QBit]`

**Goal**: Prepare the Bell state  
$$
\vert \Phi^+\rangle = \frac{\vert 00\rangle + \vert 11\rangle}{\sqrt{2}}
$$  
using a 2-qubit array.

1. Define a `@qfunc` with an `Output[QArray[QBit]]` parameter.
2. Allocate an array of length 2.
3. Apply H to the first qubit.
4. Apply CX with the first qubit as control and the second as target.

Reference solution:

```python
@qfunc
def main(arr: Output[QArray[QBit]]):
    allocate(2, arr)
    H(arr[0])
    CX(arr[0], arr[1])
```

Expected behavior:

- Only `00` and `11` appear in measurement results.
- Probabilities are close to $50\%$-$50\%$.

**Suggested figure (Figure 3)**  
Two-qubit circuit with:

- H gate on `arr[0]`.
- CX gate from `arr[0]` to `arr[1]`.

---

## 4. `QNum`: quantum numbers

`QNum` represents numbers encoded in multiple qubits, with configurable attributes.

A general form is:

```text
QNum[qbits, signed, fraction_bits]
```

- `qbits`: total number of qubits.
- `signed`: signedness (`SIGNED` / `UNSIGNED`).
- `fraction_bits`: number of qbits used for the binary fractional part.

Examples:

- `QNum[3, False, 0]`  
  3-bit unsigned integer (values 0–7).
- `QNum[4, True, 0]`  
  4-bit signed integer (two’s complement).
- `QNum[5, True, 2]`  
  5-bit signed fixed-point with 2 fractional bits.

When some attributes are omitted (for example `QNum` or `QNum[bits]`), Qmod may infer them from context in simple expressions.

### 4.1 Numeric superposition and a function of `x`

Example: create a uniform superposition over 3-bit integers and compute a function of `x`.

```python
@qfunc
def qnum_parabola(x: Output[QNum], y: Output[QNum]):
    allocate(3, x)          # 3 qubits → x ∈ {0, …, 7}
    hadamard_transform(x)   # uniform superposition over all x

    y |= x**2 + 1           # numeric assignment: y = x^2 + 1
```

Notes:

- `allocate(3, x)` fixes `x` to 3 bits where inference is not enough.
- `y |= expression` is a **numeric assignment**:
  - `y` is allocated and computed from `expression`.
  - Under the hood, it lowers to a sequence of reversible quantum operations.

Table showing 3-bit patterns and their unsigned integer values:

| qubits | Value |
|--------|-------|
| 000    | 0     |
| 001    | 1     |
| 010    | 2     |
| 011    | 3     |
| 100    | 4     |
| 101    | 5     |
| 110    | 6     |
| 111    | 7     |

### 4.2 Exercise 3: GHZ state encoded as a signed `QNum`

**Goal**: Create a 3-qubit `QNum` encoding $0$ and $−1$ with equal probability.

Steps:

1. Define a `qfunc` `number_superposition` that manipulates a `QArray`.
2. Inside this function:
   - `000` represent 0.
   - `111` represent −1 as a signed 3-qbit integer.
3. Prepare a GHZ-like state $\left(\vert 000\rangle + \vert 111\rangle\right)/\sqrt{2}$.
4. Use the type `QNum[3, SIGNED, 0]` (3-bit signed integer) in the `main` function calling .
5. Measure and interpret results as a signed integer.

Skeleton:

```python
from classiq import *
@qfunc
def number_superposition(x:QArray):
    # Your code here
    

@qfunc
def main(x: Output[QNum[3, True, 0]]):
    allocate(x)
    number_superposition(x)
```

Questions:

- Consider `a = QNum[3, SIGNED, 0]`. Which number does `111` represent? (Answer: `-1`.)
- What number does `a`represents if it is `UNSIGNED`? (Answer: `7`)
- Does your measurement output show probabilities close to 50% for 0 and 50% for −1?

Table of 3-bit signed values:

| Bits | Signed value |
|------|--------------|
| 000  | 0            |
| 001  | 1            |
| 010  | 2            |
| 011  | 3            |
| 100  | −4           |
| 101  | −3           |
| 110  | −2           |
| 111  | −1           |


## 5. `QArray[QNum]`: arrays of numbers

Quantum arrays can store numeric elements:

```python
@qfunc
def main(
    bits: Output[QArray[QBit, 3]],
    nums: Output[QArray[QNum[2, False, 0], 4]],
):
    allocate(bits)   # 3 qubits total
    allocate(nums)   # 4 numeric elements, each with 2 qubits
```

Notes:

- `bits` has 3 elements of type `QBit` → total 3 qubits.
- `nums` has 4 elements of type `QNum[2, False, 0]` → total 4 × 2 = 8 qubits.
- The array length refers to number of elements, not number of qubits.

You can act on individual elements or subarrays:

```python
@qfunc
def main(nums: Output[QArray[QNum[4, SIGNED, 0], 2]], x: Output[QBit]):
    allocate(nums)    # 2 numeric elements
    allocate(x)
    number_superposition(nums[0])  # superpose the first numeric element
    hadamard_transform(nums[1])
    x ^= nums[0] + nums[1] == 3 # Checks whether the sum of distinct elements is equals 3
```

**There will be a figure here**  
Nested blocks:

- Outer boxes: `nums[0]`, `nums[1]`, `nums[2]`.
- Inside each, smaller boxes for qubits used by each `QNum`.

## 6. `QStruct`: struct-like quantum types

A `QStruct` groups named quantum fields into a single type, similar to a classical struct.

Example:

```python
class MyState(QStruct):
    reg: QArray[QBit, 3]
    num: QNum[3, True, 1]
    flag: QBit
```

### 6.1 Allocating and accessing struct fields

[comment:]DO_NOT_TEST
```python
@qfunc
def struct_demo(state: Output[MyState]):
    allocate(state)        # allocate all fields at once

    hadamard_transform(state.reg)  # operate on the qubit array field
    hadamard_transform(state.num)  # operate on the numeric field

    # Example: compare numeric field and write to bit field
    state.flag ^= state.num < 0
```

Key points:

- `allocate(state)` uses the type definition to allocate all fields.
- Access fields with `state.<field_name>`.
- A struct is a single composite quantum object; fields are not re-bound individually.

### 6.2 Exercise 4: Portfolio-like struct

**Goal**: Create a simple struct for a financial-style example with:

- `reg`: 2-qubit register representing “asset ID”.
- `price`: 4-bit unsigned integer.
- `is_in_the_money`: one `QBit`.

**Tasks**

1. Define the struct type:

   ```python
   class PortfolioState(QStruct):
       reg: QArray[QBit, 2]
       price: QNum[4, False, 0]        # 4-qbit unsigned integer
       is_in_the_money: QBit
   ```

2. Allocate and initialize in a `@qfunc`:

   ```python
   @qfunc
   def portfolio_demo(state: Output[PortfolioState]):
       allocate(state)

       # Put all asset IDs in superposition
       hadamard_transform(state.reg)

       # Example: simple payoff rule, e.g. flag set if price > 5
       state.is_in_the_money ^= state.price > 5
   ```

3. Synthesize and sample.
4. Observe how the `is_in_the_money` flag correlates with the encoded `price`.

**Suggested figure (Figure 7)**  
Three labeled boxes in a row:

- `reg` (2 qubits)
- `price` (4 qubits)
- `is_in_the_money` (1 qubit)

## 7. Putting it together: mini-project

Use all discussed types in a small, self-contained model.

### 7.1 Project goal

Create a `QStruct` representing:

- A `QBit` control register.
- A 3-qubit unsigned integer value.

Then apply a conditional increment on the numeric field when the control register is in state `11`.

### 7.2 Implementation sketch

Define the struct:

```python
class ControlState(QStruct):
    ctrl: QBit
    val: QNum[3, False, 0]
```

Define the main quantum function:

```python
@qfunc
def conditional_increment(state: Output[ControlState]):
    allocate(state)

    # Prepare control register in equal superposition over 2 bits
    hadamard_transform(state.ctrl)

    # Conditionally increment val if ctrl == 3 (binary 11)
    control(state.ctrl == 3, lambda: (state.val |= state.val + 1))
```

Suggested workflow:

1. Synthesize and visualize:

   ```python
   qprog = synthesize(conditional_increment)
   show(qprog)
   ```

2. Run and sample:

   ```python
   with ExecutionSession(qprog) as es:
       res = es.sample()
       display(res.dataframe)
   ```

3. Inspect joint measurement outcomes of `ctrl` and `val`:
   - For `ctrl` ≠ `11`, `val` should remain unchanged.
   - For `ctrl` = `11`, you should see `val` incremented by 1.

**Suggested figure (Figure 9)**  
Circuit diagram:

- Top two qubits = `state.ctrl[0]`, `state.ctrl[1]` with H gates.
- A block labeled “+1” acting on the `val` qubits, controlled by both `ctrl` qubits.

---

## 9. Learning checklist

After completing this tutorial, you should be comfortable with:

- Distinguishing between quantum objects, types, and variables.
- Declaring and using:
  - `QBit` and `QArray[QBit]` with indexing and slicing.
  - `QNum` with explicit numeric attributes and numeric assignments.
  - `QArray[QNum]` and reasoning about element count vs qubit count.
  - `QStruct` for grouping heterogeneous quantum fields.
- Managing initialization using `Output`, `Input`, and local variables with `allocate`.
- Reading synthesized circuits and relating them to Qmod type declarations.

**Next steps**

- Extend examples with measurements and classical post-processing to compute expectations of numeric variables.
- Experiment with more complex arithmetic on `QNum` types and observe how type inference behaves under different expressions.
- Replace simple controlled operations with more advanced logic inside `control(…)` regions, still leveraging the same types and variable rules.
