"""Minimal terminal CLI for codex32 -> BIP39 conversion."""

from __future__ import annotations

import sys

import controller
from model import Codex32InputError, codex32_to_mnemonic, codex32_to_seed_bytes


def read_input() -> str:
    """Read codex32 input from CLI args or prompt."""
    if len(sys.argv) > 1:
        return "".join(sys.argv[1:])
    return ""


def main() -> int:
    """CLI runner."""
    if "--full" in sys.argv:
        return controller.run(entry_mode="full")
    codex_str = read_input()
    if not codex_str:
        return controller.run(entry_mode="box")
    try:
        seed_bytes = codex32_to_seed_bytes(codex_str)
        mnemonic = codex32_to_mnemonic(codex_str)
    except Codex32InputError as exc:
        print(f"Error: {exc}")
        return 1

    print("\nCodex32 S-share accepted.")
    print(f"Seed (hex): {seed_bytes.hex()}")
    print(f"BIP39 mnemonic: {mnemonic}")
    print("Note: This mnemonic is a display encoding of the BIP32 seed; no PBKDF2 is used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
