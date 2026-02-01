"""Terminal UI helpers for codex32 entry."""

from __future__ import annotations


def display_welcome(entry_mode: str) -> None:
    print("Codex32 S-share entry (MVP)")
    if entry_mode == "full":
        print("Paste full shares (48 or 74 chars). Ctrl+C cancels.")
    else:
        print("Enter characters box-by-box. Prefix 'MS1' is pre-filled.")
        print("Use Backspace (empty input) or '<' to go back. Ctrl+C cancels.")


def get_seed_size_choice() -> str:
    """Ask user to select seed size for box-by-box entry."""
    print("\nSelect seed size:")
    print("  [1] 128-bit (48 characters, 12-word mnemonic)")
    print("  [2] 256-bit (74 characters, 24-word mnemonic)")
    while True:
        choice = input("Enter 1 or 2 [default: 1]: ").strip()
        if choice == "" or choice == "1":
            return "128"
        elif choice == "2":
            return "256"
        else:
            print("Invalid choice. Enter 1 or 2.")


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
    word_count = len(mnemonic.split())
    bit_size = len(seed_bytes) * 8
    print(f"\nCodex32 S-share accepted ({bit_size}-bit seed).")
    print(f"Seed (hex): {seed_bytes.hex()}")
    if recovered_share:
        print(f"Recovered S-share: {recovered_share}")
    print(f"BIP39 mnemonic ({word_count} words): {mnemonic}")
    print("Note: This mnemonic is a display encoding of the BIP32 seed; no PBKDF2 is used.")


# ---------------------------------------------------------------------------
# Error Correction UI Functions
# ---------------------------------------------------------------------------

def display_checksum_failed() -> None:
    """Display message when checksum validation fails."""
    print("\nChecksum validation failed.")


def display_correction_searching(max_errors: int) -> None:
    """Display message while searching for corrections."""
    print(f"Searching for corrections (up to {max_errors} errors)...")


def display_correction_candidates(candidates: list) -> None:
    """Display list of correction candidates for user review.

    Args:
        candidates: List of CorrectionCandidate objects
    """
    if not candidates:
        print("No correction candidates found.")
        return

    print(f"\nFound {len(candidates)} potential correction(s):\n")

    for i, candidate in enumerate(candidates, 1):
        print(f"[{i}] {candidate.corrected_string}")
        if candidate.error_details:
            changes = ", ".join(
                f"pos {pos}: '{orig}'→'{new}'"
                for pos, orig, new in candidate.error_details
            )
            print(f"    Changes: {changes}")
        print()


def get_correction_choice(num_candidates: int) -> int | None:
    """Prompt user to select a correction candidate.

    Args:
        num_candidates: Number of available candidates

    Returns:
        1-indexed choice, or None if cancelled
    """
    while True:
        prompt = f"Select correction [1-{num_candidates}] or 'c' to cancel: "
        choice = input(prompt).strip().lower()

        if choice == 'c':
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= num_candidates:
                return idx
            print(f"Please enter a number between 1 and {num_candidates}")
        except ValueError:
            print("Invalid input. Enter a number or 'c' to cancel.")


def confirm_correction(candidate) -> bool:
    """Ask user to confirm a specific correction.

    Args:
        candidate: CorrectionCandidate to confirm

    Returns:
        True if user confirms, False otherwise
    """
    print("\nProposed correction:")
    print(f"  Original:  {candidate.original_string}")
    print(f"  Corrected: {candidate.corrected_string}")

    if candidate.error_details:
        print(f"  Changes ({candidate.error_count}):")
        for pos, orig, new in candidate.error_details:
            print(f"    Position {pos}: '{orig}' → '{new}'")

    return confirm("Accept this correction?")
