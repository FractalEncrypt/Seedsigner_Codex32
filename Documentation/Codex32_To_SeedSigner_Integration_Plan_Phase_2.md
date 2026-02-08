---
description: Codex32 to SeedSigner Integration - Phase 2 Plan (Multi-Share Recovery)
---

# Codex32 -> SeedSigner Integration (Phase 2)

## Purpose
Implement **multi-share entry, validation, and interpolation** for Codex32 split shares (k-of-n) inside SeedSigner, building on the Phase 1 single S-share flow.

## Current Baseline (Phase 1 Complete)
- Single S-share entry with SeedSigner keyboard UI.
- Validation and normalization via vendored `codex32_min`.
- Conversion to 16-byte seed and BIP39 mnemonic display.
- Success screen with “Show Codex32 Key” and “Load Seed”.

## Phase 2 Status (Completed)
**Completion note:** Feb 6, 2026 (multi-share flow implemented and manual device testing confirmed).
### Functional
1. **Multi-share entry flow** for split shares (S1, S2, ...).
2. **Interpolation recovery** using `Codex32String.interpolate_at` / `ms32_interpolate` to reconstruct the S-share.
3. **Validation & error handling** for:
   - Header mismatch (k / identifier)
   - Duplicate share indices
   - Invalid checksum / malformed shares
4. **User experience updates** for progress, review/edit, and safe exit.
5. **UX polish**: active share box highlighting and OK-button selection after final character.

### Non-Goals (Explicitly Deferred)
- Error-correction (ECW substitution/erasure correction).
- Persistent storage of partial shares across sessions.
- Advanced share management (e.g., save/export share sets).

---

## UX Flow (Implemented)
### Entry Path
1. User selects **Codex32** from seed entry.
2. User enters the **first share** using the existing boxed entry screen.
3. App determines:
   - If share index is **S** -> use Phase 1 flow (unchanged).
   - If share index is **not S** -> continue to split-share flow.

### Split-Share Flow
1. Pre-fill prefix for subsequent shares:
   - `MS1 + k + ident` (case preserved from the first share).
2. For each additional share:
   - Validate checksum and header before accepting.
   - Reject duplicate indices.
   - Allow **Review/Edit**, **Discard invalid share**, or **Discard all shares** (with confirmation).
3. Once **k shares** collected:
   - Run recovery: `Codex32String.interpolate_at(shares, target='s')`.
   - Validate recovered S-share and derive seed.
4. Show **Recovery Success** screen:
   - Display recovered S-share.
   - Provide “Load Seed” and “Show Codex32 Key” actions.

### Error Handling
- **Header mismatch**: prompt re-entry.
- **Duplicate index**: prompt for a different share.
- **Checksum or format error**: invalid-share flow with review/edit/discard options.
- **Recovery failure**: last entered share is discarded and user is returned to invalid-share flow.

---

## Implementation Notes
### Models / Data
- Added a `Codex32ShareCollection` to track `k`, `ident`, `case`, and collected shares.
- Reused existing `validate_codex32_s_share()` and added multi-share validation in the collection.
- Recovery uses `recover_secret_share()` with `Codex32String.interpolate_at()`.

### Views & Screens
- `Codex32EntryView` now branches into the multi-share flow when share index != 's'.
- `Codex32ShareSuccessView` displays progress (shares entered vs required).
- `Codex32ShareInvalidView` adds Review/Edit, Discard invalid, Discard all (with confirmation).
- Discard-all confirmation now returns to **Main Menu**.
- Codex32 entry screen highlights the active box at all times and auto-selects OK after the last character.

---

## Test Status
### Manual (Device)
- ✅ User reports build + device test successful.
- Recommended regression scenarios:
  - **Vector 2** (k=2): verify recovered S-share, seed hex, mnemonic.
  - **Vector 3** (k=3): verify recovered S-share, seed hex, mnemonic.
  - **Error cases**: duplicate share, wrong identifier, wrong k value. (not yet tested)

### Automated (Optional)
- Add unit tests mirroring terminal tool vectors for:
  - share parsing/validation
  - interpolation output

---

## Remaining / Future Work (Optional)
- Optional dedicated **multi-share progress screen** (if current success screen is insufficient).
- Automated test coverage for Codex32 split-share recovery.
- ECW error correction (Phase 3).
- Persistent storage of partial shares (future enhancement).

---

## Dependencies
- Vendored `codex32_min.py` (already in SeedSigner)
- `embit.bip39` for mnemonic conversion
