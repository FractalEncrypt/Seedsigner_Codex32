---
description: Codex32 SeedSigner V2 integration plan with PSBT QR considerations
---

# Codex32 -> SeedSigner V2 Integration Plan (Post-Multisig Validation)

## 1) Why this V2 doc exists
This V2 plan captures what changed after successful end-to-end multisig signing tests with the Codex32 terminal flow (including sequential cosigner signing and broadcast), and what should be ported into SeedSigner next.

Primary outcomes from terminal validation:
- Multi-key in-session signer switching works.
- Sequential multisig signing works when signed PSBT retains required metadata.
- Missing UTXO data now fails with a clear message (instead of runtime crash).

## 2) Direct answer: do we need to account for QR-based PSBTs?
Short answer: **yes, but mostly by reusing existing SeedSigner PSBT QR infrastructure**.

You do **not** need to invent a new QR protocol for Codex32.
SeedSigner already supports PSBT QR import/export formats:
- UR2 (`crypto-psbt`)
- BBQr
- Specter animated base64
- single-frame base64/base43

Relevant current implementation:
- PSBT decode routing: `DecodeQR.add_data()` and `get_psbt()` in
  `SeedSigner/src/seedsigner/models/decode_qr.py`
- PSBT scan flow: `ScanView` -> `self.controller.psbt = decoder.get_psbt()` in
  `SeedSigner/src/seedsigner/views/scan_views.py`
- Signed PSBT QR export: `UrPsbtQrEncoder` in
  `SeedSigner/src/seedsigner/models/encode_qr.py`

So for Codex32, QR transport is already there. The main work is signing-flow correctness and Codex32 seed UX integration.

## 3) SeedSigner V2 behavior now implemented
In SeedSigner PSBT finalize flow:
- `psbt.sign_with(psbt_parser.root)` signs on the original PSBT object.
- Signed export now keeps full PSBT metadata by default (no trim-before-export path).

Parser-side guardrails:
- `PSBTParser.get_inputs_missing_utxo()` detects inputs missing both `witness_utxo` and `non_witness_utxo`.
- `MissingInputUtxoError` is raised early during parsing.
- UI route displays a clear warning and exits to main menu without crash.

Relevant code:
- `SeedSigner/src/seedsigner/views/psbt_views.py` (`PSBTOverviewView`, `PSBTFinalizeView`, `PSBTMissingInputUtxoWarningView`)
- `SeedSigner/src/seedsigner/models/psbt_parser.py` (`MissingInputUtxoError`, `get_inputs_missing_utxo`)

## 4) Implemented V2 changes (SeedSigner)

### Priority A - Signing robustness (completed)
1. **Preserve full PSBT metadata after signing**
   - Trim is no longer used by default during finalize/export path.
   - Signed PSBT remains handoff-safe for sequential cosigners.

2. **Add explicit missing-UTXO precheck before signing/parse flow**
   - Missing UTXO inputs are detected during parser initialization.
   - Missing data now triggers actionable warning instead of runtime crash.

3. **Keep no-op signing detection**
   - Signature count delta check remains active and routes to existing signing-failed UX.

### Priority B - Codex32 + PSBT flow alignment (completed)
4. **Ensure Codex32Seed is first-class in PSBT signer selection**
   - Confirm Codex32 seeds appear cleanly in `PSBTSelectSeedView` and fingerprint matching logic.
   - Confirm no passphrase assumptions leak into PSBT signing path.

5. **Descriptor-based multisig verification compatibility**
   - Confirm change-verification logic works identically for Codex32 seeds when multisig descriptor is loaded.

### Priority C - UX copy and guardrails (completed)
6. **Improve user-facing guidance for incomplete PSBTs**
   - Suggest coordinator export settings (include full input data / UTXOs).
   - Keep messages short and operational.

7. **Optional: handoff mode label**
   - If retaining full PSBT increases QR length, label this as "multisig handoff-safe" behavior.

## 5) Implemented file touchpoints
- `SeedSigner/src/seedsigner/views/psbt_views.py`
  - `PSBTFinalizeView.run` preserves full signed PSBT metadata.
  - `PSBTOverviewView` handles missing-UTXO parser exception.
  - Added `PSBTMissingInputUtxoWarningView`.
- `SeedSigner/src/seedsigner/models/psbt_parser.py`
  - Added `MissingInputUtxoError` and `get_inputs_missing_utxo()` helper.
  - Kept `trim()` for optional/future compact mode use, but not default finalize path.
- Tests:
  - `tests/test_psbt_parser.py` includes missing-UTXO detection/exception coverage.
  - `tests/test_flows_psbt.py` includes missing-UTXO warning route coverage.

## 6) Test plan for V2 integration

### A. Regression tests (host)
- Sign single-sig PSBT with Codex32 seed (baseline).
- Sign multisig PSBT with signer A, then signer B on resulting PSBT (must add signature).
- Confirm signed PSBT still contains input UTXO metadata after signer A.
- Confirm missing-UTXO PSBT yields clear, non-crashing error.

### B. Device workflow tests
1. Scan unsigned PSBT QR (UR or BBQr).
2. Sign with Codex32 seed #1.
3. Export signed PSBT QR.
4. Import into coordinator or second signer.
5. Sign with Codex32 seed #2.
6. Finalize and broadcast.

### C. Compatibility checks
- Sparrow export/import
- Nunchuk / Specter / coordinator variants where possible
- Large QR payload behavior at low/medium/high QR density

## 7) Coordinator export guidance for missing-UTXO cases

When SeedSigner reports missing UTXO input data, re-export the PSBT from the coordinator with complete input context.

Coordinator-agnostic checklist:
1. Export **PSBT** (not finalized transaction hex).
2. Enable any option equivalent to:
   - include full input data,
   - include previous transaction,
   - include witness UTXO / non-witness UTXO.
3. Re-import the newly exported PSBT and re-run signing.

Notes:
- For multisig handoff, preserving UTXO metadata is required so subsequent signers can validate/sign.
- If your coordinator has both "compact" and "full" PSBT export modes, use **full**.

## 8) Decision log (recommended defaults)
- Default signed PSBT export should be **handoff-safe** (metadata preserved).
- QR support stack remains unchanged (reuse existing SeedSigner decoders/encoders).
- Missing UTXO should be treated as a user-actionable data-quality error, not an internal exception.

## 9) Implementation status snapshot
- Terminal reference implementation: validated for 2-of-3 sequential signing and network broadcast.
- SeedSigner integration: Phase 1 and Phase 2 changes are implemented and validated in host tests.
- Local Windows test helper documented for pyzbar MSVCR120 dependency patch (`tools/windows_patch_pyzbar_msvcr120.ps1`).

Validation snapshot (host):
- `tests/test_psbt_parser.py`
- `tests/test_flows_psbt.py`
- `tests/test_seed.py` (Codex32 metadata-related cases)
- `tests/test_flows_seed.py -k "codex32_backup"`
