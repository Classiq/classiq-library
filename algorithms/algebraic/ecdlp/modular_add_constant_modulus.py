from classiq import (
    qfunc,
    QNum,
    QBit,
    SIGNED,
    allocate,
    within_apply,
    bind,
    inplace_add,
    control,
    X,
    SWAP,
    QArray,
    apply_to_all,
    create_model,
    synthesize,
)
from classiq.qmod.symbolic import log, ceiling


@qfunc
def modolu_adder(x: QNum, y: QNum, modulus: int) -> None:
    """
    Reversible, in-place modular addition of two integers modulo a constant integer modulus.

    Given two n-bit integers x and y encoded in quantum registers `x` and `y`, and a constant integer `modulus`,
    this function computes the sum (x + y) mod modulus in a reversible manner. The result is stored in-place in the `y` register.
    An additional qubit `carry` is allocated internally as an ancilla to detect overflow during the modular reduction step.

    # Input
    - x: QNum
        Quantum register encoding the first integer addend (x).
    - y: QNum
        Quantum register encoding the second integer addend (y). This register will be updated in-place to hold the modular sum.
    - modulus: int
        Constant integer modulus for the modular addition.

    # Output
    - The modular sum (x + y) mod modulus is stored in-place in the `y` register.
    """
    res_and_carry = QNum("res_and_carry", 4, SIGNED, 0)
    carry = QBit("carry")
    allocate(1, carry)
    within_apply(
        lambda: bind([y, carry], res_and_carry),
        lambda: (
            inplace_add(x, res_and_carry),
            inplace_add(-modulus, res_and_carry),
        ),
    )
    # Now y and carry are split again
    control(carry, lambda: inplace_add(modulus, y))
    control(y >= x, lambda: X(carry))


@qfunc
def shift_left(reg: QArray[QBit]) -> None:
    """
    Performs a logical left shift on the quantum register array `reg` using SWAP gates.
    The most significant bit is set to 0, and all other bits are shifted left by one position.
    This is equivalent to multiplication by 2.
    """
    n = reg.size
    # Shift bits left using SWAP gates
    for i in reversed(range(1, n)):
        SWAP(reg[i], reg[i - 1])


@qfunc
def shift_right(reg: QArray[QBit]) -> None:
    """
    Performs a logical right shift on the quantum register array `reg` using SWAP gates.
    The least significant bit is set to 0, and all other bits are shifted right by one position.
    This is equivalent to integer division by 2 (rounding down).
    """
    n = reg.size
    # Shift bits right using SWAP gates
    for i in range(n - 1):
        SWAP(reg[i], reg[i + 1])


@qfunc
def modolu_double(x: QNum, modulus: int) -> None:
    """
    Doubles the value in the quantum register `x` (computes 2x), then reduces it modulo `modulus`.
    Uses an ancilla qubit `carry` to capture overflow from the doubling operation, and updates the carry using the least significant bit of x.

    # Input
    - x: QNum
        Quantum register to be doubled and reduced modulo `modulus`.
    - modulus: int
        Constant integer modulus for the modular reduction.

    # Output
    - The value (2x) % modulus is stored in-place in `x`.
    - The carry qubit is updated based on the least significant bit of x after the operation.
    """
    carry = QBit("carry")
    allocate(1, carry)
    res_and_carry = QNum("res_and_carry", x.size + 1, SIGNED, 0)
    within_apply(
        lambda: bind([x, carry], res_and_carry),
        lambda: (
            shift_left(res_and_carry),  # holds 2*x
            inplace_add(-modulus, res_and_carry),
        ),
    )
    control(carry, lambda: inplace_add(modulus, x))
    lsb = QNum("lsb", 1)
    rest = QNum("rest", x.size - 1)
    within_apply(
        lambda: bind(x, [lsb, rest]),
        lambda: (
            X(lsb),
            CX(lsb, carry),
            X(lsb),
        ),
    )


@qfunc
def modolu_multiply(
    modulus: int, x: QArray[QBit], y: QArray[QBit], z: QArray[QBit]
) -> None:
    """
    Reversible, out-of-place modular multiplication of two integers modulo a constant integer modulus.
    Given two n-bit integers x and y encoded in quantum bit arrays `x` and `y`, and a constant integer `modulus`,
    this function computes the product (x * y) mod modulus. The result is held in the third register `z`, which must be initialized to |0>.

    # Input
    - modulus: int
        Constant integer modulus.
    - x: QArray[QBit]
        Quantum bit array encoding the first integer x.
    - y: QArray[QBit]
        Quantum bit array encoding the second integer y.
    - z: QArray[QBit]
        Quantum bit array for the result. Must be in state |0> initially.

    # References
    An algorithm for multiplying two numbers modulo a constant is sketched in Section 4.3.2 of
    John Proos, Christof Zalka : "Shor's discrete logarithm quantum algorithm for elliptic curves", 2003.
    https://arxiv.org/abs/quant-ph/0301141/

    # Remarks
    The operation uses the naive approach of modular doublings and controlled modular additions as in the ModularMulDblAdd operation above.
    It only works correctly for odd moduli.
    """
    n = x.size
    for idx in reversed(range(n)):
        control(x[idx], lambda: modolu_adder(modulus, y, z))
        if idx != 0:
            modolu_double(z, modulus)


@qfunc
def modular_negate(modulus: int, x: QNum) -> None:
    """
    Reversible, in-place modular negation of an integer modulo a constant integer modulus.
    Given an n-bit integer x encoded in quantum register `x`, and a constant integer `modulus`,
    this function computes (-x) mod modulus and stores the result in-place in `x`.

    Args:
        modulus (int): Constant integer modulus.
        x (QNum): Quantum numeric register to be negated in-place.
    """
    n = x.size
    neg_modulus = 2**n - modulus - 1
    is_all_zeros = QBit("is_all_zeros")
    allocate(1, is_all_zeros)
    # Test if the input is all-zeros
    check_if_all_zero(x, is_all_zeros)
    # If all-zeros, then put the modulus in x
    control(is_all_zeros, lambda: inplace_add(modulus, x))
    # Adds neg_modulus to x
    inplace_add(neg_modulus, x)
    # If x=0, then we m' + m = all ones
    check_if_all_ones(x, is_all_zeros)
    # Bitwise negation: set x to (m'+x)'
    bitwise_negation(x)


@qfunc
def check_if_all_zero(x: QArray[QBit], ancilla: QBit) -> None:
    """
    Sets the ancilla qubit to 1 if all qubits in the quantum array `x` are zero, otherwise sets it to 0.
    Uses within_apply to handle the compute/uncompute of X gates.

    Args:
        x (QArray[QBit]): Quantum array to check for all zeros.
        ancilla (QBit): Ancilla qubit to store the result (1 if all zero, else 0).
    """
    within_apply(lambda: apply_to_all(X, x), lambda: control(x, lambda: X(ancilla)))


@qfunc
def check_if_all_ones(x: QArray[QBit], ancilla: QBit) -> None:
    """
    Sets the ancilla qubit to 1 if all qubits in the quantum array `x` are one, otherwise sets it to 0.

    Args:
        x (QArray[QBit]): Quantum array to check for all ones.
        ancilla (QBit): Ancilla qubit to store the result (1 if all one, else 0).
    """
    control(x, lambda: X(ancilla))


@qfunc
def bitwise_negation(arr: QArray[QBit]) -> None:
    """
    Applies an X gate (bitwise NOT) to each qubit in the quantum array `arr`.

    Args:
        arr (QArray[QBit]): Quantum array to be bitwise negated.
    """
    apply_to_all(X, arr)


@qfunc
def modulo_subtract(x: QNum, y: QNum, modulus: int) -> None:
    """
    Reversible, in-place modular subtraction of two integers modulo a constant integer modulus.

    Given two n-bit integers x and y encoded in quantum registers `x` and `y`, and a constant integer `modulus`,
    this function computes the difference (x - y) mod modulus in a reversible manner. The result is stored in-place in the `y` register.

    Args:
        x (QNum): Quantum register encoding the first integer operand (x).
        y (QNum): Quantum register encoding the second integer operand (y). This register will be updated in-place to hold the modular difference.
        modulus (int): Constant integer modulus for the modular subtraction.

    Output:
        The modular difference (x - y) mod modulus is stored in-place in the `y` register.
    """
    # Compute -y mod modulus in-place on y
    modular_negate(modulus, y)
    # Compute x + (-y) mod modulus in-place on y
    modolu_adder(x, y, modulus)


# Create and synthesize the model
# qmod = create_model(main)
# qprog = synthesize(qmod)
