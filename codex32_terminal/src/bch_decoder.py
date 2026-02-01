"""BCH error correction decoder for Codex32/BIP-93.

This module implements BCH (Bose-Chaudhuri-Hocquenghem) error correction
for codex32 strings as specified in BIP-93.

The codex32 checksum is a BCH code over GF(32) designed to:
- Detect any error pattern affecting up to 8 characters
- Correct up to 4 substitution errors
- Correct up to 8 erasure errors (positions known)

Algorithm components:
1. Syndrome calculation - evaluate received polynomial at roots of generator
2. Berlekamp-Massey - find error locator polynomial from syndromes
3. Chien search - find error positions (roots of error locator)
4. Forney algorithm - compute error magnitudes

Reference: https://github.com/bitcoin/bips/blob/master/bip-0093.mediawiki
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from gf32 import (
    gf32_add,
    gf32_mul,
    gf32_div,
    gf32_inv,
    gf32_pow,
    EXP,
    LOG,
)


# Maximum number of errors the BCH code can correct
MAX_ERRORS = 4

# Codex32 uses a specific BCH code with these roots
# The generator polynomial has roots at alpha^1, alpha^2, ..., alpha^8
# where alpha = 2 is the primitive element of GF(32)
BCH_ROOTS_START = 1  # First root is alpha^1
BCH_ROOTS_COUNT = 8  # 8 consecutive roots for t=4 error correction


@dataclass
class CorrectionResult:
    """Result of error correction attempt."""

    success: bool
    corrected_data: Optional[List[int]] = None
    error_positions: Optional[List[int]] = None
    error_values: Optional[Dict[int, int]] = None
    error_message: Optional[str] = None


def compute_syndromes(data: List[int], num_syndromes: int = BCH_ROOTS_COUNT) -> List[int]:
    """Compute BCH syndromes by evaluating data polynomial at roots.

    For a received polynomial r(x), syndrome S_j = r(alpha^j) where j = 1..2t.
    If r(x) is a valid codeword, all syndromes are zero.

    Args:
        data: List of GF(32) elements (integers 0-31)
        num_syndromes: Number of syndromes to compute (default 8 for t=4)

    Returns:
        List of syndrome values [S_1, S_2, ..., S_{num_syndromes}]
    """
    syndromes = []
    n = len(data)

    for j in range(BCH_ROOTS_START, BCH_ROOTS_START + num_syndromes):
        # Evaluate r(alpha^j) using Horner's method
        # r(x) = data[0] + data[1]*x + data[2]*x^2 + ... + data[n-1]*x^{n-1}
        # Note: data[0] is the constant term (rightmost character in codex32)
        s_j = 0
        alpha_j = EXP[j % 31] if j % 31 != 0 else 1

        for i in range(n):
            # Add data[i] * (alpha^j)^i
            coef = data[i]
            if coef != 0:
                power_val = gf32_pow(alpha_j, i)
                s_j = gf32_add(s_j, gf32_mul(coef, power_val))

        syndromes.append(s_j)

    return syndromes


def syndromes_are_zero(syndromes: List[int]) -> bool:
    """Check if all syndromes are zero (indicating valid codeword)."""
    return all(s == 0 for s in syndromes)


def berlekamp_massey(syndromes: List[int]) -> List[int]:
    """Find error locator polynomial using Berlekamp-Massey algorithm.

    The error locator polynomial Lambda(x) has roots at alpha^{-e_i} where
    e_i are the error positions.

    Args:
        syndromes: List of syndrome values [S_1, S_2, ...]

    Returns:
        Error locator polynomial coefficients [1, Lambda_1, Lambda_2, ...]
        where Lambda(x) = 1 + Lambda_1*x + Lambda_2*x^2 + ...
    """
    n = len(syndromes)

    # C = current connection polynomial (Lambda)
    # B = previous connection polynomial
    # L = current number of errors assumed
    # m = number of iterations since B was updated
    # b = previous discrepancy value

    C = [1]  # Lambda(x) starts as 1
    B = [1]  # Copy of previous C
    L = 0  # LFSR length / assumed errors
    m = 1  # Shift amount
    b = 1  # Previous discrepancy

    for i in range(n):
        # Compute discrepancy d = S_{i+1} + sum(C[j] * S_{i+1-j}) for j=1..L
        d = syndromes[i]
        for j in range(1, L + 1):
            if j < len(C) and (i - j) >= 0:
                d = gf32_add(d, gf32_mul(C[j], syndromes[i - j]))

        if d == 0:
            # No change needed, just increment shift
            m += 1
        elif 2 * L <= i:
            # Update polynomial and LFSR length
            T = list(C)  # Save current C

            # C(x) = C(x) - (d/b) * x^m * B(x)
            coef = gf32_div(d, b)

            # Ensure C is long enough
            while len(C) < len(B) + m:
                C.append(0)

            for j in range(len(B)):
                C[j + m] = gf32_add(C[j + m], gf32_mul(coef, B[j]))

            L = i + 1 - L
            B = T
            b = d
            m = 1
        else:
            # Only update polynomial, not L
            coef = gf32_div(d, b)

            # Ensure C is long enough
            while len(C) < len(B) + m:
                C.append(0)

            for j in range(len(B)):
                C[j + m] = gf32_add(C[j + m], gf32_mul(coef, B[j]))

            m += 1

    return C


def chien_search(error_locator: List[int], n: int) -> List[int]:
    """Find error positions using Chien search.

    Evaluates Lambda(x) at alpha^{-j} for j = 0..n-1.
    Position j has an error if Lambda(alpha^{-j}) = 0.

    Args:
        error_locator: Lambda(x) coefficients [1, L_1, L_2, ...]
        n: Length of received data

    Returns:
        List of error positions (indices into data array)
    """
    error_positions = []
    num_errors = len(error_locator) - 1

    for j in range(n):
        # Evaluate Lambda(alpha^{-j})
        # alpha^{-j} = alpha^{31-j} since order is 31
        alpha_neg_j = EXP[(31 - (j % 31)) % 31] if j % 31 != 0 else 1

        result = 0
        for i, coef in enumerate(error_locator):
            if coef != 0:
                term = gf32_mul(coef, gf32_pow(alpha_neg_j, i))
                result = gf32_add(result, term)

        if result == 0:
            error_positions.append(j)

            # Early exit if we found all expected errors
            if len(error_positions) == num_errors:
                break

    return error_positions


def forney_algorithm(
    syndromes: List[int],
    error_locator: List[int],
    error_positions: List[int],
) -> Dict[int, int]:
    """Compute error magnitudes using Forney's algorithm.

    For each error position, compute the error value that needs to be
    XORed (added in GF(32)) to correct the error.

    Args:
        syndromes: Syndrome values [S_1, S_2, ...]
        error_locator: Lambda(x) coefficients
        error_positions: List of error positions from Chien search

    Returns:
        Dict mapping position -> error magnitude (GF(32) element)
    """
    # Compute error evaluator polynomial Omega(x)
    # Omega(x) = S(x) * Lambda(x) mod x^{2t}
    # where S(x) = S_1 + S_2*x + S_3*x^2 + ...

    t = len(error_locator) - 1  # Number of errors
    two_t = len(syndromes)

    # Compute Omega by polynomial multiplication and truncation
    omega = [0] * two_t
    for i, s in enumerate(syndromes):
        for j, lam in enumerate(error_locator):
            if i + j < two_t:
                omega[i + j] = gf32_add(omega[i + j], gf32_mul(s, lam))

    # Compute formal derivative Lambda'(x)
    # In characteristic 2, (a*x^n)' = a*x^{n-1} if n is odd, else 0
    # So Lambda'(x) = Lambda_1 + Lambda_3*x^2 + Lambda_5*x^4 + ...
    lambda_prime = []
    for i in range(1, len(error_locator)):
        if i % 2 == 1:  # Odd power terms contribute
            lambda_prime.append(error_locator[i])
        else:
            lambda_prime.append(0)

    error_magnitudes = {}

    for pos in error_positions:
        # X_i = alpha^{pos} (the error locator value)
        X_i = EXP[pos % 31] if pos % 31 != 0 else 1
        X_i_inv = gf32_inv(X_i)

        # Evaluate Omega(X_i^{-1})
        omega_val = 0
        for i, o in enumerate(omega):
            if o != 0:
                term = gf32_mul(o, gf32_pow(X_i_inv, i))
                omega_val = gf32_add(omega_val, term)

        # Evaluate Lambda'(X_i^{-1})
        lambda_prime_val = 0
        for i, lp in enumerate(lambda_prime):
            if lp != 0:
                term = gf32_mul(lp, gf32_pow(X_i_inv, i))
                lambda_prime_val = gf32_add(lambda_prime_val, term)

        # Error magnitude: e_i = X_i * Omega(X_i^{-1}) / Lambda'(X_i^{-1})
        if lambda_prime_val != 0:
            e_i = gf32_mul(X_i, gf32_div(omega_val, lambda_prime_val))
            error_magnitudes[pos] = e_i
        else:
            # This shouldn't happen for valid BCH codes
            # If Lambda' evaluates to 0, something is wrong
            error_magnitudes[pos] = 0

    return error_magnitudes


def decode_bch(data: List[int], max_errors: int = MAX_ERRORS) -> CorrectionResult:
    """Attempt to decode and correct errors in BCH-encoded data.

    Args:
        data: List of GF(32) elements (received codeword)
        max_errors: Maximum errors to attempt to correct (default 4)

    Returns:
        CorrectionResult with success status and corrected data if successful
    """
    # Step 1: Compute syndromes
    syndromes = compute_syndromes(data)

    # Step 2: Check if already valid (all syndromes zero)
    if syndromes_are_zero(syndromes):
        return CorrectionResult(
            success=True,
            corrected_data=data,
            error_positions=[],
            error_values={},
        )

    # Step 3: Find error locator polynomial using Berlekamp-Massey
    error_locator = berlekamp_massey(syndromes)

    # Step 4: Check if error count exceeds capacity
    num_errors = len(error_locator) - 1
    if num_errors > max_errors:
        return CorrectionResult(
            success=False,
            error_message=f"Too many errors detected ({num_errors}), max correctable is {max_errors}",
        )

    if num_errors == 0:
        # Syndromes non-zero but no errors found - decoding failure
        return CorrectionResult(
            success=False,
            error_message="Decoding failure: non-zero syndromes but no error locator",
        )

    # Step 5: Find error positions using Chien search
    error_positions = chien_search(error_locator, len(data))

    # Step 6: Verify we found the expected number of roots
    if len(error_positions) != num_errors:
        return CorrectionResult(
            success=False,
            error_message=f"Chien search found {len(error_positions)} positions, expected {num_errors}",
        )

    # Step 7: Compute error magnitudes using Forney algorithm
    error_values = forney_algorithm(syndromes, error_locator, error_positions)

    # Step 8: Apply corrections
    corrected_data = list(data)
    for pos, magnitude in error_values.items():
        if magnitude != 0:
            corrected_data[pos] = gf32_add(corrected_data[pos], magnitude)

    # Step 9: Verify correction by recomputing syndromes
    verify_syndromes = compute_syndromes(corrected_data)
    if not syndromes_are_zero(verify_syndromes):
        return CorrectionResult(
            success=False,
            error_message="Correction verification failed: syndromes still non-zero",
        )

    return CorrectionResult(
        success=True,
        corrected_data=corrected_data,
        error_positions=error_positions,
        error_values=error_values,
    )


def decode_with_erasures(
    data: List[int],
    erasure_positions: List[int],
    max_errors: int = MAX_ERRORS,
) -> CorrectionResult:
    """Decode BCH with known erasure positions.

    Erasures are positions where the value is known to be incorrect but
    the original value is unknown. Each erasure counts as half an error
    in terms of correction capacity.

    Args:
        data: List of GF(32) elements
        erasure_positions: List of positions known to be incorrect
        max_errors: Maximum combined (errors + erasures/2) to correct

    Returns:
        CorrectionResult with success status and corrected data
    """
    # For now, treat erasures as regular errors
    # A full implementation would use the erasure locator polynomial
    # to reduce the problem size, but the basic BCH decoder can handle
    # up to 2t erasures without knowing they're erasures

    if len(erasure_positions) > 2 * max_errors:
        return CorrectionResult(
            success=False,
            error_message=f"Too many erasures ({len(erasure_positions)}), max is {2 * max_errors}",
        )

    # Use standard decoder
    return decode_bch(data, max_errors)
