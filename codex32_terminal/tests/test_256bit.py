"""Test 256-bit seed support (BIP-93 Test Vector 4)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from embit import bip39

from model import (
    Codex32InputError,
    parse_codex32_share,
    validate_codex32_s_share,
    codex32_to_seed_bytes,
    seed_bytes_to_mnemonic,
    codex32_to_mnemonic,
    VALID_LENGTHS,
)


# BIP-93 Test Vector 4: 256-bit seed
VECTOR4 = {
    "codex32": "ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycma",
    "seed_hex": "ffeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100",
    "mnemonic": "zoo ivory industry jar praise service talk skirt during october lounge acid year humble cream inspire office dry sunset pride drip much dune arm",
    "length": 74,
    "seed_bytes": 32,
    "word_count": 24,
}

# BIP-93 Test Vector 2: 128-bit seed (for comparison)
VECTOR2 = {
    "codex32": "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW",
    "seed_hex": "d1808e096b35b209ca12132b264662a5",
    "length": 48,
    "seed_bytes": 16,
    "word_count": 12,
}


def test_valid_lengths_constant():
    """Test that VALID_LENGTHS maps correctly."""
    assert 48 in VALID_LENGTHS, "48 should be a valid length"
    assert 74 in VALID_LENGTHS, "74 should be a valid length"
    assert VALID_LENGTHS[48] == 16, "48 chars should map to 16 bytes"
    assert VALID_LENGTHS[74] == 32, "74 chars should map to 32 bytes"
    print("test_valid_lengths_constant: PASS")


def test_256bit_parse():
    """Test parsing a 256-bit codex32 string."""
    codex = parse_codex32_share(VECTOR4["codex32"])
    assert codex is not None
    assert len(codex.s) == VECTOR4["length"]
    print("test_256bit_parse: PASS")


def test_256bit_validate_s_share():
    """Test validating a 256-bit S-share."""
    codex = validate_codex32_s_share(VECTOR4["codex32"])
    assert codex is not None
    assert codex.share_idx.lower() == "s"
    assert len(codex.data) == VECTOR4["seed_bytes"]
    print("test_256bit_validate_s_share: PASS")


def test_256bit_seed_extraction():
    """Test extracting seed bytes from 256-bit codex32."""
    seed_bytes = codex32_to_seed_bytes(VECTOR4["codex32"])
    assert seed_bytes.hex() == VECTOR4["seed_hex"], (
        f"Seed mismatch: got {seed_bytes.hex()}, expected {VECTOR4['seed_hex']}"
    )
    assert len(seed_bytes) == 32, f"Expected 32 bytes, got {len(seed_bytes)}"
    print("test_256bit_seed_extraction: PASS")


def test_256bit_to_mnemonic():
    """Test converting 256-bit seed to 24-word mnemonic."""
    mnemonic = codex32_to_mnemonic(VECTOR4["codex32"])
    words = mnemonic.split()
    assert len(words) == VECTOR4["word_count"], (
        f"Expected {VECTOR4['word_count']} words, got {len(words)}"
    )
    assert mnemonic == VECTOR4["mnemonic"], (
        f"Mnemonic mismatch: got {mnemonic}"
    )
    print(f"test_256bit_to_mnemonic: PASS ({len(words)} words)")


def test_128bit_still_works():
    """Test that 128-bit seeds still work (regression test)."""
    seed_bytes = codex32_to_seed_bytes(VECTOR2["codex32"])
    assert seed_bytes.hex() == VECTOR2["seed_hex"]

    mnemonic = codex32_to_mnemonic(VECTOR2["codex32"])
    words = mnemonic.split()
    assert len(words) == VECTOR2["word_count"], (
        f"Expected {VECTOR2['word_count']} words, got {len(words)}"
    )
    print(f"test_128bit_still_works: PASS ({len(words)} words)")


def test_auto_detect_length():
    """Test that length auto-detection works for both sizes."""
    # 128-bit
    codex_128 = parse_codex32_share(VECTOR2["codex32"])  # No expected_len
    assert len(codex_128.data) == 16

    # 256-bit
    codex_256 = parse_codex32_share(VECTOR4["codex32"])  # No expected_len
    assert len(codex_256.data) == 32

    print("test_auto_detect_length: PASS")


def test_invalid_length_rejected():
    """Test that invalid lengths are rejected."""
    # Too short (47 chars)
    try:
        parse_codex32_share("MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EV")
        raise AssertionError("Should have rejected 47-char input")
    except Codex32InputError:
        pass

    # Wrong length (50 chars - neither 48 nor 74)
    try:
        parse_codex32_share("MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVWXX")
        raise AssertionError("Should have rejected 50-char input")
    except Codex32InputError:
        pass

    print("test_invalid_length_rejected: PASS")


def test_seed_bytes_to_mnemonic_both_sizes():
    """Test seed_bytes_to_mnemonic handles both 16 and 32 bytes."""
    # 16 bytes -> 12 words
    seed_16 = bytes.fromhex(VECTOR2["seed_hex"])
    mnemonic_12 = seed_bytes_to_mnemonic(seed_16)
    assert len(mnemonic_12.split()) == 12

    # 32 bytes -> 24 words
    seed_32 = bytes.fromhex(VECTOR4["seed_hex"])
    mnemonic_24 = seed_bytes_to_mnemonic(seed_32)
    assert len(mnemonic_24.split()) == 24

    # Invalid size should fail
    try:
        seed_bytes_to_mnemonic(bytes(20))  # 20 bytes is not valid
        raise AssertionError("Should have rejected 20-byte seed")
    except Codex32InputError:
        pass

    print("test_seed_bytes_to_mnemonic_both_sizes: PASS")


def test_256bit_invalid_checksum_rejected():
    """Test that 256-bit strings with invalid checksums are rejected."""
    # Valid: ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycma
    # Change last character to corrupt checksum
    invalid = "ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycmx"

    try:
        parse_codex32_share(invalid)
        raise AssertionError("Should have rejected invalid 256-bit checksum")
    except Codex32InputError:
        pass

    print("test_256bit_invalid_checksum_rejected: PASS")


def test_256bit_single_char_corruption():
    """Test that single character corruption is detected in 256-bit strings."""
    valid = "ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycma"

    # Test corruption at key positions:
    # 0=HRP, 10=identifier, 30=payload middle, 50=payload, 73=last char (checksum)
    positions = [0, 10, 30, 50, 73]
    corruptions_detected = 0

    for pos in positions:
        char_list = list(valid)
        original = char_list[pos]
        # Pick a different bech32 char
        char_list[pos] = 'q' if original != 'q' else 'p'
        corrupted = ''.join(char_list)

        try:
            parse_codex32_share(corrupted)
        except Codex32InputError:
            corruptions_detected += 1

    assert corruptions_detected == len(positions), (
        f"Only detected {corruptions_detected}/{len(positions)} corruptions"
    )
    print(f"test_256bit_single_char_corruption: PASS ({corruptions_detected} detected)")


def test_73_char_length_rejected():
    """Test that 73 characters (one short of 256-bit) is rejected."""
    # 73 chars - too short for 256-bit
    too_short = "ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycm"

    try:
        parse_codex32_share(too_short)
        raise AssertionError("Should have rejected 73-char input")
    except Codex32InputError:
        pass

    print("test_73_char_length_rejected: PASS")


def test_75_char_length_rejected():
    """Test that 75 characters (one more than 256-bit) is rejected."""
    # 75 chars - too long for 256-bit
    too_long = "ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycmaa"

    try:
        parse_codex32_share(too_long)
        raise AssertionError("Should have rejected 75-char input")
    except Codex32InputError:
        pass

    print("test_75_char_length_rejected: PASS")


def test_mnemonic_words_are_valid_bip39():
    """Test that generated mnemonic words are valid BIP39 words."""
    # 256-bit mnemonic
    mnemonic = codex32_to_mnemonic(VECTOR4["codex32"])

    # Verify each word is in BIP39 wordlist
    for word in mnemonic.split():
        assert word in bip39.WORDLIST, f"'{word}' is not a valid BIP39 word"

    # 128-bit mnemonic
    mnemonic_128 = codex32_to_mnemonic(VECTOR2["codex32"])
    for word in mnemonic_128.split():
        assert word in bip39.WORDLIST, f"'{word}' is not a valid BIP39 word"

    print("test_mnemonic_words_are_valid_bip39: PASS")


def main():
    test_valid_lengths_constant()
    test_256bit_parse()
    test_256bit_validate_s_share()
    test_256bit_seed_extraction()
    test_256bit_to_mnemonic()
    test_128bit_still_works()
    test_auto_detect_length()
    test_invalid_length_rejected()
    test_seed_bytes_to_mnemonic_both_sizes()
    test_256bit_invalid_checksum_rejected()
    test_256bit_single_char_corruption()
    test_73_char_length_rejected()
    test_75_char_length_rejected()
    test_mnemonic_words_are_valid_bip39()
    print("\nAll 256-bit tests passed!")


if __name__ == "__main__":
    main()
