"""Controller logic for codex32 entry flow."""

from __future__ import annotations

from codex32_min import CHARSET

import view
from model import (
    Codex32InputError,
    codex32_to_mnemonic,
    codex32_to_seed_bytes,
    parse_codex32_share,
    recover_secret_share,
)


TOTAL_LEN = 48
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


def collect_codex32_boxes(prefix: str, start_box: int) -> str:
    current = prefix
    view.display_progress(current, TOTAL_LEN)
    box_number = start_box
    while box_number <= TOTAL_LEN:
        raw = view.get_box_input(box_number)
        ch = _normalize_box_char(raw)
        if _is_backspace(ch):
            if len(current) > len(prefix):
                current = current[:-1]
                box_number -= 1
                view.display_progress(current, TOTAL_LEN)
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
        view.display_progress(current, TOTAL_LEN)
        box_number += 1
    return current


def _display_and_confirm(codex_str: str) -> bool:
    view.display_preview(codex_str)
    return view.confirm("Submit this codex32 string?")


def _collect_share_box(prefix: str, start_box: int, index: int, total: int) -> str | object | None:
    view.display_share_prompt(index, total)
    try:
        codex_str = collect_codex32_boxes(prefix, start_box)
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
    while True:
        if entry_mode == "full":
            result = _collect_share_full(BASE_PREFIX, 1, 1)
        else:
            result = _collect_share_box(BASE_PREFIX, FIRST_BOX, 1, 1)
        if result is CANCELLED:
            return 1
        if result is None:
            continue
        codex_str = result
        try:
            first_share = parse_codex32_share(codex_str)
        except Codex32InputError as exc:
            view.display_error(str(exc))
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

        while len(shares) < threshold:
            share_index = len(shares) + 1
            if entry_mode == "full":
                result = _collect_share_full(prefix, share_index, threshold)
            else:
                result = _collect_share_box(prefix, len(prefix) + 1, share_index, threshold)
            if result is CANCELLED:
                return 1
            if result is None:
                continue
            codex_str = result
            try:
                candidate = parse_codex32_share(codex_str)
            except Codex32InputError as exc:
                view.display_error(str(exc))
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
