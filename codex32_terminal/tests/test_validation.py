"""Test input validation and error handling."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import (
    Codex32InputError,
    parse_codex32_share,
    validate_codex32_s_share,
    codex32_to_seed_bytes,
    sanitize_codex32_input,
)


def test_invalid_checksum_rejected():
    """Test that an invalid checksum is rejected."""
    # Valid: MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW
    # Changed last char W -> X
    invalid = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVX"

    try:
        parse_codex32_share(invalid)
        raise AssertionError("Should have rejected invalid checksum")
    except Codex32InputError as e:
        assert "checksum" in str(e).lower(), f"Error should mention checksum: {e}"

    print("test_invalid_checksum_rejected: PASS")


def test_wrong_length_rejected():
    """Test that wrong length inputs are rejected."""
    # Too short (47 chars instead of 48)
    too_short = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EV"

    try:
        parse_codex32_share(too_short, expected_len=48)
        raise AssertionError("Should have rejected too-short input")
    except Codex32InputError as e:
        assert "48" in str(e), f"Error should mention expected length: {e}"

    # Too long (49 chars)
    too_long = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVWW"

    try:
        parse_codex32_share(too_long, expected_len=48)
        raise AssertionError("Should have rejected too-long input")
    except Codex32InputError as e:
        assert "48" in str(e), f"Error should mention expected length: {e}"

    print("test_wrong_length_rejected: PASS")


def test_empty_input_rejected():
    """Test that empty input is rejected."""
    try:
        parse_codex32_share("")
        raise AssertionError("Should have rejected empty input")
    except Codex32InputError as e:
        assert "empty" in str(e).lower(), f"Error should mention empty: {e}"

    try:
        parse_codex32_share("   ")
        raise AssertionError("Should have rejected whitespace-only input")
    except Codex32InputError as e:
        assert "empty" in str(e).lower(), f"Error should mention empty: {e}"

    print("test_empty_input_rejected: PASS")


def test_non_s_share_rejected_for_s_share_validation():
    """Test that non-S shares are rejected when S-share is required."""
    # This is share A, not share S
    share_a = "MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDCAXRPP870HKKQRM"

    try:
        validate_codex32_s_share(share_a)
        raise AssertionError("Should have rejected non-S share")
    except Codex32InputError as e:
        assert "s" in str(e).lower(), f"Error should mention share index: {e}"

    print("test_non_s_share_rejected_for_s_share_validation: PASS")


def test_sanitize_input():
    """Test that input sanitization works correctly."""
    # Should strip whitespace
    assert sanitize_codex32_input("  MS12NAME  ") == "MS12NAME"

    # Should remove dashes
    assert sanitize_codex32_input("MS12-NAME-S6XQ") == "MS12NAMES6XQ"

    # Should handle None
    assert sanitize_codex32_input(None) == ""

    # Should join split input
    assert sanitize_codex32_input("MS12 NAME S6XQ") == "MS12NAMES6XQ"

    print("test_sanitize_input: PASS")


def test_valid_share_accepted():
    """Test that valid shares are accepted."""
    # S-share
    s_share = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"
    result = validate_codex32_s_share(s_share)
    assert result is not None
    assert result.share_idx.lower() == "s"

    # Regular share (not S)
    share_a = "MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDCAXRPP870HKKQRM"
    result = parse_codex32_share(share_a)
    assert result is not None
    assert result.share_idx.lower() == "a"

    print("test_valid_share_accepted: PASS")


def test_case_insensitive_but_consistent():
    """Test that both cases work but must be consistent."""
    # Uppercase
    upper = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"
    result_upper = parse_codex32_share(upper)
    assert result_upper is not None

    # Lowercase
    lower = "ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln"
    result_lower = parse_codex32_share(lower)
    assert result_lower is not None

    print("test_case_insensitive_but_consistent: PASS")


def main():
    test_invalid_checksum_rejected()
    test_wrong_length_rejected()
    test_empty_input_rejected()
    test_non_s_share_rejected_for_s_share_validation()
    test_sanitize_input()
    test_valid_share_accepted()
    test_case_insensitive_but_consistent()
    print("\nAll validation tests passed!")


if __name__ == "__main__":
    main()
