"""Dedicated Phase D/E tests for PSBT parsing/signing helpers."""

from __future__ import annotations

from base64 import b64decode, b64encode
import sys
import tempfile
import unittest
from pathlib import Path

from embit import bip32, psbt, script, transaction
from embit.networks import NETWORKS
from embit.psbt import DerivationPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from model import (  # noqa: E402
    Codex32InputError,
    parse_psbt_input,
    save_signed_psbt_binary,
    sign_psbt_with_seed,
)


SEED_A = bytes.fromhex("d1808e096b35b209ca12132b264662a5")
SEED_B = bytes.fromhex("ffeeddccbbaa99887766554433221100")


class TestPsbtSigningHelpers(unittest.TestCase):
    def _build_unsigned_single_sig_psbt(self, seed_bytes: bytes) -> psbt.PSBT:
        """Create a minimal unsigned p2wpkh PSBT owned by the provided seed."""
        root = bip32.HDKey.from_seed(seed_bytes, version=NETWORKS["main"]["xprv"])
        child = root.derive("m/84h/0h/0h/0/0")
        pubkey = child.key.get_public_key()
        script_pubkey = script.p2wpkh(pubkey)

        txin = transaction.TransactionInput(bytes.fromhex("11" * 32), 0)
        txout = transaction.TransactionOutput(90_000, script_pubkey)
        tx = transaction.Transaction(vin=[txin], vout=[txout])

        unsigned_psbt = psbt.PSBT(tx)
        unsigned_psbt.inputs[0].witness_utxo = transaction.TransactionOutput(100_000, script_pubkey)
        unsigned_psbt.inputs[0].bip32_derivations[pubkey] = DerivationPath(
            root.child(0).fingerprint,
            bip32.parse_path("m/84h/0h/0h/0/0"),
        )
        return unsigned_psbt

    def test_parse_psbt_input_base64_hex_and_file(self) -> None:
        unsigned = self._build_unsigned_single_sig_psbt(SEED_A)
        raw = unsigned.serialize()
        psbt_base64 = b64encode(raw).decode("ascii")
        psbt_hex = raw.hex()

        parsed_from_b64 = parse_psbt_input(psbt_base64)
        self.assertEqual(parsed_from_b64.serialize(), raw)

        parsed_from_hex = parse_psbt_input(psbt_hex)
        self.assertEqual(parsed_from_hex.serialize(), raw)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            b64_file = temp_path / "unsigned_b64.txt"
            b64_file.write_text(psbt_base64, encoding="utf-8")
            parsed_from_b64_file = parse_psbt_input(str(b64_file))
            self.assertEqual(parsed_from_b64_file.serialize(), raw)

            hex_file = temp_path / "unsigned_hex.txt"
            hex_file.write_text(psbt_hex, encoding="utf-8")
            parsed_from_hex_file = parse_psbt_input(str(hex_file))
            self.assertEqual(parsed_from_hex_file.serialize(), raw)

            raw_file = temp_path / "unsigned.psbt"
            raw_file.write_bytes(raw)
            parsed_from_raw_file = parse_psbt_input(str(raw_file))
            self.assertEqual(parsed_from_raw_file.serialize(), raw)

    def test_parse_psbt_input_invalid_raises(self) -> None:
        with self.assertRaises(Codex32InputError):
            parse_psbt_input("this-is-not-a-psbt")

    def test_sign_psbt_with_matching_seed_adds_signature(self) -> None:
        unsigned = self._build_unsigned_single_sig_psbt(SEED_A)
        unsigned_base64 = b64encode(unsigned.serialize()).decode("ascii")

        result = sign_psbt_with_seed(
            seed_bytes=SEED_A,
            network="mainnet",
            psbt_input=unsigned_base64,
        )

        self.assertGreaterEqual(int(result["signatures_added"]), 1)
        self.assertTrue(str(result["signed_psbt_base64"]))
        self.assertTrue(str(result["signed_psbt_hex"]))

        signed = psbt.PSBT.parse(b64decode(str(result["signed_psbt_base64"]), validate=True))
        self.assertIsNotNone(signed.inputs[0].utxo)

    def test_sign_psbt_missing_utxo_data_raises(self) -> None:
        txin = transaction.TransactionInput(bytes.fromhex("11" * 32), 0)
        txout = transaction.TransactionOutput(90_000, script.Script(b"\x51"))
        unsigned = psbt.PSBT(transaction.Transaction(vin=[txin], vout=[txout]))
        unsigned_base64 = b64encode(unsigned.serialize()).decode("ascii")

        with self.assertRaises(Codex32InputError):
            sign_psbt_with_seed(
                seed_bytes=SEED_A,
                network="mainnet",
                psbt_input=unsigned_base64,
            )

    def test_sign_psbt_with_wrong_seed_fails(self) -> None:
        unsigned = self._build_unsigned_single_sig_psbt(SEED_A)
        unsigned_base64 = b64encode(unsigned.serialize()).decode("ascii")

        with self.assertRaises(Codex32InputError):
            sign_psbt_with_seed(
                seed_bytes=SEED_B,
                network="mainnet",
                psbt_input=unsigned_base64,
            )

    def test_save_signed_psbt_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "signed_output.psbt"
            saved = save_signed_psbt_binary(str(output_path), "cHNidP8AAA==")
            saved_path = Path(saved)
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_bytes(), b"psbt\xff\x00\x00")

            with self.assertRaises(Codex32InputError):
                save_signed_psbt_binary(temp_dir, "cHNidP8AAA==")

            with self.assertRaises(Codex32InputError):
                save_signed_psbt_binary(str(output_path), "not-base64")


if __name__ == "__main__":
    unittest.main()
