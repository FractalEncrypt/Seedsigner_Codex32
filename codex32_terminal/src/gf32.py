"""GF(32) Galois Field arithmetic for Codex32 BCH error correction.

This module implements arithmetic operations in GF(32) = GF(2^5),
the finite field used by Codex32/BIP-93 for its BCH error-correcting code.

Field specification (from BIP-93):
- Polynomial: x^5 + x^3 + 1 (irreducible over GF(2))
- Primitive element: alpha = 2 (generator of multiplicative group)
- Field elements: 0-31 (5-bit integers)
- Multiplicative group order: 31 (prime, so all non-zero elements are generators)

Reference: https://github.com/bitcoin/bips/blob/master/bip-0093.mediawiki
"""

from __future__ import annotations


# Bech32 character set (maps integers 0-31 to characters)
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

# Reverse mapping: character -> integer
CHARSET_REV = {c: i for i, c in enumerate(CHARSET)}


# Logarithm table for GF(32)
# LOG[x] = discrete log base alpha of x (for x != 0)
# alpha = 2 is the primitive element
# Computed as: alpha^LOG[x] = x
#
# LOG[0] is undefined (set to -1 as sentinel)
# LOG[1] = 0 because alpha^0 = 1
# LOG[2] = 1 because alpha^1 = 2
# etc.
LOG = [
    -1,  # 0 (undefined)
    0,   # 1 = alpha^0
    1,   # 2 = alpha^1
    18,  # 3 = alpha^18
    2,   # 4 = alpha^2
    5,   # 5 = alpha^5
    19,  # 6 = alpha^19
    11,  # 7 = alpha^11
    3,   # 8 = alpha^3
    29,  # 9 = alpha^29
    6,   # 10 = alpha^6
    27,  # 11 = alpha^27
    20,  # 12 = alpha^20
    8,   # 13 = alpha^8
    12,  # 14 = alpha^12
    23,  # 15 = alpha^23
    4,   # 16 = alpha^4
    10,  # 17 = alpha^10
    30,  # 18 = alpha^30
    17,  # 19 = alpha^17
    7,   # 20 = alpha^7
    22,  # 21 = alpha^22
    28,  # 22 = alpha^28
    26,  # 23 = alpha^26
    21,  # 24 = alpha^21
    25,  # 25 = alpha^25
    9,   # 26 = alpha^9
    16,  # 27 = alpha^16
    13,  # 28 = alpha^13
    14,  # 29 = alpha^14
    24,  # 30 = alpha^24
    15,  # 31 = alpha^15
]

# Exponentiation table (inverse of LOG)
# EXP[i] = alpha^i (mod the field polynomial)
# Since the multiplicative group has order 31, EXP[i] = EXP[i mod 31]
# We extend to 62 entries to avoid modular arithmetic in hot paths
EXP = [
    1,   # alpha^0
    2,   # alpha^1
    4,   # alpha^2
    8,   # alpha^3
    16,  # alpha^4
    5,   # alpha^5 = 32 mod (x^5+x^3+1) = 5
    10,  # alpha^6
    20,  # alpha^7
    13,  # alpha^8 = 40 mod poly = 13
    26,  # alpha^9
    17,  # alpha^10 = 52 mod poly = 17
    7,   # alpha^11
    14,  # alpha^12
    28,  # alpha^13
    29,  # alpha^14 = 56 mod poly = 29
    31,  # alpha^15
    27,  # alpha^16 = 62 mod poly = 27
    19,  # alpha^17
    3,   # alpha^18 = 38 mod poly = 3
    6,   # alpha^19
    12,  # alpha^20
    24,  # alpha^21
    21,  # alpha^22 = 48 mod poly = 21
    15,  # alpha^23
    30,  # alpha^24
    25,  # alpha^25 = 60 mod poly = 25
    23,  # alpha^26
    11,  # alpha^27
    22,  # alpha^28
    9,   # alpha^29 = 44 mod poly = 9
    18,  # alpha^30
    # Wrap around (alpha^31 = alpha^0 = 1)
    1, 2, 4, 8, 16, 5, 10, 20, 13, 26, 17, 7, 14, 28, 29, 31,
    27, 19, 3, 6, 12, 24, 21, 15, 30, 25, 23, 11, 22, 9, 18,
]


def gf32_add(a: int, b: int) -> int:
    """Add two GF(32) elements.

    In characteristic-2 fields, addition is XOR.
    """
    return a ^ b


def gf32_sub(a: int, b: int) -> int:
    """Subtract two GF(32) elements.

    In characteristic-2 fields, subtraction equals addition (XOR).
    """
    return a ^ b


def gf32_mul(a: int, b: int) -> int:
    """Multiply two GF(32) elements using log/exp tables.

    a * b = alpha^(log(a) + log(b))
    """
    if a == 0 or b == 0:
        return 0
    # Use extended EXP table to avoid modulo
    return EXP[LOG[a] + LOG[b]]


def gf32_div(a: int, b: int) -> int:
    """Divide a by b in GF(32).

    a / b = alpha^(log(a) - log(b))

    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero in GF(32)")
    if a == 0:
        return 0
    # Add 31 before subtraction to keep result positive
    return EXP[(LOG[a] - LOG[b]) % 31]


def gf32_inv(a: int) -> int:
    """Multiplicative inverse of a in GF(32).

    inv(a) = alpha^(-log(a)) = alpha^(31 - log(a))

    Raises:
        ZeroDivisionError: If a is zero
    """
    if a == 0:
        raise ZeroDivisionError("Zero has no multiplicative inverse")
    return EXP[31 - LOG[a]]


def gf32_pow(a: int, n: int) -> int:
    """Raise a to power n in GF(32).

    a^n = alpha^(n * log(a))
    """
    if a == 0:
        return 0 if n > 0 else 1
    if n == 0:
        return 1
    # Handle negative exponents
    if n < 0:
        a = gf32_inv(a)
        n = -n
    return EXP[(LOG[a] * n) % 31]


def char_to_int(c: str) -> int:
    """Convert a bech32 character to its integer value (0-31).

    Args:
        c: Single bech32 character (case-insensitive)

    Returns:
        Integer 0-31

    Raises:
        ValueError: If character is not in bech32 charset
    """
    c_lower = c.lower()
    if c_lower not in CHARSET_REV:
        raise ValueError(f"Invalid bech32 character: {c!r}")
    return CHARSET_REV[c_lower]


def int_to_char(i: int, uppercase: bool = False) -> str:
    """Convert an integer (0-31) to its bech32 character.

    Args:
        i: Integer 0-31
        uppercase: If True, return uppercase character

    Returns:
        Bech32 character

    Raises:
        ValueError: If i is not in range 0-31
    """
    if not 0 <= i <= 31:
        raise ValueError(f"Integer must be 0-31, got {i}")
    c = CHARSET[i]
    return c.upper() if uppercase else c


def verify_tables() -> bool:
    """Verify LOG and EXP tables are consistent.

    This is a self-test function to ensure tables were computed correctly.

    Returns:
        True if tables are valid

    Raises:
        AssertionError: If tables are inconsistent
    """
    # Verify EXP[LOG[x]] = x for all x != 0
    for x in range(1, 32):
        assert EXP[LOG[x]] == x, f"EXP[LOG[{x}]] = {EXP[LOG[x]]} != {x}"

    # Verify LOG[EXP[i]] = i for i in 0..30
    for i in range(31):
        assert LOG[EXP[i]] == i, f"LOG[EXP[{i}]] = {LOG[EXP[i]]} != {i}"

    # Verify multiplication is commutative
    for a in range(32):
        for b in range(32):
            assert gf32_mul(a, b) == gf32_mul(b, a), f"mul({a},{b}) not commutative"

    # Verify inverse property: a * inv(a) = 1
    for a in range(1, 32):
        assert gf32_mul(a, gf32_inv(a)) == 1, f"{a} * inv({a}) != 1"

    # Verify distributive property: a * (b + c) = a*b + a*c
    for a in range(32):
        for b in range(32):
            for c in range(32):
                lhs = gf32_mul(a, gf32_add(b, c))
                rhs = gf32_add(gf32_mul(a, b), gf32_mul(a, c))
                assert lhs == rhs, f"Distributive failed for {a},{b},{c}"

    return True
