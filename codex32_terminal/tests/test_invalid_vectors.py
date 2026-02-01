"""Test rejection of BIP-93 invalid test vectors."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import Codex32InputError, parse_codex32_share


# BIP-93 Invalid Test Vectors
# https://github.com/bitcoin/bips/blob/master/bip-0093.mediawiki#user-content-Invalid_test_vectors

INVALID_VECTORS = [
    # Invalid checksum (single character errors)
    {
        "codex32": "ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlx",
        "reason": "Invalid checksum - last char changed",
    },
    {
        "codex32": "ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczla",
        "reason": "Invalid checksum - last char changed",
    },
    # Threshold 1 is not valid (must be 0 or 2-9)
    {
        "codex32": "ms11testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw",
        "reason": "Threshold '1' is invalid",
    },
    # Share index must be 's' when threshold is 0
    {
        "codex32": "ms10testaxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlw",
        "reason": "Share index must be 's' when k=0",
    },
]

# These should fail checksum validation
CHECKSUM_FAIL_VECTORS = [
    "ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczlx",
    "ms10testsxxxxxxxxxxxxxxxxxxxxxxxxxx4nzvca9cmczla",
    "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVX",
]


def test_invalid_checksum_vectors():
    """Test that invalid checksum vectors are rejected."""
    for vector in CHECKSUM_FAIL_VECTORS:
        try:
            # Use expected_len=None to skip length check, focus on checksum
            parse_codex32_share(vector, expected_len=None)
            raise AssertionError(f"Should have rejected: {vector}")
        except Codex32InputError:
            pass  # Expected

    print(f"test_invalid_checksum_vectors: PASS ({len(CHECKSUM_FAIL_VECTORS)} vectors rejected)")


def test_bip93_invalid_vectors():
    """Test all BIP-93 invalid test vectors are rejected."""
    passed = 0
    for vector in INVALID_VECTORS:
        try:
            parse_codex32_share(vector["codex32"], expected_len=None)
            print(f"FAIL: Should have rejected - {vector['reason']}")
            print(f"       Input: {vector['codex32']}")
        except Codex32InputError:
            passed += 1

    assert passed == len(INVALID_VECTORS), (
        f"Only {passed}/{len(INVALID_VECTORS)} invalid vectors were rejected"
    )
    print(f"test_bip93_invalid_vectors: PASS ({passed} vectors rejected)")


def test_corrupted_single_char():
    """Test that single character corruption is detected."""
    valid = "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW"

    # Test corruption at key positions:
    # 0=HRP start, 5=threshold, 10=identifier, 20=payload middle,
    # 30=payload, 40=near checksum, 47=last char (checksum)
    positions_to_test = [0, 5, 10, 20, 30, 40, 47]
    corruptions_detected = 0

    for pos in positions_to_test:
        # Change character at position
        char_list = list(valid)
        original_char = char_list[pos]
        # Pick a different bech32 char
        new_char = 'Q' if original_char != 'Q' else 'P'
        char_list[pos] = new_char
        corrupted = ''.join(char_list)

        try:
            parse_codex32_share(corrupted, expected_len=None)
        except Codex32InputError:
            corruptions_detected += 1

    assert corruptions_detected == len(positions_to_test), (
        f"Only detected {corruptions_detected}/{len(positions_to_test)} corruptions"
    )
    print(f"test_corrupted_single_char: PASS ({corruptions_detected} corruptions detected)")


def main():
    test_invalid_checksum_vectors()
    test_bip93_invalid_vectors()
    test_corrupted_single_char()
    print("\nAll invalid vector tests passed!")


if __name__ == "__main__":
    main()
