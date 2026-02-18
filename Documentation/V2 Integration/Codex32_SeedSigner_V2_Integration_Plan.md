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

## 3) Current SeedSigner behavior to revisit
In SeedSigner PSBT finalize flow:
- `psbt.sign_with(psbt_parser.root)` signs correctly.
- Then `PSBTParser.trim(psbt)` is used before display/export.

This trim behavior currently drops most per-input metadata and keeps only signatures/final witness. That can break downstream sequential multisig signing in some toolchains because later signers may require `witness_utxo` / `non_witness_utxo`.

Relevant code:
- `SeedSigner/src/seedsigner/views/psbt_views.py` (`PSBTFinalizeView.run`)
- `SeedSigner/src/seedsigner/models/psbt_parser.py` (`trim`)

## 4) Recommended V2 changes (SeedSigner)

### Priority A - Signing robustness
1. **Preserve full PSBT metadata after signing**
   - Replace unconditional trim-on-sign with full PSBT retention for export (or at least for multisig paths).
   - Keep an optional compact mode only if explicitly needed for QR size constraints.

2. **Add explicit missing-UTXO precheck before signing**
   - For each input, verify `inp.utxo` (or equivalent witness/non-witness UTXO availability).
   - If missing, show actionable error:
     - "PSBT missing witness_utxo/non_witness_utxo for input(s) X. Re-export with full input data."

3. **Keep no-op signing detection**
   - If signature count does not increase after signing, keep existing error flow and improve message context (wrong signer / already signed / mismatch key origin).

### Priority B - Codex32 + PSBT flow alignment
4. **Ensure Codex32Seed is first-class in PSBT signer selection**
   - Confirm Codex32 seeds appear cleanly in `PSBTSelectSeedView` and fingerprint matching logic.
   - Confirm no passphrase assumptions leak into PSBT signing path.

5. **Descriptor-based multisig verification compatibility**
   - Confirm change-verification logic works identically for Codex32 seeds when multisig descriptor is loaded.

### Priority C - UX copy and guardrails
6. **Improve user-facing guidance for incomplete PSBTs**
   - Suggest coordinator export settings (include full input data / UTXOs).
   - Keep messages short and operational.

7. **Optional: handoff mode label**
   - If retaining full PSBT increases QR length, label this as "multisig handoff-safe" behavior.

## 5) Suggested file touchpoints
- `SeedSigner/src/seedsigner/views/psbt_views.py`
  - Update `PSBTFinalizeView.run` signing/export behavior.
- `SeedSigner/src/seedsigner/models/psbt_parser.py`
  - Add helper for missing-UTXO detection.
  - Potentially keep `trim()` but stop using it by default for multisig handoff.
- `SeedSigner/src/seedsigner/gui` warning/error screens (if needed)
  - Add a dedicated message for missing UTXO details.
- Tests:
  - PSBT signing tests for preserved metadata and sequential signer handoff.
  - Error-path tests for missing UTXO fields.

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

## 7) Decision log (recommended defaults)
- Default signed PSBT export should be **handoff-safe** (metadata preserved).
- QR support stack remains unchanged (reuse existing SeedSigner decoders/encoders).
- Missing UTXO should be treated as a user-actionable data-quality error, not an internal exception.

## 8) Implementation status snapshot
- Terminal reference implementation: validated for 2-of-3 sequential signing and network broadcast.
- SeedSigner integration: Codex32 seed entry exists; PSBT QR stack exists; signing export semantics need V2 adjustment for robust multisig handoff.
