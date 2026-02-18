"""Controller logic for codex32 entry flow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codex32_min import CHARSET

import view
from model import (
    Codex32InputError,
    MULTISIG_SCRIPT_NATIVE,
    MULTISIG_SCRIPT_NESTED,
    SCRIPT_NATIVE,
    SCRIPT_NESTED,
    SCRIPT_TAPROOT,
    build_multisig_cosigner_export,
    build_single_sig_export,
    codex32_to_seed_bytes,
    get_seed_fingerprint,
    normalize_network,
    parse_codex32_share,
    recover_secret_share,
    save_signed_psbt_binary,
    sign_psbt_with_seed,
)


TOTAL_LEN = 48
BASE_PREFIX = "MS1"
FIRST_BOX = len(BASE_PREFIX) + 1
CANCELLED = object()
ENTRY_CANCEL_COMMANDS = {"/cancel", "/exit"}


@dataclass
class LoadedKey:
    seed_bytes: bytes
    fingerprint: str
    recovered_share: str | None = None


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
        if (raw or "").strip().lower() in ENTRY_CANCEL_COMMANDS:
            raise KeyboardInterrupt
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


def _parse_script_type_choice(raw_choice: str) -> str | None:
    choice = (raw_choice or "").strip().lower()
    mapping = {
        "1": SCRIPT_NESTED,
        "nested": SCRIPT_NESTED,
        "2": SCRIPT_NATIVE,
        "native": SCRIPT_NATIVE,
        "3": SCRIPT_TAPROOT,
        "taproot": SCRIPT_TAPROOT,
    }
    if choice in {"", "b", "back"}:
        return None
    return mapping.get(choice)


def _parse_multisig_script_type_choice(raw_choice: str) -> str | None:
    choice = (raw_choice or "").strip().lower()
    mapping = {
        "1": MULTISIG_SCRIPT_NESTED,
        "nested": MULTISIG_SCRIPT_NESTED,
        "2": MULTISIG_SCRIPT_NATIVE,
        "native": MULTISIG_SCRIPT_NATIVE,
    }
    if choice in {"", "b", "back"}:
        return None
    return mapping.get(choice)


def _parse_multisig_policy(raw_policy: str) -> tuple[int, int] | None:
    policy = (raw_policy or "").strip()
    if not policy:
        return None
    if "/" not in policy:
        raise Codex32InputError("Use m/n format for multisig policy (example: 2/3).")
    threshold_raw, total_raw = policy.split("/", maxsplit=1)
    if not threshold_raw.strip().isdigit() or not total_raw.strip().isdigit():
        raise Codex32InputError("Multisig policy values must be integers (example: 2/3).")
    return int(threshold_raw.strip()), int(total_raw.strip())


def _compose_signed_psbt_output_path(output_directory: str, output_filename: str) -> str:
    raw_filename = (output_filename or "").strip()
    if not raw_filename:
        raise Codex32InputError("Output file name is empty.")

    if "/" in raw_filename or "\\" in raw_filename:
        raise Codex32InputError("Output file name must not include a path. Use the directory prompt for folders.")

    filename_base = raw_filename[:-5] if raw_filename.lower().endswith(".psbt") else raw_filename
    if not filename_base:
        raise Codex32InputError("Output file name is empty.")
    final_filename = f"{filename_base}.psbt"

    filename_path = Path(final_filename)

    raw_directory = (output_directory or "").strip()
    base_dir = Path(raw_directory).expanduser() if raw_directory else Path(".")
    return str(base_dir / filename_path)


def _build_loaded_key(seed_bytes: bytes, network: str, recovered_share: str | None = None) -> LoadedKey:
    return LoadedKey(
        seed_bytes=seed_bytes,
        fingerprint=get_seed_fingerprint(seed_bytes, network),
        recovered_share=recovered_share,
    )


def _find_loaded_key_index(loaded_keys: list[LoadedKey], seed_bytes: bytes) -> int | None:
    for index, loaded in enumerate(loaded_keys):
        if loaded.seed_bytes == seed_bytes:
            return index
    return None


def _parse_switch_key_choice(raw_choice: str, loaded_keys: list[LoadedKey]) -> int | None:
    choice = (raw_choice or "").strip().lower()
    if choice in {"", "b", "back"}:
        return None

    if choice.isdigit():
        selected = int(choice)
        if 1 <= selected <= len(loaded_keys):
            return selected - 1
        raise Codex32InputError(f"Selection out of range. Choose 1-{len(loaded_keys)}.")

    for index, loaded in enumerate(loaded_keys):
        if loaded.fingerprint.lower() == choice:
            return index

    raise Codex32InputError("Invalid key selection. Enter a list number or fingerprint.")


def _load_seed_from_entry(entry_mode: str, initial_share: str | None = None) -> tuple[bytes, str | None] | object:
    pending_share = initial_share

    while True:
        if pending_share is not None:
            codex_str = pending_share
            pending_share = None
        else:
            if entry_mode == "full":
                result = _collect_share_full(BASE_PREFIX, 1, 1)
            else:
                result = _collect_share_box(BASE_PREFIX, FIRST_BOX, 1, 1)
            if result is CANCELLED:
                return CANCELLED
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
            except Codex32InputError as exc:
                view.display_error(str(exc))
                view.wait_for_retry()
                continue
            return seed_bytes, None

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
                return CANCELLED
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
        except Codex32InputError as exc:
            view.display_error(str(exc))
            view.wait_for_retry()
            continue
        return seed_bytes, secret.s


def _session_loop(loaded_keys: list[LoadedKey], active_key_index: int, network: str, entry_mode: str) -> int:
    active_key = loaded_keys[active_key_index]
    view.display_session_loaded(
        seed_bytes=active_key.seed_bytes,
        fingerprint=active_key.fingerprint,
        network=network,
        recovered_share=active_key.recovered_share,
    )

    while True:
        active_key = loaded_keys[active_key_index]
        try:
            action = view.prompt_main_menu_choice(
                active_fingerprint=active_key.fingerprint,
                loaded_count=len(loaded_keys),
            )
        except KeyboardInterrupt:
            view.display_cancelled()
            return 1

        if action == "1":
            script_choice = view.prompt_single_sig_script_type()
            script_type = _parse_script_type_choice(script_choice)
            if script_type is None:
                continue
            try:
                export_data = build_single_sig_export(
                    seed_bytes=active_key.seed_bytes,
                    script_type=script_type,
                    network=network,
                )
            except Codex32InputError as exc:
                view.display_error(str(exc))
                continue

            view.display_single_sig_export(export_data)
            view.wait_for_continue()

        elif action == "2":
            script_choice = view.prompt_multisig_script_type()
            script_type = _parse_multisig_script_type_choice(script_choice)
            if script_type is None:
                continue

            try:
                policy = _parse_multisig_policy(view.prompt_multisig_policy())
                if policy is None:
                    export_data = build_multisig_cosigner_export(
                        seed_bytes=active_key.seed_bytes,
                        script_type=script_type,
                        network=network,
                    )
                else:
                    threshold, total_cosigners = policy
                    export_data = build_multisig_cosigner_export(
                        seed_bytes=active_key.seed_bytes,
                        script_type=script_type,
                        network=network,
                        threshold=threshold,
                        total_cosigners=total_cosigners,
                    )
            except Codex32InputError as exc:
                view.display_error(str(exc))
                continue

            view.display_multisig_cosigner_export(export_data)
            view.wait_for_continue()

        elif action == "3":
            try:
                psbt_input = view.prompt_psbt_input()
            except KeyboardInterrupt:
                view.display_cancelled()
                return 1

            if not psbt_input:
                continue

            try:
                sign_result = sign_psbt_with_seed(
                    seed_bytes=active_key.seed_bytes,
                    network=network,
                    psbt_input=psbt_input,
                )
            except Codex32InputError as exc:
                view.display_error(str(exc))
                continue

            view.display_psbt_sign_result(sign_result)

            if view.confirm("Save signed PSBT to a binary .psbt file?"):
                output_directory = view.prompt_signed_psbt_output_directory()
                output_filename = view.prompt_signed_psbt_output_filename()
                try:
                    output_path = _compose_signed_psbt_output_path(
                        output_directory=output_directory,
                        output_filename=output_filename,
                    )
                    saved_path = save_signed_psbt_binary(
                        output_path=output_path,
                        signed_psbt_base64=str(sign_result["signed_psbt_base64"]),
                    )
                except Codex32InputError as exc:
                    view.display_error(str(exc))
                else:
                    view.display_saved_psbt_path(saved_path)

            view.wait_for_continue()

        elif action == "4":
            view.display_session_loaded(
                seed_bytes=active_key.seed_bytes,
                fingerprint=active_key.fingerprint,
                network=network,
                recovered_share=active_key.recovered_share,
            )

        elif action == "5":
            load_result = _load_seed_from_entry(entry_mode=entry_mode)
            if load_result is CANCELLED:
                continue
            seed_bytes, recovered_share = load_result
            existing_index = _find_loaded_key_index(loaded_keys, seed_bytes)
            if existing_index is not None:
                active_key_index = existing_index
                view.display_info(
                    f"Key already loaded. Switched to fingerprint {loaded_keys[active_key_index].fingerprint}."
                )
            else:
                loaded_keys.append(
                    _build_loaded_key(
                        seed_bytes=seed_bytes,
                        network=network,
                        recovered_share=recovered_share,
                    )
                )
                active_key_index = len(loaded_keys) - 1
                view.display_info(f"Loaded key fingerprint: {loaded_keys[active_key_index].fingerprint}")

        elif action == "6":
            if len(loaded_keys) < 2:
                view.display_error("No alternate key loaded yet. Use action 5 to load new key first.")
                continue
            view.display_loaded_keys(
                fingerprints=[loaded.fingerprint for loaded in loaded_keys],
                active_index=active_key_index,
            )
            try:
                selected = _parse_switch_key_choice(
                    raw_choice=view.prompt_switch_loaded_key_choice(),
                    loaded_keys=loaded_keys,
                )
            except Codex32InputError as exc:
                view.display_error(str(exc))
                continue
            if selected is None:
                continue
            active_key_index = selected
            view.display_info(f"Active key fingerprint: {loaded_keys[active_key_index].fingerprint}")

        elif action == "7":
            view.display_goodbye()
            return 0

        else:
            view.display_error("Invalid action. Choose 1, 2, 3, 4, 5, 6, or 7.")


def _collect_share_full(prefix: str | None, index: int, total: int) -> str | object | None:
    view.display_share_prompt(index, total)
    view.display_full_share_hint(prefix)
    try:
        codex_str = view.get_full_share_input().strip()
        if codex_str.lower() in ENTRY_CANCEL_COMMANDS:
            raise KeyboardInterrupt
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


def run(entry_mode: str = "box", network: str = "mainnet", initial_share: str | None = None) -> int:
    try:
        selected_network = normalize_network(network)
    except Codex32InputError as exc:
        view.display_error(str(exc))
        return 1

    view.display_welcome(entry_mode, selected_network)
    load_result = _load_seed_from_entry(entry_mode=entry_mode, initial_share=initial_share)
    if load_result is CANCELLED:
        return 1

    seed_bytes, recovered_share = load_result
    loaded_keys = [
        _build_loaded_key(
            seed_bytes=seed_bytes,
            network=selected_network,
            recovered_share=recovered_share,
        )
    ]
    return _session_loop(
        loaded_keys=loaded_keys,
        active_key_index=0,
        network=selected_network,
        entry_mode=entry_mode,
    )
