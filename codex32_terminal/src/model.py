"""Core Codex32 S-share validation and conversion helpers."""

from __future__ import annotations

from codex32_min import Codex32String, CodexError
from embit import bip39


class Codex32InputError(ValueError):
    """Raised when a codex32 input fails validation."""


def sanitize_codex32_input(raw: str) -> str:
    """Normalize user input by removing whitespace and separators."""
    if raw is None:
        return ""
    compact = "".join(raw.split())
    return compact.replace("-", "")


def parse_codex32_share(codex_str: str, expected_len: int = 48) -> Codex32String:
    """Parse and validate a codex32 share string (checksum + header)."""
    cleaned = sanitize_codex32_input(codex_str)
    if not cleaned:
        raise Codex32InputError("Codex32 input is empty")
    if expected_len is not None and len(cleaned) != expected_len:
        raise Codex32InputError(
            f"Expected {expected_len} characters for a 128-bit codex32 share, got {len(cleaned)}"
        )
    try:
        codex = Codex32String(cleaned)
    except CodexError as exc:
        raise Codex32InputError(str(exc)) from exc
    if codex.hrp != "ms":
        raise Codex32InputError(f"Unsupported HRP '{codex.hrp}', expected 'ms'")
    return codex


def validate_codex32_s_share(codex_str: str, expected_len: int = 48) -> Codex32String:
    """Validate a codex32 S-share string and return a Codex32String object."""
    codex = parse_codex32_share(codex_str, expected_len)
    if codex.share_idx.lower() != "s":
        raise Codex32InputError(
            f"Share index must be 's' for an unshared secret, got '{codex.share_idx}'"
        )
    if len(codex.data) != 16:
        raise Codex32InputError(
            f"Expected 16-byte (128-bit) master seed, got {len(codex.data)} bytes"
        )
    return codex


def codex32_to_seed_bytes(codex_str: str) -> bytes:
    """Convert a codex32 S-share string into 16 bytes of seed entropy."""
    codex = validate_codex32_s_share(codex_str)
    return codex.data


def seed_bytes_to_mnemonic(seed_bytes: bytes) -> str:
    """Convert 16 bytes of entropy to a 12-word BIP39 mnemonic."""
    if len(seed_bytes) != 16:
        raise Codex32InputError(
            f"Expected 16 bytes of entropy for a 12-word mnemonic, got {len(seed_bytes)}"
        )
    return bip39.mnemonic_from_bytes(seed_bytes)


def codex32_to_mnemonic(codex_str: str) -> str:
    """Convert a codex32 S-share into a 12-word BIP39 mnemonic."""
    return seed_bytes_to_mnemonic(codex32_to_seed_bytes(codex_str))


def recover_secret_share(shares: list[Codex32String]) -> Codex32String:
    """Recover the secret share (index 's') from a set of codex32 shares."""
    if not shares:
        raise Codex32InputError("No shares provided for recovery")
    try:
        return Codex32String.interpolate_at(shares, target="s")
    except CodexError as exc:
        raise Codex32InputError(str(exc)) from exc
