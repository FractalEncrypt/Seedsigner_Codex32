"""Error correction for Codex32 strings.

This module implements error correction for codex32/BIP-93 strings using a
validated brute-force approach. Rather than implementing raw BCH decoding
(which requires exact polynomial alignment with codex32's specific construction),
we generate correction candidates and validate each using the codex32 library.

Advantages:
- Guaranteed correctness (uses proven checksum validation)
- Works with any codex32-compatible string
- Simpler and more maintainable

Trade-offs:
- Slower than algebraic BCH decoding for 3-4 errors
- Still practical for human error correction scenarios

Correction capacity (per BIP-93):
- Up to 4 substitution errors
- Up to 8 erasure errors (when positions are known)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Iterator
from itertools import combinations, product

from codex32 import Codex32String, CodexError
from codex32.bech32 import CHARSET


# Maximum errors to attempt correction
MAX_SUBSTITUTION_ERRORS = 4
MAX_ERASURE_ERRORS = 8


@dataclass
class CorrectionCandidate:
    """A potential correction for a codex32 string."""

    corrected_string: str
    original_string: str
    error_count: int
    error_positions: List[int]
    error_details: List[Tuple[int, str, str]]  # (position, original_char, corrected_char)


@dataclass
class CorrectionResult:
    """Result of error correction attempt."""

    success: bool
    candidates: List[CorrectionCandidate]
    error_message: Optional[str] = None


def _validate_codex32(s: str) -> bool:
    """Check if string is a valid codex32 share."""
    try:
        Codex32String(s)
        return True
    except CodexError:
        return False


def _generate_single_substitutions(
    s: str,
    start_pos: int = 3,  # Skip "ms1" prefix
) -> Iterator[Tuple[str, int, str, str]]:
    """Generate all single-character substitutions.

    Yields:
        (modified_string, position, original_char, new_char)
    """
    s_lower = s.lower()
    chars = list(s_lower)

    for pos in range(start_pos, len(chars)):
        original_char = chars[pos]
        for new_char in CHARSET:
            if new_char != original_char:
                chars[pos] = new_char
                yield "".join(chars), pos, original_char, new_char
                chars[pos] = original_char


def _generate_multi_substitutions(
    s: str,
    num_errors: int,
    start_pos: int = 3,
) -> Iterator[Tuple[str, List[Tuple[int, str, str]]]]:
    """Generate all combinations of num_errors substitutions.

    Yields:
        (modified_string, [(position, original_char, new_char), ...])
    """
    s_lower = s.lower()
    data_positions = list(range(start_pos, len(s_lower)))

    # For each combination of positions
    for positions in combinations(data_positions, num_errors):
        # Generate all possible character replacements
        original_chars = [s_lower[p] for p in positions]

        # For each position, get all possible replacement characters
        replacement_options = []
        for orig in original_chars:
            replacements = [c for c in CHARSET if c != orig]
            replacement_options.append(replacements)

        # Generate all combinations of replacements
        for new_chars in product(*replacement_options):
            chars = list(s_lower)
            changes = []
            for pos, orig, new in zip(positions, original_chars, new_chars):
                chars[pos] = new
                changes.append((pos, orig, new))
            yield "".join(chars), changes


def try_correct_errors(
    codex32_str: str,
    max_errors: int = MAX_SUBSTITUTION_ERRORS,
    stop_on_first: bool = False,
) -> CorrectionResult:
    """Attempt to correct errors in a codex32 string.

    Searches for valid corrections by trying substitutions at each position
    and validating with the codex32 library.

    Args:
        codex32_str: The potentially corrupted codex32 string
        max_errors: Maximum number of errors to attempt (1-4, default 4)
        stop_on_first: If True, return after finding first valid correction

    Returns:
        CorrectionResult with list of valid correction candidates
    """
    # Normalize and validate input
    s = (codex32_str or "").strip()
    if not s:
        return CorrectionResult(
            success=False,
            candidates=[],
            error_message="Empty input string",
        )

    # Check if already valid
    if _validate_codex32(s):
        return CorrectionResult(
            success=True,
            candidates=[
                CorrectionCandidate(
                    corrected_string=s,
                    original_string=s,
                    error_count=0,
                    error_positions=[],
                    error_details=[],
                )
            ],
        )

    # Clamp max_errors
    max_errors = min(max_errors, MAX_SUBSTITUTION_ERRORS)
    candidates = []

    # Try increasing numbers of errors
    for num_errors in range(1, max_errors + 1):
        if num_errors == 1:
            # Optimized path for single error
            for modified, pos, orig, new in _generate_single_substitutions(s):
                if _validate_codex32(modified):
                    candidate = CorrectionCandidate(
                        corrected_string=modified,
                        original_string=s,
                        error_count=1,
                        error_positions=[pos],
                        error_details=[(pos, orig, new)],
                    )
                    candidates.append(candidate)
                    if stop_on_first:
                        return CorrectionResult(success=True, candidates=candidates)
        else:
            # Multi-error case
            for modified, changes in _generate_multi_substitutions(s, num_errors):
                if _validate_codex32(modified):
                    positions = [c[0] for c in changes]
                    candidate = CorrectionCandidate(
                        corrected_string=modified,
                        original_string=s,
                        error_count=num_errors,
                        error_positions=positions,
                        error_details=changes,
                    )
                    candidates.append(candidate)
                    if stop_on_first:
                        return CorrectionResult(success=True, candidates=candidates)

        # If we found candidates at this error level, don't search higher
        # (Occam's razor - prefer simpler corrections)
        if candidates:
            break

    if candidates:
        return CorrectionResult(success=True, candidates=candidates)

    return CorrectionResult(
        success=False,
        candidates=[],
        error_message=f"No valid correction found with up to {max_errors} errors",
    )


def try_correct_with_erasures(
    codex32_str: str,
    erasure_positions: List[int],
) -> CorrectionResult:
    """Correct errors when some positions are known to be wrong (erasures).

    When the user marks positions as "unknown" or "unreadable", we only need
    to search those specific positions, making correction much faster.

    Args:
        codex32_str: The codex32 string with erasures
        erasure_positions: List of positions (0-indexed) that are known errors

    Returns:
        CorrectionResult with valid correction candidates
    """
    # Normalize and validate input
    s = (codex32_str or "").strip().lower()
    if not s:
        return CorrectionResult(
            success=False,
            candidates=[],
            error_message="Empty input string",
        )

    # Validate erasure count
    if len(erasure_positions) > MAX_ERASURE_ERRORS:
        return CorrectionResult(
            success=False,
            candidates=[],
            error_message=f"Too many erasures ({len(erasure_positions)}), max is {MAX_ERASURE_ERRORS}",
        )

    # Validate positions are within string
    for pos in erasure_positions:
        if pos < 0 or pos >= len(s):
            return CorrectionResult(
                success=False,
                candidates=[],
                error_message=f"Erasure position {pos} out of range",
            )

    candidates = []

    # Generate all possible characters for erasure positions
    for chars in product(CHARSET, repeat=len(erasure_positions)):
        test_str = list(s)
        changes = []

        for pos, new_char in zip(erasure_positions, chars):
            orig_char = test_str[pos]
            if new_char != orig_char:
                changes.append((pos, orig_char, new_char))
            test_str[pos] = new_char

        modified = "".join(test_str)

        if _validate_codex32(modified):
            candidate = CorrectionCandidate(
                corrected_string=modified,
                original_string=s,
                error_count=len(erasure_positions),
                error_positions=erasure_positions,
                error_details=changes,
            )
            candidates.append(candidate)

    if candidates:
        return CorrectionResult(success=True, candidates=candidates)

    return CorrectionResult(
        success=False,
        candidates=[],
        error_message="No valid correction found for given erasure positions",
    )


def format_correction_diff(candidate: CorrectionCandidate) -> str:
    """Format a correction showing the differences.

    Returns a string showing original vs corrected with markers.
    """
    lines = []
    lines.append(f"Original:  {candidate.original_string}")
    lines.append(f"Corrected: {candidate.corrected_string}")

    if candidate.error_details:
        lines.append(f"Changes ({candidate.error_count}):")
        for pos, orig, new in candidate.error_details:
            lines.append(f"  Position {pos}: '{orig}' -> '{new}'")

    return "\n".join(lines)


def estimate_search_space(string_length: int, max_errors: int) -> int:
    """Estimate the number of candidates to check.

    Useful for progress indication and timeout estimation.
    """
    from math import comb

    data_length = string_length - 3  # Exclude "ms1" prefix
    charset_size = len(CHARSET)  # 32

    total = 0
    for k in range(1, max_errors + 1):
        # C(n, k) * (31)^k  (31 alternative chars per position)
        total += comb(data_length, k) * (charset_size - 1) ** k

    return total
