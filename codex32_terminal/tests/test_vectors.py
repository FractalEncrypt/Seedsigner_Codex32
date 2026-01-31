"""Manual test harness for BIP-93 codex32 vectors (2/3)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from model import codex32_to_seed_bytes, seed_bytes_to_mnemonic  # noqa: E402


VECTORS = {
    "vector2": {
        "codex32": "MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW",
        "seed_hex": "d1808e096b35b209ca12132b264662a5",
    },
    "vector3": {
        "codex32": "ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln",
        "seed_hex": "ffeeddccbbaa99887766554433221100",
    },
}


def main() -> None:
    for name, vector in VECTORS.items():
        seed_bytes = codex32_to_seed_bytes(vector["codex32"])
        expected = bytes.fromhex(vector["seed_hex"])
        if seed_bytes != expected:
            raise AssertionError(
                f"{name}: seed mismatch. got={seed_bytes.hex()} expected={vector['seed_hex']}"
            )
        mnemonic = seed_bytes_to_mnemonic(seed_bytes)
        print(f"{name}: seed OK -> {mnemonic}")


if __name__ == "__main__":
    main()
