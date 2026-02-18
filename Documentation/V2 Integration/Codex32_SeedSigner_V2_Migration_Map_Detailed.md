---
description: Detailed migration map for porting Codex32 terminal V2 behavior into SeedSigner with minimal Codex32-only changes
---

# Codex32 -> SeedSigner V2 Migration Map (Detailed, Minimal-Change)

## 1) Scope and guardrails

## Goal
Port the validated Codex32 terminal V2 behavior into SeedSigner while preserving all existing non-Codex32 flows.

## Hard guardrails
1. Preserve current SeedSigner UX/logic for non-Codex32 seeds.
2. Keep Codex32 share-entry flow as-is (already functional).
3. Keep Codex32 success screen actions as-is:
   - Show Codex32 Key
   - Load seed
4. Keep existing flows unchanged for:
   - Scan transaction
   - Export xpub
   - Address explorer
   - Discard seed
   - BIP-85 child seed (remain enabled)
5. Only alter Codex32-specific backup behavior and Codex32-relevant PSBT robustness.

---

## 2) Current repo behavior map (what already matches requirements)

### A) Main menu -> Seeds list -> per-seed options
Already matches the requested behavior:
- Main menu routes to Seeds via `MainMenuView`.
- Seeds list shows fingerprints + "Load a seed".
- Selecting a fingerprint routes to seed options.

Relevant files:
- `SeedSigner/src/seedsigner/views/view.py` (`MainMenuView`)
- `SeedSigner/src/seedsigner/views/seed_views.py` (`SeedsMenuView`)

### B) Codex32 seed load and success flow
Already implemented and should stay unchanged:
- `LoadSeedView` includes "Enter Codex32 Seed".
- `Codex32EntryView` supports S-share and k-of-n recovery.
- `Codex32MasterShareSuccessView` already provides:
  - Show Codex32 Key
  - Load seed
- "Show Codex32 Key" flow already exists (`Codex32MasterSecretWarningView` + display pages).

Relevant files:
- `SeedSigner/src/seedsigner/views/seed_views.py`
- `SeedSigner/src/seedsigner/gui/screens/seed_screens.py`
- `SeedSigner/src/seedsigner/models/codex32.py`
- `SeedSigner/src/seedsigner/models/seed.py` (`Codex32Seed`)

### C) Seed options (non-Codex32)
Already present and should remain unchanged:
- Scan transaction
- Export xpub
- Address explorer
- Backup seed
- Discard seed
- BIP-85 child seed (when enabled)

Relevant file:
- `SeedSigner/src/seedsigner/views/seed_views.py` (`SeedOptionsView`)

### D) PSBT QR transport
Already present and should be reused (no new protocol required):
- PSBT QR decode supports UR2, BBQr, Specter animated base64, base64/base43.
- Signed PSBT QR export uses UR `crypto-psbt`.

Relevant files:
- `SeedSigner/src/seedsigner/models/decode_qr.py`
- `SeedSigner/src/seedsigner/views/scan_views.py`
- `SeedSigner/src/seedsigner/models/encode_qr.py`

---

## 3) Gap analysis (what must change)

### Gap 1: Codex32 backup menu behavior
Current `SeedBackupView` is generic and shows:
- View seed words
- Export as SeedQR (if `seedqr_supported`)

For Codex32 this is not desired. Requirement is:
- Add "View Codex32 Secret"
- Hide/deactivate:
  - View seed words
  - Export SeedQR

### Gap 2: Codex32 secret availability after seed is loaded
Current code shows Codex32 secret during entry success flow, but after loading seed there is no guaranteed stored Codex32 master-share string for backup view reuse.

Needed for backup UX:
- Persist the normalized Codex32 secret with the loaded Codex32 seed object (or equivalent metadata storage).

### Gap 3: PSBT signing robustness for multisig handoff
Current `PSBTFinalizeView` signs then trims via `PSBTParser.trim()`. This can drop metadata needed by downstream cosigner(s).

Needed (based on terminal V2 validation):
- Preserve full signed PSBT metadata for handoff signing.
- Add missing-UTXO precheck with clear user-facing error.
- Keep no-op signing detection behavior.

---

## Final Decisions (Approved)

1. **Implementation mode: Hardening-first (most robust).**

2. **Seed dedupe policy:** Keep one logical seed per `seed_bytes` while preserving metadata.
   - On duplicate entropy, do not create a second entry.
   - If incoming seed has richer Codex32 metadata, merge/promote so Codex32 backup capability is retained.

3. **Backup fallback policy (Codex32):** If Codex32 secret metadata is unavailable, show disabled state/error.
   - Do not fall back to seed words.
   - Do not fall back to SeedQR export.

4. **PSBT default behavior:** Reuse existing SeedSigner PSBT flow and hand off for normal signing.
   - Keep existing parse/review/sign UX path.
   - Add missing-UTXO precheck with clear user-facing error.
   - Preserve signed PSBT metadata for handoff by default (no default trim in finalize path).
   - Keep existing no-op signing detection behavior.

---

## 4) Minimal change design

## A) Keep these areas unchanged
1. `Codex32EntryView` input UX and validation flow.
2. `Codex32MasterShareSuccessView` and "Show Codex32 Key" sequence.
3. `SeedOptionsView` action structure/order.
4. xpub export flow.
5. address explorer flow.
6. discard flow.
7. BIP-85 flow (no disabling).
8. QR decode/encode transport stack.

## B) Codex32-only backup changes

### Proposed behavior
In `SeedBackupView`:
- If selected seed is `Codex32Seed`:
  - show `View Codex32 Secret`
  - do not show `View seed words`
  - do not show `Export as SeedQR`
- Else: keep existing backup menu unchanged.

### Proposed implementation points
1. Add Codex32-specific backup option constant/view route in `SeedBackupView`.
2. Reuse existing warning + display screens (or add thin wrappers) for consistency.
3. Ensure required Codex32 secret is available from loaded seed metadata.

## C) Codex32 seed metadata persistence

### Proposed model extension
Extend `Codex32Seed` to carry optional normalized secret string, e.g.:
- `codex32_master_share: str | None`

Set this during Codex32 entry/recovery before pending seed finalization.

### Why this is minimal
- No storage schema migration required (seed remains in-memory object).
- No impact on BIP39/Electrum seeds.
- Backup view can branch on type and metadata presence.

## D) PSBT signing reliability alignment with terminal V2

### Proposed behavior changes
1. In `PSBTFinalizeView`:
   - sign on original PSBT object
   - do not trim before export (default handoff-safe behavior)
2. Add pre-sign check for missing UTXO data.
3. Route missing-UTXO failures to clear warning/error view message.
4. Keep "Signing Failed" flow for no signature added.

### Why this is still minimal
- QR import/export pipeline unchanged.
- Only finalize/signing internals adjusted.
- Preserves existing user journey.

---

## 5) File-by-file migration map

## 1) `SeedSigner/src/seedsigner/views/seed_views.py`
### Keep
- `LoadSeedView`
- `Codex32EntryView`
- `Codex32MasterShareSuccessView`
- `SeedOptionsView` action list
- xpub/explorer/discard/BIP85 flows

### Change
- `SeedBackupView`:
  - add Codex32 branch with `View Codex32 Secret`
  - suppress words/SeedQR options for Codex32 seeds
- When constructing `Codex32Seed` in entry/recovery paths, include normalized share metadata.

## 2) `SeedSigner/src/seedsigner/models/seed.py`
### Keep
- Existing `Codex32Seed` no-PBKDF2 behavior
- `passphrase_supported = False`
- `bip85_supported` behavior inherited (stays enabled)

### Change
- Add optional Codex32 secret metadata field/accessor used by backup view.
- Keep non-Codex32 seed classes untouched.

## 3) `SeedSigner/src/seedsigner/views/psbt_views.py`
### Keep
- Screen routing and flow structure
- `PSBTSignedQRDisplayView` UR export

### Change
- `PSBTFinalizeView.run`:
  - add missing-UTXO guard
  - stop default trim assignment for signed export
  - preserve signature-count check

## 4) `SeedSigner/src/seedsigner/models/psbt_parser.py`
### Keep
- parse logic, policy detection, fingerprint fill behavior

### Change
- Add helper for missing-UTXO input indices.
- Keep `trim()` available for optional/future compact mode, but not default handoff path.

## 5) `SeedSigner/src/seedsigner/models/decode_qr.py`
### Keep
- No change expected (formats already supported)

## 6) `SeedSigner/src/seedsigner/models/encode_qr.py`
### Keep
- No change expected (UR signed PSBT export remains)

---

## 6) Test impact and additions

## Existing tests to preserve
- `tests/test_flows_psbt.py`
- `tests/test_psbt_parser.py`
- `tests/test_decodepsbtqr.py`
- `tests/test_encodepsbtqr.py`

## Add/adjust tests
1. Codex32 backup menu test:
   - Codex32 seed shows only `View Codex32 Secret`.
   - BIP39 seed backup options unchanged.
2. Codex32 metadata persistence test:
   - secret entered/recovered is available in backup flow.
3. PSBT finalize handoff test:
   - after first signature, resulting PSBT still has required UTXO metadata.
4. Missing-UTXO error test:
   - clear failure path, no crash.

---

## 7) Incremental implementation sequence

### Phase 1: Codex32 backup-only UX
- Implement Codex32 branch in `SeedBackupView`.
- Persist Codex32 secret metadata in `Codex32Seed` creation path.
- Validate no regressions in non-Codex32 backup behavior.

### Phase 2: PSBT robustness parity with terminal V2
- Update finalize flow to preserve metadata.
- Add missing-UTXO guard and user-facing message.
- Run PSBT decode/flow/parser test suite.

### Phase 3: Documentation + polish
- Update integration docs and user-facing notes.
- Capture coordinator export guidance for missing UTXO cases.

---

## 8) Acceptance criteria (must all pass)

1. Codex32 seed entry/recovery flow remains unchanged and functional.
2. Codex32 success screen remains unchanged (Show Codex32 Key / Load seed).
3. In Seeds menu, fingerprints and load behavior unchanged.
4. Seed options remain unchanged for scan/xpub/explorer/discard/BIP85.
5. Backup behavior differs only for Codex32:
   - includes "View Codex32 Secret"
   - excludes seed words + SeedQR options
6. PSBT QR scanning/export formats remain unchanged.
7. Multisig sequential signing handoff works (no metadata-loss regression).
8. Missing-UTXO PSBT fails cleanly with actionable message.

---

## 9) Summary
This migration can be done with a narrow, Codex32-focused delta:
- Codex32 backup specialization + secret persistence
- PSBT finalize reliability updates

Everything else (entry UX, seed options, xpub, explorer, BIP85, discard, QR transport) stays as-is.
