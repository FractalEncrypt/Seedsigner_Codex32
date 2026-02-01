"""Core Codex32 S-share validation and conversion helpers."""

from __future__ import annotations

from codex32 import Codex32String, CodexError
from embit import bip39


# Valid codex32 string lengths and corresponding seed sizes
# 48 chars = 128-bit seed (16 bytes) = 12-word mnemonic
# 74 chars = 256-bit seed (32 bytes) = 24-word mnemonic
VALID_LENGTHS = {48: 16, 74: 32}


class Codex32InputError(ValueError):
    """Raised when a codex32 input fails validation."""


def sanitize_codex32_input(raw: str) -> str:
    """Normalize user input by removing whitespace and separators."""
    if raw is None:
        return ""
    compact = "".join(raw.split())
    return compact.replace("-", "")


def parse_codex32_share(codex_str: str, expected_len: int | None = None) -> Codex32String:
    """Parse and validate a codex32 share string (checksum + header).

    Args:
        codex_str: The codex32 string to parse
        expected_len: Expected length (48 or 74), or None to auto-detect
    """
    cleaned = sanitize_codex32_input(codex_str)
    if not cleaned:
        raise Codex32InputError("Codex32 input is empty")

    # Validate length
    if expected_len is not None:
        if expected_len not in VALID_LENGTHS:
            raise Codex32InputError(
                f"Invalid expected_len {expected_len}, must be 48 (128-bit) or 74 (256-bit)"
            )
        if len(cleaned) != expected_len:
            raise Codex32InputError(
                f"Expected {expected_len} characters, got {len(cleaned)}"
            )
    else:
        # Auto-detect: must be a valid length
        if len(cleaned) not in VALID_LENGTHS:
            raise Codex32InputError(
                f"Invalid length {len(cleaned)}, expected 48 (128-bit) or 74 (256-bit)"
            )

    try:
        codex = Codex32String(cleaned)
    except CodexError as exc:
        raise Codex32InputError(str(exc)) from exc
    if codex.hrp != "ms":
        raise Codex32InputError(f"Unsupported HRP '{codex.hrp}', expected 'ms'")
    return codex


def validate_codex32_s_share(codex_str: str, expected_len: int | None = None) -> Codex32String:
    """Validate a codex32 S-share string and return a Codex32String object.

    Args:
        codex_str: The codex32 string to validate
        expected_len: Expected length (48 or 74), or None to auto-detect
    """
    codex = parse_codex32_share(codex_str, expected_len)
    if codex.share_idx.lower() != "s":
        raise Codex32InputError(
            f"Share index must be 's' for an unshared secret, got '{codex.share_idx}'"
        )
    # Validate seed size matches expected length
    expected_bytes = VALID_LENGTHS.get(len(codex.s))
    if expected_bytes is not None and len(codex.data) != expected_bytes:
        raise Codex32InputError(
            f"Expected {expected_bytes}-byte seed for {len(codex.s)}-char string, "
            f"got {len(codex.data)} bytes"
        )
    return codex


def codex32_to_seed_bytes(codex_str: str) -> bytes:
    """Convert a codex32 S-share string into seed entropy (16 or 32 bytes)."""
    codex = validate_codex32_s_share(codex_str)
    return codex.data


def seed_bytes_to_mnemonic(seed_bytes: bytes) -> str:
    """Convert seed entropy to a BIP39 mnemonic.

    Args:
        seed_bytes: 16 bytes (128-bit) for 12 words, or 32 bytes (256-bit) for 24 words
    """
    if len(seed_bytes) == 16:
        return bip39.mnemonic_from_bytes(seed_bytes)  # 12 words
    elif len(seed_bytes) == 32:
        return bip39.mnemonic_from_bytes(seed_bytes)  # 24 words
    else:
        raise Codex32InputError(
            f"Expected 16 bytes (12 words) or 32 bytes (24 words), got {len(seed_bytes)} bytes"
        )


def codex32_to_mnemonic(codex_str: str) -> str:
    """Convert a codex32 S-share into a BIP39 mnemonic (12 or 24 words)."""
    return seed_bytes_to_mnemonic(codex32_to_seed_bytes(codex_str))


def recover_secret_share(shares: list[Codex32String]) -> Codex32String:
    """Recover the secret share (index 's') from a set of codex32 shares."""
    if not shares:
        raise Codex32InputError("No shares provided for recovery")
    try:
        return Codex32String.interpolate_at(shares, target="s")
    except CodexError as exc:
        raise Codex32InputError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Error Correction (ECW) Functions
# ---------------------------------------------------------------------------

def try_correct_codex32_errors(
    codex_str: str,
    max_errors: int = 4,
    stop_on_first: bool = False,
):
    """Attempt to correct errors in a codex32 string.

    This function searches for valid corrections by trying character
    substitutions and validating each candidate. Per BIP-93, corrections
    should be user-confirmed before use.

    Args:
        codex_str: The potentially corrupted codex32 string
        max_errors: Maximum number of errors to attempt (1-4, default 4)
        stop_on_first: If True, return after finding first valid correction

    Returns:
        CorrectionResult with success status and list of candidates

    Example:
        >>> result = try_correct_codex32_errors("MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVX")
        >>> if result.success:
        ...     for candidate in result.candidates:
        ...         print(f"Found: {candidate.corrected_string}")
    """
    from error_correction import try_correct_errors
    return try_correct_errors(codex_str, max_errors, stop_on_first)


def try_correct_with_erasures(
    codex_str: str,
    erasure_positions: list[int],
):
    """Correct errors when some positions are known to be wrong (erasures).

    When the user marks positions as "unknown" or "unreadable", we only
    need to search those specific positions, making correction much faster.
    Erasures can correct up to 8 positions (vs 4 for unknown errors).

    Args:
        codex_str: The codex32 string with erasures
        erasure_positions: List of positions (0-indexed) that are known errors

    Returns:
        CorrectionResult with valid correction candidates
    """
    from error_correction import try_correct_with_erasures as _try_erasures
    return _try_erasures(codex_str, erasure_positions)
