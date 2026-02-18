"""Manual test harness for BIP-93 codex32 vectors (2/3)."""

from __future__ import annotations

from base64 import b64encode
import sys
from pathlib import Path

from embit import bip32, psbt, script, transaction
from embit.networks import NETWORKS
from embit.psbt import DerivationPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from model import (  # noqa: E402
    build_multisig_cosigner_export,
    codex32_to_seed_bytes,
    get_seed_fingerprint,
    sign_psbt_with_seed,
)


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
        fp_mainnet = get_seed_fingerprint(seed_bytes, "mainnet")
        fp_testnet4 = get_seed_fingerprint(seed_bytes, "testnet4")
        ms_nested = build_multisig_cosigner_export(
            seed_bytes=seed_bytes,
            script_type="nested",
            network="mainnet",
            threshold=2,
            total_cosigners=3,
        )
        if ms_nested["derivation_path"] != "m/48'/0'/0'/1'":
            raise AssertionError(
                f"{name}: unexpected nested multisig derivation {ms_nested['derivation_path']}"
            )
        if not ms_nested["key_origin"].startswith(f"[{fp_mainnet}/48'/0'/0'/1']"):
            raise AssertionError(f"{name}: key origin missing expected nested BIP48 origin")

        ms_native_testnet = build_multisig_cosigner_export(
            seed_bytes=seed_bytes,
            script_type="native",
            network="testnet4",
            threshold=2,
            total_cosigners=3,
        )
        if ms_native_testnet["derivation_path"] != "m/48'/1'/0'/2'":
            raise AssertionError(
                f"{name}: unexpected native multisig testnet derivation {ms_native_testnet['derivation_path']}"
            )
        if "receive_descriptor_template" not in ms_native_testnet:
            raise AssertionError(f"{name}: expected receive descriptor template for multisig export")

        # Phase D smoke test: build a simple p2wpkh PSBT for this seed and sign it
        root = bip32.HDKey.from_seed(seed_bytes, version=NETWORKS["main"]["xprv"])
        child = root.derive("m/84h/0h/0h/0/0")
        pubkey = child.key.get_public_key()
        script_pubkey = script.p2wpkh(pubkey)

        txin = transaction.TransactionInput(bytes.fromhex("11" * 32), 0)
        txout = transaction.TransactionOutput(90000, script_pubkey)
        tx = transaction.Transaction(vin=[txin], vout=[txout])

        unsigned_psbt = psbt.PSBT(tx)
        unsigned_psbt.inputs[0].witness_utxo = transaction.TransactionOutput(100000, script_pubkey)
        unsigned_psbt.inputs[0].bip32_derivations[pubkey] = DerivationPath(
            root.child(0).fingerprint,
            bip32.parse_path("m/84h/0h/0h/0/0"),
        )
        unsigned_b64 = b64encode(unsigned_psbt.serialize()).decode("ascii")

        sign_result = sign_psbt_with_seed(
            seed_bytes=seed_bytes,
            network="mainnet",
            psbt_input=unsigned_b64,
        )
        if int(sign_result["signatures_added"]) < 1:
            raise AssertionError(f"{name}: expected at least one new PSBT signature")
        if not str(sign_result["signed_psbt_base64"]):
            raise AssertionError(f"{name}: signed PSBT output missing")

        print(
            f"{name}: seed OK -> fp mainnet={fp_mainnet} testnet4={fp_testnet4}; multisig+psbt OK"
        )


if __name__ == "__main__":
    main()
