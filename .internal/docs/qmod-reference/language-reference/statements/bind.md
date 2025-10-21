---
search:
    boost: 3.183
---

# Bind

The _bind_ statement (operator `->`) is used to rewire the qubits referenced by one
or more source variables to one or more destination variables. In accordance
with the no-cloning principle, the source variables, which are initialized prior
to the bind statement, become uninitialized subsequently. You can use the `bind` statement
to split one quantum object into multiple objects and to join multiple objects into one.
You can also use it to reinterpret a numeric object as a qubit array and vice versa.

## Syntax

=== "Python"

    [comment]: DO_NOT_TEST
    ```python
    def bind(
        source: Union[Input[QVar], List[Input[QVar]]],
        destination: Union[Output[QVar], List[Output[QVar]]],
    ) -> None:
        pass
    ```

=== "Native"

    _source-var-list_ **->** _destination-var-list_

    _source-var-list_ and _destination-var-list_ are either a single quantum variable or
    a list of one or more comma-separated quantum variables enclosed in **{**  **}**

## Semantics

-   Prior to a `bind` statement variables in _source-var-list_ must be initialized and
    variables in _destination-var-list_ must be uninitialized.
-   Following a `bind` statement variables in _source-var-list_ are uninitialized and
    variables in _destination-var-list_ are initialized.
-   If more than one variable is listed in _destination-var-list_, the overall size in bits
    of each variable must be known. This is required to determine the partition of qubits between them.
    -   `qnum` variables must have a declared or previously inferred size.
    -   `qbit[]` variables must have a declared or previously inferred length.
-   The sum of sizes associated with variables in _destination-var-list_ must agree with
    the overall number of qubits actually used by variables in _source-var-list_.
-   Following a `bind` statement qubits are rewired from the source variable(s) to
    the respective position in the destination variable(s).

Note that the `bind` statement is only rewiring qubits across model variables and has no
resource footprint (additional gates or auxiliary qubits) on the resulting circuit.

## Examples

### Example 1: Cast

The following example demonstrates how to use the `bind` statement to cast
a numeric variable to a qubit array and cast back. In it, all bits of some number are
flipped. Accessing qubits cannot be performed directly on a `qnum` variable. Therefore,
`x` is bound to a `qbit[]` variable to perform the operation and subsequently
bound back.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def main(x: Output[QNum]) -> None:
        x |= 5
        qba = QArray()
        bind(x, qba)
        repeat(qba.len, lambda i: X(qba[i]))
        bind(qba, x)
    ```

=== "Native"

    ```
    qfunc main(output x: qnum) {
      x = 5;
      qba: qbit[];
      x -> qba;
      repeat (i: qba.len) {
        X(qba[i]);
      }
      qba -> x;
    }
    ```

### Example 2: Split and join

The following example demonstrates how to apply an operation on a specific qubit
of a numeric variable. In function `xor_lsb` the LSB (least significant bit) of
argument
`x` is the target of a `CX` operation. This is done by splitting it from `x`
while
keeping the rest of the qubits in `msbs` and subsequently joining `x` back.

=== "Python"

    ```python
    from classiq import *


    @qfunc
    def xor_lsb(x: QNum, xor_bit: QBit):
        lsb = QNum("lsb", 1, UNSIGNED, 1)
        msbs = QArray("msbs", QBit, x.size - 1)
        bind(x, [lsb, msbs])
        CX(xor_bit, lsb)
        bind([lsb, msbs], x)


    @qfunc
    def main(x: Output[QNum]) -> None:
        x |= 5
        xor_bit = QBit()
        allocate(xor_bit)
        H(xor_bit)
        xor_lsb(x, xor_bit)
    ```

=== "Native"

    ```
    qfunc xor_lsb(x: qnum, xor_bit: qbit) {
      lsb: qnum<1, UNSIGNED, 1>;
      msbs: qbit[x.size - 1];
      x -> {lsb, msbs};
      CX(xor_bit, lsb);
      {lsb, msbs} -> x;
    }

    qfunc main(output x: qnum) {
      x = 5;
      xor_bit: qbit;
      allocate(xor_bit);
      H(xor_bit);
      xor_lsb(x, xor_bit);
    }
    ```

In the overall model, function `main` calls `xor_lsb` with the number 5. Its output
is the uniform distribution of 5 and 4, correlative to the `xor_bit` being 0 and 1.
Below is the visualization of the resulting quantum program.

![xor_lsb.png](resources/xor_lsb.png)
