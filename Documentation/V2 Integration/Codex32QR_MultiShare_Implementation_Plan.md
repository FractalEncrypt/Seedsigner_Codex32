---
description: Planning doc for Codex32 multi-share import/export support in SeedSigner (no-code phase)
---

# Codex32QR Multi-Share Import/Export Implementation Plan (Planning Only)

## 1) Purpose

This document defines the next implementation phase after S-share MVP:
- Support **multi-share import** (QR scan + manual entry).
- Support **multi-share export** (QR backup by selected share index).
- Preserve current S-share-only behavior when the user only has/imports one S-share.

No code changes are included in this phase; this is an execution-ready plan.

---

## 2) Locked behavior requirements (from current product direction)

1. If a user enters/imports only an **S-share**, then backup supports only that **S-share**.
2. If a user enters/imports **multiple split shares** (manual and/or QR), backup supports:
   - all entered split shares, and
   - the **S-share not originally entered** (if derivable from the collected set).
3. User can choose which share index to export by QR.
4. Supported export target set is capped at:
   - **max 5 split shares**, plus
   - **1 S-share**.
5. Export is enabled only after enough valid, compatible shares are collected to recover S-share.

---

## 3) Scope

### In scope
- New share-collection UX for Codex32 (manual + scan).
- Share-set validation, de-duplication, and canonicalization.
- Share-index export selection UX.
- Codex32QR export for each eligible share.
- Test coverage for multi-share import/export and guardrails.

### Out of scope (this phase)
- Changing PSBT signing architecture.
- New QR transport formats.
- Non-Codex32 seed backup behavior changes.

---

## 4) Conceptual model

Introduce a Codex32 share-set model (name TBD) with these responsibilities:

- Track collected shares by normalized canonical payload.
- Track metadata needed for compatibility checks (identifier, threshold policy, index).
- Distinguish:
  - entered shares,
  - derived shares (especially S-share).
- Provide ordered export candidates: `S + split-share indices (2..5 as present)`.
- Enforce maximum counts and deterministic conflict handling.

### Suggested state shape

- `entered_shares_by_index: Dict[str, Codex32Share]`
- `derived_shares_by_index: Dict[str, Codex32Share]`
- `session_id` / identifier metadata
- `threshold / policy metadata`
- `validation_errors: List[...]`

---

## 5) Import behavior design

## 5.1 Entry points

1. **Scan flow**
   - Keep current fast path for pure S-share scan.
   - Add a dedicated "collect split shares" path that accepts non-S shares.

2. **Manual entry flow**
   - Add manual entry for Codex32 share string(s), one share at a time.
   - Reuse canonical normalization and parse validation.

## 5.2 Validation rules

For each entered/scanned share:
- Must parse as valid Codex32 share string.
- Must match active set identity/policy (same family/session parameters).
- Duplicate identical share: accepted but ignored with deterministic UI copy.
- Duplicate index with different payload: hard error (conflict).
- Reject if exceeding maximum supported split-share count for MVP phase.

## 5.3 Completion rules

- S-only mode:
  - one valid S-share -> current Codex32 seed flow remains unchanged.
- Multi-share mode:
  - collection remains open until user chooses "Done".
  - if enough compatible shares are present, derive missing S-share for export menu.
  - if insufficient shares for derivation, export is disabled; user must continue adding valid shares.

---

## 6) Export behavior design

## 6.1 Export menu behavior

### Case A: only S-share is loaded
Show current MVP behavior:
- View Codex32 secret
- Export S-share as Codex32QR

### Case B: multi-share set loaded
Show a share-selection menu:
- Export S-share (entered or derived)
- Export index 2
- Export index 3
- Export index 4
- Export index 5
Only show indices that are available and valid in the current set.

## 6.2 Export selection constraints

- Disable/selectively hide options that are unavailable.
- Clearly label whether S-share is:
  - entered, or
  - derived from split-share set.
- Do not enable export selection until share-set validity is sufficient to recover S-share.
- Enforce cap: max 5 split + 1 S for selectable exports.

## 6.3 Export payload constraints

- Keep existing canonical Codex32QR payload contract (uppercase, separator-stripped).
- Preserve current QR profile target (v3/29x29 for canonical payload when applicable).

---

## 7) UX flow additions (high level)

1. **Codex32 Import Mode View**
   - Options: `Scan S-share (quick import)` / `Collect split shares` / `Manual entry`.

2. **Share Collection Progress View**
   - Shows collected indices and validation status.
   - CTA: `Add another share`, `Done`, `Cancel`.

3. **Share Conflict/Error Views**
   - Duplicate conflict, incompatible set, parse invalid, max-share reached.

4. **Share Export Selection View**
   - One-button-per-index export route.

5. **Export Transcription/Confirm Reuse**
   - Reuse existing Codex32 QR transcription + confirm scan flow, parameterized by selected share.

---

## 8) Proposed file touchpoints (planning map)

- `SeedSigner/src/seedsigner/models/codex32.py`
  - share-set model, compatibility/derivation helpers.

- `SeedSigner/src/seedsigner/models/decode_qr.py`
  - enable multi-share collection mode decoding paths (non-S no longer always terminal error in collection context).

- `SeedSigner/src/seedsigner/views/scan_views.py`
  - route split shares to collection flow when in multi-share mode.

- `SeedSigner/src/seedsigner/views/seed_views.py`
  - import-mode entry, share progress UI, export-index selection.

- `SeedSigner/src/seedsigner/gui/screens/seed_screens.py`
  - minimal new screen components for progress/selection/copy.

- Tests
  - `SeedSigner/tests/test_decodepsbtqr.py`
  - `SeedSigner/tests/test_flows_tools.py`
  - `SeedSigner/tests/test_flows_seed.py`
  - optionally `SeedSigner/tests/test_seed.py` for share-set model rules.

---

## 9) Test strategy (planning)

## 9.1 Decode/model tests

1. Multi-share set accepts compatible indices and rejects incompatible shares.
2. Duplicate identical share is idempotent.
3. Duplicate index with conflicting payload is rejected.
4. Derived S-share is available only when share set is sufficient.

## 9.2 Flow tests

1. Scan path: collect 2+ split shares then export selected index by QR.
2. Manual path: enter shares, derive S, export derived S.
3. S-only path remains unchanged (no multi-share-only options shown).
4. Export selector shows only available indices.
5. Non-collection scan path keeps current hard-error behavior for non-S shares.

## 9.3 Regression tests

- Preserve existing SeedQR/PSBT/address behavior.
- Preserve current Codex32 S-share MVP roundtrip and 29x29 guarantee tests.

---

## 10) Phased execution proposal

1. **Phase MS-0: Model + validation scaffolding**
   - Share-set model + unit tests only.

2. **Phase MS-1: Multi-share collection import flows**
   - Scan/manual collection UX + conflict handling.

3. **Phase MS-2: Export selection and QR backup**
   - Index picker + export/transcription wiring.

4. **Phase MS-3: Hardening + regressions**
   - Edge-case handling + full targeted suite.

---

## 11) Locked decisions for coding kickoff

1. Require enough valid compatible shares to recover `S` before enabling multi-share export (no partial-share export before recoverability).
2. In collection mode, conflicting duplicate index may be replaced, but only after explicit user confirmation.
3. Export ordering is always `S` first, then numeric indices.
4. Derived S-share must be visually tagged as `Derived` across backup/confirm screens.

---

## 12) Exit criteria for this planning phase

- Multi-share import/export behavior is fully specified.
- Locked UX decisions and edge-case rules are documented.
- Implementation phases and test gates are ready for coding kickoff.
