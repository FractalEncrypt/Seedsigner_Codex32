"""Core Codex32 validation and BIP32 export helpers."""

from __future__ import annotations

from base64 import b64decode, b64encode
from binascii import hexlify, unhexlify
from pathlib import Path

from codex32_min import Codex32String, CodexError
from embit import bip32, psbt
from embit.networks import NETWORKS


class Codex32InputError(ValueError):
    """Raised when a codex32 input fails validation."""


NETWORK_MAINNET = "mainnet"
NETWORK_TESTNET4 = "testnet4"

SCRIPT_NESTED = "nested"
SCRIPT_NATIVE = "native"
SCRIPT_TAPROOT = "taproot"

MULTISIG_SCRIPT_NESTED = "nested"
MULTISIG_SCRIPT_NATIVE = "native"

SCRIPT_DISPLAY_NAMES = {
    SCRIPT_NESTED: "Nested Segwit (BIP49)",
    SCRIPT_NATIVE: "Native Segwit (BIP84)",
    SCRIPT_TAPROOT: "Taproot (BIP86)",
}

_SINGLE_SIG_PURPOSE = {
    SCRIPT_NESTED: "49'",
    SCRIPT_NATIVE: "84'",
    SCRIPT_TAPROOT: "86'",
}

_SINGLE_SIG_WRAPPERS = {
    SCRIPT_NESTED: "sh(wpkh({key}))",
    SCRIPT_NATIVE: "wpkh({key})",
    SCRIPT_TAPROOT: "tr({key})",
}

_MULTISIG_PURPOSE = {
    MULTISIG_SCRIPT_NESTED: "1'",
    MULTISIG_SCRIPT_NATIVE: "2'",
}

_MULTISIG_WRAPPERS = {
    MULTISIG_SCRIPT_NESTED: "sh(wsh(sortedmulti({threshold},{keys})))",
    MULTISIG_SCRIPT_NATIVE: "wsh(sortedmulti({threshold},{keys}))",
}


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


def normalize_network(network: str) -> str:
    """Validate and normalize supported CLI network names."""
    cleaned = (network or "").strip().lower()
    if cleaned not in {NETWORK_MAINNET, NETWORK_TESTNET4}:
        raise Codex32InputError(
            f"Unsupported network '{network}'. Use '{NETWORK_MAINNET}' or '{NETWORK_TESTNET4}'."
        )
    return cleaned


def normalize_multisig_script_type(script_type: str) -> str:
    """Validate and normalize multisig script type names."""
    cleaned = (script_type or "").strip().lower()
    if cleaned not in _MULTISIG_PURPOSE:
        supported = ", ".join(sorted(_MULTISIG_PURPOSE))
        raise Codex32InputError(
            f"Unsupported multisig script type '{script_type}'. Use one of: {supported}."
        )
    return cleaned


def normalize_single_sig_script_type(script_type: str) -> str:
    """Validate and normalize single-sig script type names."""
    cleaned = (script_type or "").strip().lower()
    if cleaned not in _SINGLE_SIG_PURPOSE:
        supported = ", ".join(sorted(_SINGLE_SIG_PURPOSE))
        raise Codex32InputError(
            f"Unsupported script type '{script_type}'. Use one of: {supported}."
        )
    return cleaned


def get_embit_network_name(network: str) -> str:
    """Map CLI network names to embit network identifiers."""
    normalized = normalize_network(network)
    if normalized == NETWORK_MAINNET:
        return "main"
    return "test"


def get_single_sig_account_derivation(script_type: str, network: str) -> str:
    """Return BIP49/84/86 account derivation path for the selected network."""
    normalized_script = normalize_single_sig_script_type(script_type)
    normalized_network = normalize_network(network)
    coin_type = "0'" if normalized_network == NETWORK_MAINNET else "1'"
    purpose = _SINGLE_SIG_PURPOSE[normalized_script]
    return f"m/{purpose}/{coin_type}/0'"


def get_multisig_account_derivation(script_type: str, network: str) -> str:
    """Return BIP48 account derivation path for nested/native multisig."""
    normalized_script = normalize_multisig_script_type(script_type)
    normalized_network = normalize_network(network)
    coin_type = "0'" if normalized_network == NETWORK_MAINNET else "1'"
    script_path = _MULTISIG_PURPOSE[normalized_script]
    return f"m/48'/{coin_type}/0'/{script_path}"


def _validate_multisig_policy(threshold: int, total_cosigners: int) -> tuple[int, int]:
    if threshold < 2:
        raise Codex32InputError("Multisig threshold must be at least 2.")
    if total_cosigners < 2:
        raise Codex32InputError("Multisig total cosigners must be at least 2.")
    if threshold > total_cosigners:
        raise Codex32InputError("Multisig threshold cannot exceed total cosigners.")
    return threshold, total_cosigners


def _build_multisig_placeholders(total_cosigners: int, branch_name: str) -> list[str]:
    placeholders = []
    for index in range(2, total_cosigners + 1):
        placeholders.append(f"<cosigner_{index}_{branch_name}_key>")
    return placeholders


def get_seed_fingerprint(seed_bytes: bytes, network: str) -> str:
    """Return the master fingerprint for the supplied seed bytes."""
    if len(seed_bytes) != 16:
        raise Codex32InputError(
            f"Expected 16-byte Codex32 master seed, got {len(seed_bytes)} bytes"
        )
    embit_network = get_embit_network_name(network)
    root = bip32.HDKey.from_seed(seed_bytes, version=NETWORKS[embit_network]["xprv"])
    return hexlify(root.child(0).fingerprint).decode("utf-8")


def derive_account_xpub(seed_bytes: bytes, derivation_path: str, network: str) -> str:
    """Derive an account-level xpub/tpub string for a derivation path."""
    embit_network = get_embit_network_name(network)
    root = bip32.HDKey.from_seed(seed_bytes, version=NETWORKS[embit_network]["xprv"])
    xpub = root.derive(derivation_path).to_public()
    return xpub.to_string(version=NETWORKS[embit_network]["xpub"])


def build_single_sig_export(seed_bytes: bytes, script_type: str, network: str) -> dict[str, str]:
    """Build standard single-sig descriptor export artifacts for the loaded seed."""
    normalized_script = normalize_single_sig_script_type(script_type)
    derivation_path = get_single_sig_account_derivation(normalized_script, network)
    fingerprint = get_seed_fingerprint(seed_bytes, network)
    xpub = derive_account_xpub(seed_bytes, derivation_path, network)

    origin_path = derivation_path[2:] if derivation_path.startswith("m/") else derivation_path
    receive_key = f"[{fingerprint}/{origin_path}]{xpub}/0/*"
    change_key = f"[{fingerprint}/{origin_path}]{xpub}/1/*"
    wrapper = _SINGLE_SIG_WRAPPERS[normalized_script]

    return {
        "script_type": normalized_script,
        "script_display": SCRIPT_DISPLAY_NAMES[normalized_script],
        "network": normalize_network(network),
        "fingerprint": fingerprint,
        "derivation_path": derivation_path,
        "xpub": xpub,
        "receive_descriptor": wrapper.format(key=receive_key),
        "change_descriptor": wrapper.format(key=change_key),
    }


def build_multisig_cosigner_export(
    seed_bytes: bytes,
    script_type: str,
    network: str,
    threshold: int | None = None,
    total_cosigners: int | None = None,
) -> dict[str, str]:
    """Build nested/native multisig cosigner export artifacts for the loaded seed."""
    normalized_script = normalize_multisig_script_type(script_type)
    derivation_path = get_multisig_account_derivation(normalized_script, network)
    fingerprint = get_seed_fingerprint(seed_bytes, network)
    xpub = derive_account_xpub(seed_bytes, derivation_path, network)

    origin_path = derivation_path[2:] if derivation_path.startswith("m/") else derivation_path
    key_origin = f"[{fingerprint}/{origin_path}]{xpub}"
    receive_key = f"{key_origin}/0/*"
    change_key = f"{key_origin}/1/*"

    result = {
        "script_type": normalized_script,
        "script_display": SCRIPT_DISPLAY_NAMES[normalized_script],
        "network": normalize_network(network),
        "fingerprint": fingerprint,
        "derivation_path": derivation_path,
        "xpub": xpub,
        "key_origin": key_origin,
        "receive_key": receive_key,
        "change_key": change_key,
    }

    if threshold is not None or total_cosigners is not None:
        if threshold is None or total_cosigners is None:
            raise Codex32InputError("Provide both threshold and total cosigners, or neither.")
        threshold, total_cosigners = _validate_multisig_policy(threshold, total_cosigners)
        wrapper = _MULTISIG_WRAPPERS[normalized_script]

        receive_keys = [receive_key] + _build_multisig_placeholders(total_cosigners, "receive")
        change_keys = [change_key] + _build_multisig_placeholders(total_cosigners, "change")

        result["policy"] = f"{threshold}/{total_cosigners}"
        result["receive_descriptor_template"] = wrapper.format(
            threshold=threshold,
            keys=", ".join(receive_keys),
        )
        result["change_descriptor_template"] = wrapper.format(
            threshold=threshold,
            keys=", ".join(change_keys),
        )

    return result


def _count_psbt_signatures(tx: psbt.PSBT) -> int:
    count = 0
    for inp in tx.inputs:
        if inp.final_scriptwitness is not None:
            count += 1
        else:
            count += len(inp.partial_sigs)
    return count


def _get_inputs_missing_utxo(parsed_psbt: psbt.PSBT) -> list[int]:
    missing_inputs: list[int] = []
    for index, inp in enumerate(parsed_psbt.inputs, start=1):
        if inp.utxo is None:
            missing_inputs.append(index)
    return missing_inputs


def _parse_psbt_text_input(raw_input: str) -> psbt.PSBT:
    compact = "".join((raw_input or "").split())
    if not compact:
        raise Codex32InputError("PSBT input is empty.")

    # Prefer base64 first (most common export format)
    try:
        decoded = b64decode(compact, validate=True)
        return psbt.PSBT.parse(decoded)
    except Exception:
        pass

    # Fallback to hex-encoded PSBT bytes
    try:
        decoded = unhexlify(compact)
        return psbt.PSBT.parse(decoded)
    except Exception as exc:
        raise Codex32InputError(
            "Unable to parse PSBT input. Provide base64 PSBT, hex PSBT, or a file path."
        ) from exc


def parse_psbt_input(psbt_input: str) -> psbt.PSBT:
    """Parse PSBT from direct base64/hex text or from a file path."""
    raw_value = (psbt_input or "").strip()
    if not raw_value:
        raise Codex32InputError("PSBT input is empty.")

    candidate_path = Path(raw_value)
    if candidate_path.exists() and candidate_path.is_file():
        data = candidate_path.read_bytes()
        if data.startswith(b"psbt\xff"):
            return psbt.PSBT.parse(data)

        text_data = data.decode("utf-8", errors="ignore")
        return _parse_psbt_text_input(text_data)

    return _parse_psbt_text_input(raw_value)


def sign_psbt_with_seed(seed_bytes: bytes, network: str, psbt_input: str) -> dict[str, str | int]:
    """Sign a PSBT with the loaded Codex32 seed and return signed export strings."""
    if len(seed_bytes) != 16:
        raise Codex32InputError(
            f"Expected 16-byte Codex32 master seed, got {len(seed_bytes)} bytes"
        )

    parsed_psbt = parse_psbt_input(psbt_input)
    missing_utxo_inputs = _get_inputs_missing_utxo(parsed_psbt)
    if missing_utxo_inputs:
        missing_list = ", ".join(str(i) for i in missing_utxo_inputs)
        raise Codex32InputError(
            "PSBT input is missing UTXO data (witness_utxo/non_witness_utxo) "
            f"for input(s): {missing_list}. Re-export PSBT with full input data before signing."
        )

    embit_network = get_embit_network_name(network)
    root = bip32.HDKey.from_seed(seed_bytes, version=NETWORKS[embit_network]["xprv"])

    before_count = _count_psbt_signatures(parsed_psbt)
    try:
        parsed_psbt.sign_with(root)
    except AttributeError as exc:
        raise Codex32InputError(
            "Unable to sign PSBT because required UTXO details are missing. "
            "Re-export PSBT with complete input data (witness_utxo/non_witness_utxo)."
        ) from exc

    after_count = _count_psbt_signatures(parsed_psbt)

    if after_count == before_count:
        raise Codex32InputError(
            "Signing with this seed did not add a signature. Verify the PSBT belongs to this key."
        )

    serialized = parsed_psbt.serialize()
    return {
        "network": normalize_network(network),
        "signatures_added": after_count - before_count,
        "total_signatures": after_count,
        "signed_psbt_base64": b64encode(serialized).decode("ascii"),
        "signed_psbt_hex": serialized.hex(),
    }


def save_signed_psbt_binary(output_path: str, signed_psbt_base64: str) -> str:
    """Save signed PSBT as raw binary bytes to a file and return resolved path."""
    raw_path = (output_path or "").strip()
    if not raw_path:
        raise Codex32InputError("Output path is empty.")

    destination = Path(raw_path).expanduser()
    if destination.exists() and destination.is_dir():
        raise Codex32InputError("Output path points to a directory. Provide a file path.")

    try:
        payload = b64decode((signed_psbt_base64 or "").strip(), validate=True)
    except Exception as exc:
        raise Codex32InputError("Signed PSBT payload is not valid base64.") from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return str(destination.resolve())


def recover_secret_share(shares: list[Codex32String]) -> Codex32String:
    """Recover the secret share (index 's') from a set of codex32 shares."""
    if not shares:
        raise Codex32InputError("No shares provided for recovery")
    try:
        return Codex32String.interpolate_at(shares, target="s")
    except CodexError as exc:
        raise Codex32InputError(str(exc)) from exc
