"""Terminal UI helpers for codex32-native terminal flow."""

from __future__ import annotations


def display_welcome(entry_mode: str, network: str) -> None:
    print("Codex32 BIP32 terminal (v1)")
    print(f"Network: {network}")
    if entry_mode == "full":
        print("Paste full shares. Ctrl+C or /cancel cancels.")
    else:
        print("Enter characters box-by-box. Prefix 'MS1' is pre-filled.")
        print("Use Backspace (empty input) or '<' to go back. Ctrl+C or /cancel cancels.")


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
    return input(f"Box {box_number:02d} (/cancel to abort): ")


def get_full_share_input() -> str:
    return input("Paste full codex32 share (/cancel to abort): ")


def display_error(message: str) -> None:
    print(f"Error: {message}")


def display_info(message: str) -> None:
    print(message)


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


def display_session_loaded(
    seed_bytes: bytes,
    fingerprint: str,
    network: str,
    recovered_share: str | None = None,
) -> None:
    print("\nCodex32 seed loaded.")
    print(f"Seed (hex): {seed_bytes.hex()}")
    print(f"Fingerprint: {fingerprint}")
    print(f"Network: {network}")
    if recovered_share:
        print(f"Recovered S-share: {recovered_share}")


def prompt_main_menu_choice(active_fingerprint: str, loaded_count: int) -> str:
    print("\nActions:")
    print(f"Active key fingerprint: {active_fingerprint}")
    print(f"Loaded keys: {loaded_count}")
    print("  1) Export single-sig descriptor")
    print("  2) Export multisig cosigner")
    print("  3) Sign PSBT")
    print("  4) Show loaded seed details")
    print("  5) Load new key")
    print("  6) Show loaded keys")
    print("  7) Exit")
    return input("Select action [1-7]: ").strip().lower()


def display_loaded_keys(fingerprints: list[str], active_index: int) -> None:
    print("\nLoaded keys:")
    for index, fingerprint in enumerate(fingerprints, start=1):
        active_marker = " (active)" if (index - 1) == active_index else ""
        print(f"  {index}) {fingerprint}{active_marker}")


def prompt_switch_loaded_key_choice() -> str:
    print("Enter list number or fingerprint to make active. [Enter/b] Back")
    return input("Activate key: ").strip().lower()


def prompt_single_sig_script_type() -> str:
    print("\nSingle-sig script type:")
    print("  1) Nested Segwit (BIP49)")
    print("  2) Native Segwit (BIP84)")
    print("  3) Taproot (BIP86)")
    print("  [Enter/b] Back")
    return input("Select script type: ").strip().lower()


def display_single_sig_export(export_data: dict[str, str]) -> None:
    print("\nSingle-sig export")
    print(f"Script: {export_data['script_display']}")
    print(f"Network: {export_data['network']}")
    print(f"Fingerprint: {export_data['fingerprint']}")
    print(f"Derivation: {export_data['derivation_path']}")
    print(f"Xpub: {export_data['xpub']}")
    print("Receive descriptor:")
    print(export_data["receive_descriptor"])
    print("Change descriptor:")
    print(export_data["change_descriptor"])


def prompt_multisig_script_type() -> str:
    print("\nMultisig script type:")
    print("  1) Nested Segwit (BIP48 /1')")
    print("  2) Native Segwit (BIP48 /2')")
    print("  [Enter/b] Back")
    return input("Select script type: ").strip().lower()


def prompt_multisig_policy() -> str:
    print("\nOptional multisig policy template (press Enter to skip):")
    print("  Example: 2/3")
    return input("Policy m/n: ").strip()


def display_multisig_cosigner_export(export_data: dict[str, str]) -> None:
    print("\nMultisig cosigner export")
    print(f"Script: {export_data['script_display']}")
    print(f"Network: {export_data['network']}")
    print(f"Fingerprint: {export_data['fingerprint']}")
    print(f"Derivation: {export_data['derivation_path']}")
    print(f"Xpub: {export_data['xpub']}")
    print(f"Key origin: {export_data['key_origin']}")
    print("Cosigner receive key:")
    print(export_data["receive_key"])
    print("Cosigner change key:")
    print(export_data["change_key"])
    if "policy" in export_data:
        print(f"Policy: {export_data['policy']}")
        print("Receive descriptor template:")
        print(export_data["receive_descriptor_template"])
        print("Change descriptor template:")
        print(export_data["change_descriptor_template"])


def prompt_psbt_input() -> str:
    print("\nPSBT input")
    print("- Paste base64 PSBT")
    print("- OR paste hex PSBT")
    print("- OR paste a local file path containing PSBT bytes/base64/hex")
    print("- Press Enter to cancel")
    return input("PSBT input: ").strip()


def display_psbt_sign_result(sign_result: dict[str, str | int]) -> None:
    print("\nPSBT signed.")
    print(f"Network: {sign_result['network']}")
    print(f"Signatures added: {sign_result['signatures_added']}")
    print(f"Total signatures: {sign_result['total_signatures']}")
    print("Signed PSBT (base64):")
    print(sign_result["signed_psbt_base64"])


def prompt_signed_psbt_output_directory() -> str:
    print("Save location (directory path). Press Enter for current directory.")
    return input("Output directory: ").strip()


def prompt_signed_psbt_output_filename() -> str:
    print("Enter output file name without extension (example: signed_test1)")
    print("The tool automatically saves with .psbt extension.")
    return input("Output file name: ").strip()


def display_saved_psbt_path(saved_path: str) -> None:
    print(f"Saved signed PSBT binary to: {saved_path}")


def wait_for_continue() -> None:
    input("Press Enter to return to menu...")


def display_goodbye() -> None:
    print("Session ended.")
