"""Minimal Codex32 implementation (BIP-93) with no external dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
CHARSET_MAP = {c: i for i, c in enumerate(CHARSET)}

MS32_CONST = 0x10CE0795C2FD1E62A
MS32_LONG_CONST = 0x43381E570BF4798AB26

BECH32_INV = [
    0, 1, 20, 24, 10, 8, 12, 29, 5, 11, 4, 9, 6, 28, 26, 31,
    22, 18, 17, 23, 2, 25, 16, 19, 3, 21, 14, 30, 13, 7, 27, 15,
]


class CodexError(ValueError):
    """Raised when a codex32 string fails validation."""


def _is_single_case(value: str) -> bool:
    return value == value.lower() or value == value.upper()


def _validate_ascii(value: str) -> None:
    if any(ord(x) < 33 or ord(x) > 126 for x in value):
        raise CodexError("Codex32 input contains invalid characters")


def ms32_polymod(values: Iterable[int]) -> int:
    gen = [
        0x19DC500CE73FDE210,
        0x1BFAE00DEF77FE529,
        0x1FBD920FFFE7BEE52,
        0x1739640BDEEE3FDAD,
        0x07729A039CFC75F5A,
    ]
    residue = 0x23181B3
    for v in values:
        b = residue >> 60
        residue = (residue & 0x0FFFFFFFFFFFFFFF) << 5 ^ v
        for i in range(5):
            residue ^= gen[i] if ((b >> i) & 1) else 0
    return residue


def ms32_long_polymod(values: Iterable[int]) -> int:
    gen = [
        0x3D59D273535EA62D897,
        0x7A9BECB6361C6C51507,
        0x543F9B7E6C38D8A2A0E,
        0x0C577EAECCF1990D13C,
        0x1887F74F8DC71B10651,
    ]
    residue = 0x23181B3
    for v in values:
        b = residue >> 70
        residue = (residue & 0x3FFFFFFFFFFFFFFFFF) << 5 ^ v
        for i in range(5):
            residue ^= gen[i] if ((b >> i) & 1) else 0
    return residue


def ms32_verify_long_checksum(data: List[int]) -> bool:
    return ms32_long_polymod(data) == MS32_LONG_CONST


def ms32_create_long_checksum(data: List[int]) -> List[int]:
    polymod = ms32_long_polymod(data + [0] * 15) ^ MS32_LONG_CONST
    return [(polymod >> 5 * (14 - i)) & 31 for i in range(15)]


def ms32_verify_checksum(data: List[int]) -> bool:
    if len(data) >= 96:
        return ms32_verify_long_checksum(data)
    if len(data) <= 93:
        return ms32_polymod(data) == MS32_CONST
    return False


def ms32_create_checksum(data: List[int]) -> List[int]:
    if len(data) > 80:
        return ms32_create_long_checksum(data)
    polymod = ms32_polymod(data + [0] * 13) ^ MS32_CONST
    return [(polymod >> 5 * (12 - i)) & 31 for i in range(13)]


def ms32_encode(data: List[int]) -> str:
    combined = data + ms32_create_checksum(data)
    return "ms1" + "".join(CHARSET[d] for d in combined)


def _checksum_length(data_values: List[int]) -> int:
    return 15 if len(data_values) >= 96 else 13


def _decode_data_values(codex_str: str) -> tuple[List[int], str]:
    _validate_ascii(codex_str)
    if not _is_single_case(codex_str):
        raise CodexError("Codex32 input must be single-case")

    case = "upper" if codex_str == codex_str.upper() else "lower"
    codex = codex_str.lower()
    pos = codex.rfind("1")
    if pos < 2 or not (48 <= len(codex) <= 127):
        raise CodexError("Codex32 input has invalid length")
    if codex[:pos] != "ms":
        raise CodexError("Codex32 input must start with ms1")

    data_part = codex[pos + 1 :]
    if not data_part:
        raise CodexError("Codex32 input missing data payload")
    if not all(x in CHARSET for x in data_part):
        raise CodexError("Codex32 input has non-bech32 characters")

    threshold_char = data_part[0]
    if threshold_char not in "023456789":
        raise CodexError("Codex32 threshold must be 0 or 2-9")
    if threshold_char == "0" and len(data_part) > 5 and data_part[5] != "s":
        raise CodexError("Codex32 share index must be 's' when threshold is 0")

    data_values = [CHARSET_MAP[c] for c in data_part]
    if not ms32_verify_checksum(data_values):
        raise CodexError("Codex32 checksum failed")

    return data_values, case


def _payload_to_bytes(payload_values: List[int]) -> bytes:
    acc = 0
    bits = 0
    out = bytearray()
    for value in payload_values:
        acc = (acc << 5) | value
        bits += 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xFF)
            acc &= (1 << bits) - 1 if bits else 0
    return bytes(out)


def bech32_mul(a: int, b: int) -> int:
    res = 0
    for i in range(5):
        res ^= a if ((b >> i) & 1) else 0
        a *= 2
        a ^= 41 if (32 <= a) else 0
    return res


def bech32_lagrange(indices: List[int], x: int) -> List[int]:
    n = 1
    coeffs: List[int] = []
    for i in indices:
        n = bech32_mul(n, i ^ x)
        m = 1
        for j in indices:
            m = bech32_mul(m, (x if i == j else i) ^ j)
        coeffs.append(m)
    return [bech32_mul(n, BECH32_INV[i]) for i in coeffs]


def ms32_interpolate(shares: List[List[int]], x: int) -> List[int]:
    weights = bech32_lagrange([s[5] for s in shares], x)
    res: List[int] = []
    for i in range(len(shares[0])):
        n = 0
        for j in range(len(shares)):
            n ^= bech32_mul(weights[j], shares[j][i])
        res.append(n)
    return res


@dataclass
class Codex32String:
    value: str

    def __post_init__(self) -> None:
        data_values, case = _decode_data_values(self.value)
        checksum_len = _checksum_length(data_values)
        data_part_values = data_values[:-checksum_len]
        data_part_chars = [CHARSET[v] for v in data_part_values]

        self._case = case
        self._data_part_values = data_part_values
        self.hrp = "ms"
        self.k = data_part_chars[0]
        self.ident = "".join(data_part_chars[1:5])
        self.share_idx = data_part_chars[5]
        self._payload_values = data_part_values[6:]
        self.data = _payload_to_bytes(self._payload_values)

    @property
    def s(self) -> str:
        return self.value

    @property
    def data_part_values(self) -> List[int]:
        return list(self._data_part_values)

    @property
    def case(self) -> str:
        return self._case

    @staticmethod
    def interpolate_at(shares: List["Codex32String"], target: str = "s") -> "Codex32String":
        if not shares:
            raise CodexError("No shares provided for interpolation")
        target_val = CHARSET_MAP.get(target.lower())
        if target_val is None:
            raise CodexError(f"Invalid target share index '{target}'")

        base_len = len(shares[0]._data_part_values)
        for share in shares:
            if len(share._data_part_values) != base_len:
                raise CodexError("Shares must be the same length for interpolation")

        interpolated = ms32_interpolate([s._data_part_values for s in shares], target_val)
        encoded = ms32_encode(interpolated)
        if shares[0].case == "upper":
            encoded = encoded.upper()
        return Codex32String(encoded)
