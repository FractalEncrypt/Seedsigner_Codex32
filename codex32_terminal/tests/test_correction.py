"""Battle-tested error correction tests.

Tests verify edge cases, boundary conditions, and failure modes.
Uses stop_on_first=True where possible for speed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from error_correction import (
    try_correct_errors,
    try_correct_with_erasures,
    format_correction_diff,
    estimate_search_space,
    CorrectionCandidate,
    CorrectionResult,
)


# BIP-93 test vectors
VECTOR_48 = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"
VECTOR_74 = "ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycma"


def corrupt(s: str, pos: int, char: str) -> str:
    """Introduce error at position."""
    chars = list(s.lower())
    chars[pos] = char.lower()
    return "".join(chars)


# =============================================================================
# HAPPY PATH
# =============================================================================

def test_already_valid():
    """Valid strings return immediately."""
    result = try_correct_errors(VECTOR_48)
    assert result.success
    assert result.candidates[0].error_count == 0
    print("test_already_valid: PASS")


def test_single_error():
    """Single error is corrected."""
    corrupted = corrupt(VECTOR_48, 10, 'q')
    result = try_correct_errors(corrupted, max_errors=1, stop_on_first=True)
    assert result.success
    assert result.candidates[0].corrected_string.lower() == VECTOR_48.lower()
    print("test_single_error: PASS")


def test_256bit():
    """Works for 74-char strings."""
    corrupted = corrupt(VECTOR_74, 20, 'q')
    result = try_correct_errors(corrupted, max_errors=1, stop_on_first=True)
    assert result.success
    print("test_256bit: PASS")


# =============================================================================
# INPUT EDGE CASES
# =============================================================================

def test_empty_string():
    """Empty string fails with message."""
    result = try_correct_errors("")
    assert not result.success
    assert "empty" in result.error_message.lower()
    print("test_empty_string: PASS")


def test_whitespace_only():
    """Whitespace-only fails."""
    result = try_correct_errors("   \t\n")
    assert not result.success
    assert "empty" in result.error_message.lower()
    print("test_whitespace_only: PASS")


def test_none_input():
    """None handled gracefully."""
    result = try_correct_errors(None)  # type: ignore
    assert not result.success
    print("test_none_input: PASS")


def test_wrong_length():
    """Wrong length doesn't crash."""
    result = try_correct_errors("ms12tooshort", max_errors=1)
    assert isinstance(result, CorrectionResult)
    print("test_wrong_length: PASS")


def test_invalid_chars():
    """Invalid bech32 chars don't crash."""
    # 'b' not in bech32
    result = try_correct_errors("ms12namesbxqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evw", max_errors=1)
    assert isinstance(result, CorrectionResult)
    print("test_invalid_chars: PASS")


# =============================================================================
# POSITION EDGE CASES
# =============================================================================

def test_error_at_start():
    """Error at position 3 (first data char)."""
    corrupted = corrupt(VECTOR_48, 3, 'q')
    result = try_correct_errors(corrupted, max_errors=1, stop_on_first=True)
    assert result.success
    print("test_error_at_start: PASS")


def test_error_at_end():
    """Error at last position."""
    corrupted = corrupt(VECTOR_48, 47, 'q')
    result = try_correct_errors(corrupted, max_errors=1, stop_on_first=True)
    assert result.success
    print("test_error_at_end: PASS")


def test_error_in_prefix():
    """Error in ms1 prefix doesn't crash."""
    corrupted = "qs12names6xqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evw"
    result = try_correct_errors(corrupted, max_errors=1)
    assert isinstance(result, CorrectionResult)
    print("test_error_in_prefix: PASS")


# =============================================================================
# BOUNDARY CONDITIONS
# =============================================================================

def test_max_errors_zero():
    """max_errors=0 only validates."""
    corrupted = corrupt(VECTOR_48, 10, 'q')
    result = try_correct_errors(corrupted, max_errors=0)
    # Should not find correction with 0 max errors
    assert not result.success or result.candidates[0].error_count == 0
    print("test_max_errors_zero: PASS")


def test_max_errors_clamped():
    """max_errors>4 clamped to 4."""
    corrupted = corrupt(VECTOR_48, 10, 'q')
    result = try_correct_errors(corrupted, max_errors=100, stop_on_first=True)
    assert result.success
    print("test_max_errors_clamped: PASS")


def test_stop_on_first():
    """stop_on_first returns single candidate."""
    corrupted = corrupt(VECTOR_48, 10, 'q')
    result = try_correct_errors(corrupted, max_errors=1, stop_on_first=True)
    assert len(result.candidates) == 1
    print("test_stop_on_first: PASS")


# =============================================================================
# ERASURE TESTS
# =============================================================================

def test_erasure_basic():
    """Erasure correction works."""
    corrupted = corrupt(VECTOR_48, 10, 'q')
    result = try_correct_with_erasures(corrupted, [10])
    assert result.success
    found = any(c.corrected_string.lower() == VECTOR_48.lower() for c in result.candidates)
    assert found
    print("test_erasure_basic: PASS")


def test_erasure_empty_list():
    """Empty erasure list on valid string."""
    result = try_correct_with_erasures(VECTOR_48, [])
    assert result.success
    print("test_erasure_empty_list: PASS")


def test_erasure_negative_pos():
    """Negative position fails gracefully."""
    result = try_correct_with_erasures(VECTOR_48, [-1])
    assert not result.success
    assert "range" in result.error_message.lower() or "position" in result.error_message.lower()
    print("test_erasure_negative_pos: PASS")


def test_erasure_out_of_range():
    """Position beyond string fails."""
    result = try_correct_with_erasures(VECTOR_48, [1000])
    assert not result.success
    print("test_erasure_out_of_range: PASS")


def test_erasure_too_many():
    """More than 8 erasures fails."""
    result = try_correct_with_erasures(VECTOR_48, list(range(3, 12)))  # 9 positions
    assert not result.success
    assert "too many" in result.error_message.lower() or "max" in result.error_message.lower()
    print("test_erasure_too_many: PASS")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def test_format_diff():
    """Diff formatting works."""
    candidate = CorrectionCandidate(
        corrected_string="ms12names6xqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evw",
        original_string="ms12names6xqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evx",
        error_count=1,
        error_positions=[47],
        error_details=[(47, 'x', 'w')],
    )
    diff = format_correction_diff(candidate)
    assert "Original:" in diff
    assert "Corrected:" in diff
    print("test_format_diff: PASS")


def test_search_space():
    """Search space math is correct."""
    # 48-char string, 1 error: (48-3 data chars) * 31 alternatives = 1395
    # The "ms1" prefix (3 chars) is excluded from error correction
    assert estimate_search_space(48, 1) == (48 - 3) * 31
    print("test_search_space: PASS")


def test_case_insensitive():
    """Case doesn't matter."""
    upper = try_correct_errors(corrupt(VECTOR_48, 10, 'Q'), max_errors=1, stop_on_first=True)
    lower = try_correct_errors(corrupt(VECTOR_48.lower(), 10, 'q'), max_errors=1, stop_on_first=True)
    assert upper.success and lower.success
    assert upper.candidates[0].corrected_string.lower() == lower.candidates[0].corrected_string.lower()
    print("test_case_insensitive: PASS")


def main():
    """Run all tests."""
    test_already_valid()
    test_single_error()
    test_256bit()
    test_empty_string()
    test_whitespace_only()
    test_none_input()
    test_wrong_length()
    test_invalid_chars()
    test_error_at_start()
    test_error_at_end()
    test_error_in_prefix()
    test_max_errors_zero()
    test_max_errors_clamped()
    test_stop_on_first()
    test_erasure_basic()
    test_erasure_empty_list()
    test_erasure_negative_pos()
    test_erasure_out_of_range()
    test_erasure_too_many()
    test_format_diff()
    test_search_space()
    test_case_insensitive()
    print("\n=== All 22 tests passed! ===")


if __name__ == "__main__":
    main()
