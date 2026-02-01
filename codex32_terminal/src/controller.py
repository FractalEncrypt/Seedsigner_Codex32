"""Controller logic for codex32 entry flow."""

from __future__ import annotations

from codex32.bech32 import CHARSET

import view
from model import (
    Codex32InputError,
    codex32_to_mnemonic,
    codex32_to_seed_bytes,
    parse_codex32_share,
    recover_secret_share,
    try_correct_codex32_errors,
)


# Supported seed sizes - must match VALID_LENGTHS in model.py
# 128-bit (48 chars) or 256-bit (74 chars)
LEN_128BIT = 48
LEN_256BIT = 74
BASE_PREFIX = "MS1"
FIRST_BOX = len(BASE_PREFIX) + 1
CANCELLED = object()


def _normalize_box_char(value: str) -> str:
    if not value:
        return ""
    return value.strip().upper()


def _is_valid_bech32_char(value: str) -> bool:
    return len(value) == 1 and value.lower() in CHARSET


def _is_backspace(value: str) -> bool:
    return value == "" or value == "<"


def _attempt_error_correction(codex_str: str, max_errors: int = 2) -> str | None:
    """Attempt to correct errors in a codex32 string.

    Offers correction candidates to user for confirmation per BIP-93.

    Args:
        codex_str: The string that failed validation
        max_errors: Maximum errors to search for (default 2 for speed)

    Returns:
        Corrected string if user accepts, None otherwise
    """
    view.display_checksum_failed()

    if not view.confirm("Would you like to search for corrections?"):
        return None

    view.display_correction_searching(max_errors)
    result = try_correct_codex32_errors(codex_str, max_errors=max_errors)

    if not result.success or not result.candidates:
        view.display_error(f"No corrections found with up to {max_errors} errors.")
        return None

    view.display_correction_candidates(result.candidates)

    if len(result.candidates) == 1:
        # Single candidate - just confirm
        if view.confirm_correction(result.candidates[0]):
            return result.candidates[0].corrected_string
        return None

    # Multiple candidates - let user choose
    choice = view.get_correction_choice(len(result.candidates))
    if choice is None:
        return None

    selected = result.candidates[choice - 1]
    if view.confirm_correction(selected):
        return selected.corrected_string

    return None


def collect_codex32_boxes(prefix: str, start_box: int, total_len: int) -> str:
    current = prefix
    view.display_progress(current, total_len)
    box_number = start_box
    while box_number <= total_len:
        raw = view.get_box_input(box_number)
        ch = _normalize_box_char(raw)
        if _is_backspace(ch):
            if len(current) > len(prefix):
                current = current[:-1]
                box_number -= 1
                view.display_progress(current, total_len)
            else:
                view.display_error("Already at the first editable box.")
            continue
        if len(ch) != 1:
            view.display_error("Enter exactly one character.")
            continue
        if not _is_valid_bech32_char(ch):
            view.display_error("Invalid bech32 character. Use bech32 charset.")
            continue
        current += ch
        view.display_progress(current, total_len)
        box_number += 1
    return current


def _display_and_confirm(codex_str: str) -> bool:
    view.display_preview(codex_str)
    return view.confirm("Submit this codex32 string?")


def _collect_share_box(prefix: str, start_box: int, index: int, total: int, total_len: int) -> str | object | None:
    view.display_share_prompt(index, total)
    try:
        codex_str = collect_codex32_boxes(prefix, start_box, total_len)
    except KeyboardInterrupt:
        view.display_cancelled()
        return CANCELLED
    if not _display_and_confirm(codex_str):
        view.wait_for_retry()
        return None
    return codex_str


def _collect_share_full(prefix: str | None, index: int, total: int) -> str | object | None:
    view.display_share_prompt(index, total)
    view.display_full_share_hint(prefix)
    try:
        codex_str = view.get_full_share_input().strip()
    except KeyboardInterrupt:
        view.display_cancelled()
        return CANCELLED
    if not codex_str:
        view.display_error("Share input cannot be empty.")
        view.wait_for_retry()
        return None
    if not _display_and_confirm(codex_str):
        view.wait_for_retry()
        return None
    return codex_str


def run(entry_mode: str = "box") -> int:
    view.display_welcome(entry_mode)

    # For box mode, ask user about seed size
    total_len = LEN_128BIT  # default
    if entry_mode == "box":
        seed_size = view.get_seed_size_choice()
        if seed_size == "256":
            total_len = LEN_256BIT

    while True:
        if entry_mode == "full":
            result = _collect_share_full(BASE_PREFIX, 1, 1)
        else:
            result = _collect_share_box(BASE_PREFIX, FIRST_BOX, 1, 1, total_len)
        if result is CANCELLED:
            return 1
        if result is None:
            continue
        codex_str = result
        try:
            first_share = parse_codex32_share(codex_str)
        except Codex32InputError as exc:
            view.display_error(str(exc))
            # Offer error correction for checksum failures
            corrected = _attempt_error_correction(codex_str)
            if corrected:
                try:
                    first_share = parse_codex32_share(corrected)
                    codex_str = corrected
                except Codex32InputError:
                    view.display_error("Correction still invalid. Please re-enter.")
                    view.wait_for_retry()
                    continue
            else:
                view.wait_for_retry()
                continue
        if first_share.share_idx.lower() == "s":
            try:
                seed_bytes = codex32_to_seed_bytes(first_share.s)
                mnemonic = codex32_to_mnemonic(first_share.s)
            except Codex32InputError as exc:
                view.display_error(str(exc))
                view.wait_for_retry()
                continue
            view.display_success(seed_bytes, mnemonic)
            return 0

        try:
            threshold = int(first_share.k)
        except ValueError:
            view.display_error("Invalid threshold value in share header.")
            view.wait_for_retry()
            continue
        if threshold < 2:
            view.display_error("Threshold must be >= 2 for split shares.")
            view.wait_for_retry()
            continue

        shares = [first_share]
        prefix = f"{BASE_PREFIX}{first_share.k}{first_share.ident}"
        if first_share.s.isupper():
            prefix = prefix.upper()

        # For subsequent shares, use the same total_len as detected from first share
        share_total_len = len(first_share.s)

        while len(shares) < threshold:
            share_index = len(shares) + 1
            if entry_mode == "full":
                result = _collect_share_full(prefix, share_index, threshold)
            else:
                result = _collect_share_box(prefix, len(prefix) + 1, share_index, threshold, share_total_len)
            if result is CANCELLED:
                return 1
            if result is None:
                continue
            codex_str = result
            try:
                candidate = parse_codex32_share(codex_str)
            except Codex32InputError as exc:
                view.display_error(str(exc))
                # Offer error correction for checksum failures
                corrected = _attempt_error_correction(codex_str)
                if corrected:
                    try:
                        candidate = parse_codex32_share(corrected)
                        codex_str = corrected
                    except Codex32InputError:
                        view.display_error("Correction still invalid. Please re-enter.")
                        view.wait_for_retry()
                        continue
                else:
                    view.wait_for_retry()
                    continue
            if candidate.k != first_share.k or candidate.ident != first_share.ident:
                view.display_error("Share header mismatch (k/identifier).")
                view.wait_for_retry()
                continue
            if candidate.share_idx.lower() in {s.share_idx.lower() for s in shares}:
                view.display_error("Duplicate share index entered.")
                view.wait_for_retry()
                continue
            shares.append(candidate)

        try:
            secret = recover_secret_share(shares)
            seed_bytes = codex32_to_seed_bytes(secret.s)
            mnemonic = codex32_to_mnemonic(secret.s)
        except Codex32InputError as exc:
            view.display_error(str(exc))
            view.wait_for_retry()
            continue
        view.display_success(seed_bytes, mnemonic, recovered_share=secret.s)
        return 0
