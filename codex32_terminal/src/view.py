"""Terminal UI helpers for codex32 entry."""

from __future__ import annotations


def display_welcome(entry_mode: str) -> None:
    print("Codex32 S-share entry (MVP)")
    if entry_mode == "full":
        print("Paste full shares. Ctrl+C cancels.")
    else:
        print("Enter characters box-by-box. Prefix 'MS1' is pre-filled.")
        print("Use Backspace (empty input) or '<' to go back. Ctrl+C cancels.")


def display_progress(current: str, total_len: int) -> None:
    remaining = max(0, total_len - len(current))
    progress = f"{current}{'_' * remaining}"
    print(f"Progress: {progress}")


def display_share_prompt(index: int, total: int) -> None:
    print(f"\nEnter share {index} of {total}:")


def display_full_share_hint(prefix: str | None) -> None:
    if prefix:
        print(f"Prefix hint: {prefix}...")


def get_box_input(box_number: int) -> str:
    return input(f"Box {box_number:02d}: ")


def get_full_share_input() -> str:
    return input("Paste full codex32 share: ")


def display_error(message: str) -> None:
    print(f"Error: {message}")


def display_preview(codex_str: str) -> None:
    print("\nPreview:")
    print(codex_str)


def confirm(prompt: str) -> bool:
    response = input(f"{prompt} [y/N]: ").strip().lower()
    return response in {"y", "yes"}


def display_correction(original: str, corrected: str) -> None:
    print("\nCorrection candidate found:")
    print(f"Original:  {original}")
    print(f"Corrected: {corrected}")


def wait_for_retry() -> None:
    input("Press Enter to try again...")


def display_cancelled() -> None:
    print("Entry cancelled.")


def display_success(seed_bytes: bytes, mnemonic: str, recovered_share: str | None = None) -> None:
    print("\nCodex32 S-share accepted.")
    print(f"Seed (hex): {seed_bytes.hex()}")
    if recovered_share:
        print(f"Recovered S-share: {recovered_share}")
    print(f"BIP39 mnemonic: {mnemonic}")
    print("Note: This mnemonic is a display encoding of the BIP32 seed; no PBKDF2 is used.")
