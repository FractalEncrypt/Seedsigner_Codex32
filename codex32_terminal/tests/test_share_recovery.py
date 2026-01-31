"""Test share recovery using BIP-93 test vectors."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import (
    parse_codex32_share,
    recover_secret_share,
    codex32_to_seed_bytes,
    seed_bytes_to_mnemonic,
)


# BIP-93 Test Vector 2: 2-of-n shares
VECTOR2_SHARES = {
    "A": "MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDCAXRPP870HKKQRM",
    "C": "MS12NAMECACDEFGHJKLMNPQRSTUVWXYZ023FTR2GDZMPY6PN",
}
VECTOR2_EXPECTED = {
    "s_share": "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW",
    "seed_hex": "d1808e096b35b209ca12132b264662a5",
    "mnemonic": "spice afford liquid stool forest agent choose draw clinic cram obvious enough",
}

# BIP-93 Test Vector 3: 3-of-n shares
VECTOR3_SHARES = {
    "A": "ms13casha320zyxwvutsrqpnmlkjhgfedca2a8d0zehn8a0t",
    "C": "ms13cashcacdefghjklmnpqrstuvwxyz023949xq35my48dr",
    "D": "ms13cashd0wsedstcdcts64cd7wvy4m90lm28w4ffupqs7rm",
}
VECTOR3_EXPECTED = {
    "s_share": "ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln",
    "seed_hex": "ffeeddccbbaa99887766554433221100",
    "mnemonic": "zoo ivory industry jar praise service talk skirt during october lounge absurd",
}


def test_vector2_share_recovery():
    """Test 2-of-n share recovery with BIP-93 Vector 2."""
    shares = [
        parse_codex32_share(VECTOR2_SHARES["A"]),
        parse_codex32_share(VECTOR2_SHARES["C"]),
    ]

    secret = recover_secret_share(shares)
    assert secret.s == VECTOR2_EXPECTED["s_share"], (
        f"S-share mismatch: got {secret.s}, expected {VECTOR2_EXPECTED['s_share']}"
    )

    seed_bytes = codex32_to_seed_bytes(secret.s)
    assert seed_bytes.hex() == VECTOR2_EXPECTED["seed_hex"], (
        f"Seed mismatch: got {seed_bytes.hex()}, expected {VECTOR2_EXPECTED['seed_hex']}"
    )

    mnemonic = seed_bytes_to_mnemonic(seed_bytes)
    assert mnemonic == VECTOR2_EXPECTED["mnemonic"], (
        f"Mnemonic mismatch: got {mnemonic}"
    )

    print("test_vector2_share_recovery: PASS")


def test_vector3_share_recovery():
    """Test 3-of-n share recovery with BIP-93 Vector 3."""
    shares = [
        parse_codex32_share(VECTOR3_SHARES["A"]),
        parse_codex32_share(VECTOR3_SHARES["C"]),
        parse_codex32_share(VECTOR3_SHARES["D"]),
    ]

    secret = recover_secret_share(shares)
    assert secret.s.lower() == VECTOR3_EXPECTED["s_share"].lower(), (
        f"S-share mismatch: got {secret.s}, expected {VECTOR3_EXPECTED['s_share']}"
    )

    seed_bytes = codex32_to_seed_bytes(secret.s)
    assert seed_bytes.hex() == VECTOR3_EXPECTED["seed_hex"], (
        f"Seed mismatch: got {seed_bytes.hex()}, expected {VECTOR3_EXPECTED['seed_hex']}"
    )

    mnemonic = seed_bytes_to_mnemonic(seed_bytes)
    assert mnemonic == VECTOR3_EXPECTED["mnemonic"], (
        f"Mnemonic mismatch: got {mnemonic}"
    )

    print("test_vector3_share_recovery: PASS")


def test_vector3_different_share_combination():
    """Test that any valid 3-of-n combination recovers the same secret."""
    # We can also derive share E and F from the S-share, but for this test
    # we just verify A+C+D works (which we already know from above)
    # This test confirms the interpolation is deterministic

    shares_acd = [
        parse_codex32_share(VECTOR3_SHARES["A"]),
        parse_codex32_share(VECTOR3_SHARES["C"]),
        parse_codex32_share(VECTOR3_SHARES["D"]),
    ]

    # Try different order - should get same result
    shares_dca = [
        parse_codex32_share(VECTOR3_SHARES["D"]),
        parse_codex32_share(VECTOR3_SHARES["C"]),
        parse_codex32_share(VECTOR3_SHARES["A"]),
    ]

    secret_acd = recover_secret_share(shares_acd)
    secret_dca = recover_secret_share(shares_dca)

    assert secret_acd.s.lower() == secret_dca.s.lower(), (
        "Share order should not affect recovery result"
    )

    print("test_vector3_different_share_combination: PASS")


def main():
    test_vector2_share_recovery()
    test_vector3_share_recovery()
    test_vector3_different_share_combination()
    print("\nAll share recovery tests passed!")


if __name__ == "__main__":
    main()
