import argparse
from codex32_min import CHARSET_MAP, CHARSET, Codex32String, CodexError, ms32_create_checksum

BECH32_CHARSET = set(CHARSET)
SUBSTITUTIONS = {
    "b": "8",
    "o": "0",
    "i": "f",
    "1": "g",
}
SHARE_INDEX_ORDER = ["A", "C", "D", "E", "F"]
PAYLOAD_LENGTH = 26
IDENT_LENGTH = 4


def _normalize_input(value: str) -> str:
    return "".join(value.split()).replace("-", "")


def build_share(header: str, payload: str, uppercase: bool | None = None) -> str:
    header = _normalize_input(header)
    payload = _normalize_input(payload)
    original_header = header

    if header.lower().startswith("ms1"):
        header = header[3:]

    if len(header) != 6:
        raise SystemExit("Header must be MS1 + k + ident(4) + share_idx (6 chars after MS1).")

    data_part = (header + payload).lower()
    values = [CHARSET_MAP[c] for c in data_part]
    checksum = "".join(CHARSET[v] for v in ms32_create_checksum(values))
    share = "ms1" + data_part + checksum
    if uppercase is None:
        uppercase = original_header.isupper()
    return share.upper() if uppercase else share


def _prompt_k() -> int:
    while True:
        raw = input("Please enter the total number of shares for the (k) value (2-5): ").strip()
        if raw.isdigit():
            k = int(raw)
            if 2 <= k <= len(SHARE_INDEX_ORDER):
                return k
        print("k must be a number between 2 and 5.")


def _prompt_identifier() -> str:
    charset_display = "".join(CHARSET)
    while True:
        ident = _normalize_input(input("Please enter a 4-character identifier: "))
        if len(ident) != IDENT_LENGTH:
            print("Identifier must be exactly 4 characters.")
            continue
        invalid = sorted({ch for ch in ident.lower() if ch not in BECH32_CHARSET})
        if invalid:
            print(
                "Identifier must use bech32 characters ({}). Invalid: {}".format(
                    charset_display, ", ".join(invalid)
                )
            )
            continue
        return ident.upper()


def _apply_substitutions(raw: str) -> tuple[str, list[tuple[str, str]]]:
    cleaned = _normalize_input(raw).lower()
    substitutions: list[tuple[str, str]] = []
    output: list[str] = []
    for ch in cleaned:
        if ch in BECH32_CHARSET:
            output.append(ch)
            continue
        replacement = SUBSTITUTIONS.get(ch, "0")
        output.append(replacement)
        substitutions.append((ch, replacement))
    return "".join(output), substitutions


def _prompt_payload(label: str) -> str:
    payload = ""
    substitutions: list[tuple[str, str]] = []
    while len(payload) < PAYLOAD_LENGTH:
        remaining = PAYLOAD_LENGTH - len(payload)
        prompt = f"Enter {label} ({remaining} chars remaining): " if payload else f"Enter {label} ({PAYLOAD_LENGTH} chars): "
        chunk = input(prompt)
        normalized, chunk_subs = _apply_substitutions(chunk)
        payload += normalized
        substitutions.extend(chunk_subs)
        if len(payload) > PAYLOAD_LENGTH:
            payload = payload[:PAYLOAD_LENGTH]
            print(f"Payload truncated to {PAYLOAD_LENGTH} characters.")
    if substitutions:
        pretty = ", ".join(f"{src}->{dst.upper()}" for src, dst in substitutions)
        print(f"Substituted invalid characters: {pretty}")
    return payload.upper()


def _swap_halves(value: str) -> str:
    mid = len(value) // 2
    return value[mid:] + value[:mid]


def _rotate_left(value: str, count: int) -> str:
    count = count % len(value)
    return value[count:] + value[:count]


def _rotate_right(value: str, count: int) -> str:
    count = count % len(value)
    return value[-count:] + value[:-count]


def _generate_payloads(payload: str, count: int) -> list[str]:
    transforms = [
        lambda v: v,
        lambda v: v[::-1],
        _swap_halves,
        lambda v: _rotate_left(v, 3),
        lambda v: _rotate_right(v, 3),
    ]
    payloads: list[str] = []
    used: set[str] = set()
    for idx in range(count):
        candidate = transforms[idx](payload) if idx < len(transforms) else _rotate_left(payload, idx + 1)
        if candidate in used:
            candidate = _rotate_left(payload, idx + 1)
            if candidate in used:
                candidate = _rotate_right(payload, idx + 2)
        used.add(candidate)
        payloads.append(candidate)
    return payloads


def _recover_s_share(shares: list[str]) -> str | None:
    try:
        codex_shares = [Codex32String(share) for share in shares]
        secret = Codex32String.interpolate_at(codex_shares, target="s")
        return secret.s
    except CodexError as exc:
        print(f"Warning: unable to reconstruct S share: {exc}")
        return None


def _interactive_mode() -> None:
    k_value = _prompt_k()
    identifier = _prompt_identifier()
    base_payload = _prompt_payload("payload")

    separate = input("Enter separate payloads for each share? [y/N]: ").strip().lower() == "y"
    share_indices = SHARE_INDEX_ORDER[:k_value]
    if separate:
        payloads = [base_payload]
        payloads.extend(
            _prompt_payload(f"payload for share {share_idx}")
            for share_idx in share_indices[1:]
        )
    else:
        payloads = _generate_payloads(base_payload, k_value)

    print("\nGenerated shares:")
    shares: list[str] = []
    for share_idx, payload in zip(share_indices, payloads):
        header = f"MS1{k_value}{identifier}{share_idx}"
        share = build_share(header, payload, uppercase=True)
        shares.append(share)
        print(f"Share {share_idx}: {share}")

    s_share = _recover_s_share(shares)
    if s_share:
        print(f"S Share (Master Codex32 key): {s_share}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Codex32 test shares with valid checksums.")
    parser.add_argument("--header", help="MS1 + k + ident(4) + share_idx")
    parser.add_argument("--payload", help="26-character payload (bech32 charset)")
    args = parser.parse_args()

    if args.header and args.payload:
        if len(_normalize_input(args.payload)) != PAYLOAD_LENGTH:
            print(f"Warning: payload length should be {PAYLOAD_LENGTH} characters.")
        print(build_share(args.header, args.payload))
        return

    _interactive_mode()


if __name__ == "__main__":
    main()