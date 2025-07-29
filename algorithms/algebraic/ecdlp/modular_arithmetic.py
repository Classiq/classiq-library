"""
Quantum Modular Arithmetic Functions for Elliptic Curve Cryptography

This module contains reversible quantum implementations of modular arithmetic operations
required for elliptic curve point addition and scalar multiplication using Classiq.

All functions maintain quantum reversibility and use proper auxiliary qubit management
following the compute-uncompute pattern.
"""

from classiq import *


# Basic Modular Arithmetic Operations


@qfunc
def modular_in_place_add(x: QNum, y: QNum, modulus: int) -> None:
    """
    Reversible, in-place modular addition of two integers modulo a constant integer modulus.
    Given two n-bit integers x and y encoded in quantum registers `x` and `y`, and a constant integer `modulus`,
    this function computes the sum (x + y) mod modulus in a reversible manner.
    The result is stored in-place in the `y` register.

    Args:
        x (QNum): Quantum register encoding the first integer addend (x).
        y (QNum): Quantum register encoding the second integer addend (y).
                  This register will be updated in-place to hold the modular sum.
        modulus (int): Constant integer modulus for the modular addition.
    """
    # Use a carry qubit to detect overflow
    carry = QBit("carry")
    allocate(1, carry)

    # Create temporary register that combines y and carry
    res_and_carry = QNum("res_and_carry", y.size + 1, SIGNED, 0)

    # Compute-uncompute pattern for reversible arithmetic
    within_apply(
        # COMPUTE: Bind y and carry into combined register
        lambda: bind([y, carry], res_and_carry),
        # APPLY: Perform modular arithmetic operations
        lambda: (
            inplace_add(x, res_and_carry),  # Add x to the combined register
            inplace_add(-modulus, res_and_carry),  # Subtract modulus to check overflow
        ),
    )
    # UNCOMPUTE: y and carry are automatically separated

    # If carry is set (negative result), add modulus back to y
    control(carry, lambda: inplace_add(modulus, y))

    # Update carry qubit based on comparison (y >= x after operation)
    control(y >= x, lambda: X(carry))

    # Clean up auxiliary qubit
    free(carry)


@qfunc
def check_if_all_zero(x: QArray[QBit], ancilla: QBit) -> None:
    """
    Sets the ancilla qubit to 1 if all qubits in the quantum array `x` are zero, otherwise sets it to 0.
    Uses within_apply to handle the compute/uncompute of X gates.
    """
    within_apply(lambda: apply_to_all(X, x), lambda: control(x, lambda: X(ancilla)))


@qfunc
def check_if_all_ones(x: QArray[QBit], ancilla: QBit) -> None:
    """
    Sets the ancilla qubit to 1 if all qubits in the quantum array `x` are one, otherwise sets it to 0.
    """
    control(x, lambda: X(ancilla))


@qfunc
def bitwise_negation(arr: QArray[QBit]) -> None:
    """
    Applies an X gate (bitwise NOT) to each qubit in the quantum array `arr`.
    """
    apply_to_all(X, arr)


@qfunc
def modular_in_place_negate(x: QNum, modulus: int) -> None:
    """
    Reversible, in-place modular negation of an integer modulo a constant integer modulus.
    Given an n-bit integer x encoded in quantum register `x`, and a constant integer `modulus`,
    this function computes (-x) mod modulus and stores the result in-place in `x`.

    Algorithm:
    1. Check if x is all zeros (special case)
    2. If x=0, set x to modulus, otherwise compute complement
    3. Apply bitwise negation to get final result

    Args:
        x (QNum): Quantum numeric register to be negated in-place.
        modulus (int): Constant integer modulus.
    """
    n = x.size
    neg_modulus = 2**n - modulus - 1

    is_all_zeros = QBit("is_all_zeros")
    allocate(1, is_all_zeros)

    # Test if the input is all-zeros
    check_if_all_zero(x, is_all_zeros)

    # If all-zeros, then put the modulus in x
    control(is_all_zeros, lambda: inplace_add(modulus, x))

    # Add neg_modulus to x
    inplace_add(neg_modulus, x)

    # If x=0, then we have neg_modulus + modulus = all ones
    check_if_all_ones(x, is_all_zeros)

    # Bitwise negation: set x to (neg_modulus + x)'
    bitwise_negation(x)

    free(is_all_zeros)


@qfunc
def modular_in_place_subtract(x: QNum, y: QNum, modulus: int) -> None:
    """
    Reversible, in-place modular subtraction of two integers modulo a constant integer modulus.
    Given two n-bit integers x and y encoded in quantum registers `x` and `y`, and a constant integer `modulus`,
    this function computes the difference (x - y) mod modulus in a reversible manner.
    The result is stored in-place in the `y` register.
    |x>|y> -> |x>|(x-y) % p>

    Algorithm:
    1. Compute (-y) mod modulus in-place on y
    2. Compute x + (-y) mod modulus in-place on y

    Args:
        x (QNum): Quantum register encoding the first integer operand (x).
        y (QNum): Quantum register encoding the second integer operand (y).
                  This register will be updated in-place to hold the modular difference.
        modulus (int): Constant integer modulus for the modular subtraction.
    """
    # Compute -y mod modulus in-place on y
    modular_in_place_negate(y, modulus)
    # Compute x + (-y) mod modulus in-place on y
    modular_in_place_add(x, y, modulus)


# Constant Operations


@qfunc
def modular_in_place_add_constant(x: QNum, constant: int, modulus: int) -> None:
    """
    Computes (x + constant) mod modulus in-place on x.
    Uses a single carry qubit to check if we need to subtract modulus.

    This function demonstrates key quantum arithmetic techniques:
    1. Auxiliary qubits for overflow detection
    2. Compute-uncompute patterns for reversibility
    3. Conditional modular reduction

    Args:
        x (QNum): The quantum register to add to.
        constant (int): The classical integer constant to add.
        modulus (int): The integer modulus.
    """
    # Allocate a single carry qubit
    carry = QBit("carry")
    allocate(1, carry)

    # Create and allocate temporary register to hold x + carry
    temp = QNum("temp", x.size + 1, SIGNED, 0)

    # Bind x and carry into temp for addition
    within_apply(
        lambda: bind([x, carry], temp),
        lambda: (
            # Add constant to temp
            inplace_add(constant, temp),
            # Add -modulus to temp to check for overflow
            inplace_add(-modulus, temp),
        ),
    )

    # If carry is set, we need to add modulus back
    control(carry, lambda: inplace_add(modulus, x))
    control(x >= constant, lambda: X(carry))

    # Free the temporary registers
    free(carry)


# Doubling and Shifting


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
def modular_in_place_double(x: QNum, modulus: int) -> None:
    """
    Doubles the value in the quantum register `x` (computes 2x), then reduces it modulo `modulus`.
    Uses an ancilla qubit `carry` to capture overflow from the doubling operation, and updates
    the carry using the least significant bit of x.

    Algorithm:
    1. Use carry qubit to extend register size
    2. Perform left shift (multiplication by 2)
    3. Subtract modulus to check for overflow
    4. Conditionally add modulus back if needed
    5. Update carry based on LSB analysis

    Args:
        x (QNum): Quantum register to be doubled and reduced modulo `modulus`.
        modulus (int): Constant integer modulus for the modular reduction.
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

    # Update carry based on LSB of original x
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
    free(carry)


# Multiplication Operations


@qfunc
def modular_out_of_place_multiply(
    x: QArray[QBit], y: QArray[QBit], z: QArray[QBit], modulus: int
) -> None:
    """
    Reversible, out-of-place modular multiplication of two integers modulo a constant integer modulus.
    Given two n-bit integers x and y encoded in quantum bit arrays `x` and `y`, and a constant integer `modulus`,
    this function computes the product (x * y) mod modulus. The result is held in the third register `z`,
    which must be initialized to |0⟩.

    Algorithm (Double-and-Add for Multiplication):
    1. For each bit of x (from MSB to LSB):
       - If bit is 1: add y to accumulator z
       - Double z for next iteration (except last)
    2. Perform modular reduction at each step

    Args:
        x (QArray[QBit]): Quantum bit array encoding the first integer x.
        y (QArray[QBit]): Quantum bit array encoding the second integer y.
        z (QArray[QBit]): Quantum bit array for the result. Must be in state |0⟩ initially.
        modulus (int): Constant integer modulus.

    References:
        Based on Section 4.3.2 of Proos & Zalka: "Shor's discrete logarithm quantum algorithm
        for elliptic curves", https://arxiv.org/abs/quant-ph/0301141
    """
    n = x.size
    for idx in reversed(range(n)):
        # If x[idx] = 1, add y to z (controlled addition)
        control(x[idx], lambda: modular_in_place_add(y, z, modulus))
        # Double z for next iteration (except for the last iteration)
        if idx != 0:
            modular_in_place_double(z, modulus)


@qfunc
def modular_out_of_place_square(x: QArray[QBit], z: QArray[QBit], p: int) -> None:
    """
    Modular squaring of x modulo p, storing result in z.

    Implements x^2 mod p using controlled modular addition and doubling.
    The algorithm is based on the Q# ModularSquDblAddConstantModulus operation.

    Algorithm (Optimized Double-and-Add for Squaring):
    1. For each bit i of x (from MSB-1 down to 1):
       - If x[i] = 1: add x to accumulator z
       - Double z for next iteration
    2. For the LSB (bit 0):
       - If x[0] = 1: add x to accumulator z
       - No doubling after LSB
    3. All operations performed modulo p

    Args:
        x: Input quantum bit array to be squared
        z: Output quantum bit array to store x^2 mod p
        p: Classical modulus value

    Note: This is more efficient than general multiplication since we're
    multiplying x by itself, allowing for optimized bit processing.
    """
    n = x.size
    assert z.size == n, "Output register z must have the same number of qubits as x"

    anc = QBit("anc")
    allocate(1, anc)

    # Process bits from MSB-1 down to 1
    for i in range(n - 1, 0, -1):
        control(x[i], lambda: X(anc))
        control(anc, lambda: modular_in_place_add(x, z, p))
        control(x[i], lambda: X(anc))
        modular_in_place_double(z, p)

    # Process LSB (bit 0) - no doubling after this
    control(x[0], lambda: X(anc))
    control(anc, lambda: modular_in_place_add(x, z, p))
    control(x[0], lambda: X(anc))

    free(anc)


# Modular Inverse (Mock Implementation for Educational Purposes)


@qfunc
def _set_value(reg: QNum, value: int) -> None:
    """Helper function to set a value in a quantum register."""
    reg ^= value


@qfunc
def mock_inverse_modulus_7(x: QNum, result: QNum) -> None:
    """
    Mock implementation for modular inverse modulo 7.
    For input x in range 1-6, computes x^(-1) mod 7.
    The modular inverses modulo 7 are:
    1^(-1) = 1 mod 7
    2^(-1) = 4 mod 7
    3^(-1) = 5 mod 7
    4^(-1) = 2 mod 7
    5^(-1) = 3 mod 7
    6^(-1) = 6 mod 7

    Algorithm (Lookup Table using Controlled Operations):
    Uses a series of controlled operations to implement the inverse mapping.
    Each control checks for a specific input value and sets the corresponding inverse.

    Args:
        x (QNum): Input quantum number (should be in range 1-6)
        result (QNum): Output quantum number to store the inverse

    Note: This is a simplified implementation for educational purposes.
    A production implementation would use Kaliski's quantum modular inverse algorithm.
    """
    # Use a series of controlled operations to set the correct inverse
    # For x = 1: result = 1
    control(x == 1, lambda: _set_value(result, 1))

    # For x = 2: result = 4
    control(x == 2, lambda: _set_value(result, 4))

    # For x = 3: result = 5
    control(x == 3, lambda: _set_value(result, 5))

    # For x = 4: result = 2
    control(x == 4, lambda: _set_value(result, 2))

    # For x = 5: result = 3
    control(x == 5, lambda: _set_value(result, 3))

    # For x = 6: result = 6
    control(x == 6, lambda: _set_value(result, 6))
