---
description: Codex32 to SeedSigner Integration - Phase 1 Summary & Phase 2 Plan
---

# Codex32 → SeedSigner Integration (Phase 1)

## Scope (Phase 1)
Phase 1 focused on the **happy-path** for a **single S-share (master share)**:
- Enter a Codex32 share using the on-device keyboard UI.
- Validate and normalize the share.
- Convert the share to a 16-byte seed and load it into SeedSigner as a Codex32 seed.
- Provide a success screen and optional display of the Codex32 key.

This phase intentionally excludes multi-share recovery and interpolation.

---

## Origin: Codex32 Terminal Tool (Baseline)
The initial Codex32 work started as a standalone terminal tool located at:
```
C:\Users\FractalEncrypt\Documents\Windsurf\Seedsigner_Codex32\codex32_terminal
```

Key behaviors in the terminal tool:
- Parses and validates Codex32 strings (header, length, checksum, data).
- Uses the upstream `codex32` Python library for encode/decode and checksum validation.
- Converts recovered master seed bytes to a BIP39 mnemonic via `embit.bip39`.
- Supports interpolation (recovery) when given multiple shares (future Phase 2 scope).

---

## Vendoring Codex32 into SeedSigner
To keep the SeedSigner runtime lightweight and self-contained, the upstream `codex32`
Python dependency was replaced with a **vendored minimal implementation**:

- Added `codex32_min.py` (pure Python) under:
  ```
  src/seedsigner/models/codex32_min.py
  ```
- Updated `codex32.py` to import from the vendored implementation.
- Removed the external `codex32` dependency from `requirements.txt`.

This ensures the Codex32 logic is present at runtime without additional pip installs.

---

## SeedSigner Integration (Happy Path)

### New/Updated Components
- **Models**
  - `Codex32Seed` class (SeedSigner model) now accepts **16-byte seed entropy** and
    derives a BIP39 mnemonic via `embit.bip39`.

- **Codex32 entry UI**
  - `Codex32EntryScreen` handles boxed share entry, keyboard navigation, and paging.
  - Uses a 4-box window with left/right arrow navigation.
  - Entry validation through `codex32_model.validate_codex32_s_share`.

- **Views**
  - `Codex32EntryView` orchestrates screen entry, validation, and transitions.
  - `Codex32ShareInvalidView` allows “Review & edit” with share preservation.
  - `Codex32MasterShareSuccessView` presents final actions:
    - “Show Codex32 Key”
    - “Load Seed”

### UI/UX fixes completed in Phase 1
- Arrow selection now works via D-pad center + vertical buttons.
- Full navigation between boxes, arrows, and keyboard (no forced backspacing).
- Right/left page navigation restored.
- OK button highlights after final character entry.
- Review/Edit preserves the share instead of resetting it.
- Success screen label updated to “Show Codex32 Key”.

---

## Phase 1 Status
✅ **Happy path fully functional** for entering a single S-share and loading the seed.

---

# Phase 2 Goals: Split Share Recovery

Phase 2 will focus on **multi-share recovery and interpolation**:

## Functional Goals
1. **Multi-share entry flow**
   - Add support for entering multiple shares (S1, S2, ...).
   - Track progress across shares and allow review/edit per share.

2. **Interpolation / recovery**
   - Use the vendored Codex32 recovery function (`ms32_recover`) to reconstruct
     the master share from multiple splits.

3. **Validation and error handling**
   - Detect invalid or mismatched shares early.
   - Provide clear error messages for header/identifier mismatch and checksum failures.

4. **User experience updates**
   - Multi-share progress screen.
   - Recovery success screen (master share shown and/or auto-loaded).
   - “Discard share” confirmation and safe exit paths.

## Technical To-Do (Phase 2)
- Extend Codex32 views to support a share list / share collection flow.
- Add a split-share recovery view that calls `ms32_recover` and validates output.
- Ensure storage model can handle multiple pending shares before final seed creation.

---

## Notes / References
- Main app repo: `C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner`
- OS build repo: `C:\Users\FractalEncrypt\Documents\Windsurf\seedsigner-os-stock`
- Dev workflow doc: `Codex32_SeedSigner_Dev_Flow.md`

