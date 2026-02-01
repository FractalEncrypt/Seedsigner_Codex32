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


def test_invalid_bech32_characters_rejected():
    """Test that invalid bech32 characters are rejected.

    Bech32 alphabet excludes: 1, b, i, o (to avoid confusion).
    The '1' is only valid as the HRP separator.
    """
    # 'b' is not in bech32 alphabet - inject it into a valid string
    # Valid: MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW
    with_b = "MS12NAMbS6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"

    try:
        parse_codex32_share(with_b)
        raise AssertionError("Should have rejected string with 'b'")
    except Codex32InputError:
        pass  # Expected - invalid character or checksum failure

    # 'i' is not in bech32 alphabet
    with_i = "MS12NAMiS6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"

    try:
        parse_codex32_share(with_i)
        raise AssertionError("Should have rejected string with 'i'")
    except Codex32InputError:
        pass  # Expected

    # 'o' is not in bech32 alphabet
    with_o = "MS12NAMoS6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"

    try:
        parse_codex32_share(with_o)
        raise AssertionError("Should have rejected string with 'o'")
    except Codex32InputError:
        pass  # Expected

    print("test_invalid_bech32_characters_rejected: PASS")


def test_mixed_case_rejected():
    """Test that mixed case (upper and lower in same string) is rejected.

    Bech32 requires consistent case throughout the string.
    """
    # Mix upper and lower - should fail
    mixed = "MS12names6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"

    try:
        parse_codex32_share(mixed)
        raise AssertionError("Should have rejected mixed case input")
    except Codex32InputError:
        pass  # Expected - mixed case or checksum failure

    print("test_mixed_case_rejected: PASS")


def test_none_input_returns_empty_error():
    """Test that None input is handled gracefully."""
    try:
        parse_codex32_share(None)
        raise AssertionError("Should have rejected None input")
    except Codex32InputError as e:
        assert "empty" in str(e).lower(), f"Error should mention empty: {e}"

    print("test_none_input_returns_empty_error: PASS")


def test_wrong_hrp_rejected():
    """Test that wrong HRP (human-readable part) is rejected.

    Codex32 requires 'ms' as the HRP.
    """
    # Change HRP from 'ms' to 'bc' (Bitcoin address HRP)
    wrong_hrp = "BC12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"

    try:
        parse_codex32_share(wrong_hrp)
        raise AssertionError("Should have rejected wrong HRP")
    except Codex32InputError as e:
        # Should fail - either wrong HRP or checksum
        pass

    print("test_wrong_hrp_rejected: PASS")


def main():
    test_invalid_checksum_rejected()
    test_wrong_length_rejected()
    test_empty_input_rejected()
    test_non_s_share_rejected_for_s_share_validation()
    test_sanitize_input()
    test_valid_share_accepted()
    test_case_insensitive_but_consistent()
    test_invalid_bech32_characters_rejected()
    test_mixed_case_rejected()
    test_none_input_returns_empty_error()
    test_wrong_hrp_rejected()
    print("\nAll validation tests passed!")


if __name__ == "__main__":
    main()
