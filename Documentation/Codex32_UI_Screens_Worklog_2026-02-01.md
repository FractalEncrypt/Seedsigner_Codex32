# Codex32 UI Screens – Worklog & Next Steps (2026-02-01)

## Goal
Generate UI screenshots for the new Codex32 entry flow (Seeds menu + Bech32 keyboard screen) to support design review and define remaining screens and user flow prior to terminal-tool wiring.

## Accomplishments
- Screenshot generator runs successfully on Windows (Python 3.11 venv).
- Codex32 screenshots generated, and the new screens are visible in the `seedsigner-screenshots/en/README.md` index.
- Screenshot generator now completes for `--locale en`.

## Key Fixes / Changes
### 1) Screenshot generator can run without native zbar DLLs (Windows)
We stubbed `pyzbar` in the screenshot generator to avoid native DLL loading. This is safe for the screenshot run because `DecodeQR.add_data()` is used (no actual image decoding is needed).

File: `tests/screenshot_generator/generator.py`
- Added a stub `pyzbar` module to bypass DLL loading.

### 2) gettext shadowing bug fixed
A local `_` variable in `Codex32EntryScreen.__post_init__()` shadowed gettext (`_`), causing `UnboundLocalError`.

File: `src/seedsigner/gui/screens/seed_screens.py`
- Renamed tuple unpack variable to `_bottom`.

### 3) Windows UnicodeEncodeError fixed
README generation on Windows failed with `'charmap'` encoding errors. We explicitly write all README files as UTF-8.

File: `tests/screenshot_generator/generator.py`
- Added `encoding="utf-8"` to `open()` calls for read/write.

## Environment / Setup Notes
- Python 3.11 venv used: `c:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\.venv`
- MSVC runtime installed (2015–2022 x64) but did **not** resolve pyzbar DLL loading.
- zbar/libiconv DLLs copied into `pyzbar` folder, but still failed to load on this host.
- Effective solution: pyzbar stub in generator.

## Commands Used (reference)
- Screenshot generator:
  ```powershell
  .\.venv\Scripts\python -m pytest tests\screenshot_generator\generator.py --locale en
  ```

## Output Location
- Screenshots (English locale):
  `c:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\`
- Index page:
  `seedsigner-screenshots/en/README.md`

---

## Codex32 UI Screens (current)
UI-only screens added for the Codex32 flow (storage wiring deferred):

1. **LoadSeedView**
   - Entry point for loading/typing a seed (starting point for Codex32 flow from Seeds menu).
2. **Codex32EntryView**
   - Bech32 keyboard for entering a Codex32 share.
3. **Codex32ShareInvalidView**
   - Shows invalid share warning (checksum failure).
   - Actions: Review & edit (returns to entry) or Discard.
4. **Codex32DiscardShareConfirmView**
   - Discard confirmation for the current share entry.
   - Actions: Review & edit (returns to entry) or Discard (exit flow).
5. **Codex32ShareSuccessView**
   - Valid non-master share accepted.
   - Displays `M of N shares have been entered`.
   - Actions: Enter next share or Discard.
6. **Codex32MasterShareSuccessView**
   - Valid master share accepted.
   - Actions: Display mnemonic or Load seed.
7. **Codex32MasterSecretWarningView**
   - Dire warning before displaying the master secret.
8. **Codex32MasterSecretDisplayView (Boxes 1-24 / 25-48)**
   - Two-page boxed display of the master secret share.
   - Uses test vector: `MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW`.

## Screenshot References
```
LoadSeedView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\LoadSeedView.png

Codex32EntryView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32EntryView.png

Codex32ShareInvalidView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32ShareInvalidView.png

Codex32DiscardShareConfirmView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32DiscardShareConfirmView.png

Codex32ShareSuccessView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32ShareSuccessView.png

Codex32MasterShareSuccessView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32MasterShareSuccessView.png

Codex32MasterSecretWarningView
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32MasterSecretWarningView.png

Codex32MasterSecretDisplayView_1
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32MasterSecretDisplayView_1.png

Codex32MasterSecretDisplayView_2
  C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\seedsigner-screenshots\en\seed_views\Codex32MasterSecretDisplayView_2.png
```

## Happy Path Flow (expected)
1. **LoadSeedView** → enter Codex32 flow.
2. **Codex32EntryView** → enter a Codex32 share.
3. If **valid non-master share**:
   - **Codex32ShareSuccessView** (shows `M of N`).
   - Tap **Enter next share** → back to **Codex32EntryView**.
   - Repeat until threshold is satisfied.
4. If **valid master share**:
   - **Codex32MasterShareSuccessView**.
   - Tap **Display mnemonic** → **Codex32MasterSecretWarningView**.
   - Continue to **Codex32MasterSecretDisplayView (1-24)**.
   - Tap **Continue to Boxes 25-48** → **Codex32MasterSecretDisplayView (25-48)**.
   - Tap **Finalize Seed** → proceed to seed finalize/options.

## Invalid / Discard Paths
- **Invalid share** after entry:
  - **Codex32ShareInvalidView** appears.
  - **Review & edit** returns to **Codex32EntryView** with the share prefilled.
  - **Discard** exits the flow (recommended to route through discard confirmation when wiring).
- **Discard confirmation** path:
  - **Codex32DiscardShareConfirmView** presents Review & edit or Discard.
  - **Discard** should clear the pending share and exit to the main menu.

## Terminal Tool Wiring Recommendations
1. **Integrate codex32-terminal as a validation layer**
   - Wrap it in a helper (e.g., `seedsigner/models/codex32_validator.py`) to normalize input and return structured results.
2. **Normalized output schema** should include:
   - `is_valid` (bool)
   - `error_type` (`header`, `data`, `checksum`, `unknown`)
   - `share_type` (`master` vs `share`)
   - `threshold_k`, `share_index`, `total_shares` (when available)
   - `master_secret` (when recovered)
3. **View mapping**
   - `invalid` → **Codex32ShareInvalidView**
   - `valid share` → **Codex32ShareSuccessView**
   - `valid master share` → **Codex32MasterShareSuccessView** → warning → display views
4. **Storage (Option A)**
   - Store pending Codex32 share data in `controller.storage` between views.
   - Keep UI screens stateless and use `view_args` only for testing/screenshot overrides.

## Freeze UI Naming/Flow Before Wiring
Any renaming or flow changes should be completed **before** wiring the terminal tool into the UI. Lock down screen titles, button labels, and transitions to avoid rework once validation/state integration begins.

# Next Steps

## A) UI Screens to Design / Add
(From user requirements + design review)
1. **Invalid Codex32 seed header/data/checksum**
   - Error views for:
     - Invalid header
     - Invalid data body
     - Invalid checksum
2. **Valid master S Share**
   - Success/confirmation view for valid master share.
3. **Valid share requiring `(k)` threshold**
   - Success/confirmation view when a share is valid but requires more shares.
4. **X shares left to enter**
   - UI that displays remaining share count.
   - Buttons: enter next share / cancel or discard share.

## B) User Flow Finalization
1. Determine entry path from Seeds menu to Codex32 flow (screen-by-screen).
2. Define transitions from:
   - Share entry → validation results (success / error / needs more shares).
   - Validation → next share prompt or exit to Seeds menu.
3. Confirm where/how “discard share” should be offered.
4. Confirm behavior for partial entry vs. full entry completion.

## C) Terminal Tool Wiring Plan
1. Identify the exact terminal tool commands / API to invoke for:
   - Validate header
   - Validate data
   - Validate checksum
   - Determine share type (master vs share)
   - Determine threshold requirements (k)
2. Decide on data flow between the terminal tool and screen view classes:
   - Input → validation → result structure → screen selection
3. Build minimal integration layer:
   - A helper in `seedsigner/models` or `seedsigner/helpers` that returns structured results for the UI.
4. Add unit tests / integration tests for the validation layer.

---

## Open Questions
1. Which screens should appear for a **valid master S share** vs. **valid non-master share**?
2. Should the “X shares left to enter” prompt appear after every valid share or only when threshold is not met?
3. Do we want a dedicated “discard share” confirmation screen, or just a confirmation toast?

---

## Notes
- The pyzbar stub is localized to the screenshot generator test; production code still expects real pyzbar/zbar DLLs on Windows. If we later need screenshot validation of QR decoding, revisit DLL setup or gate the stub behind a test-only flag.
- Codex32 UI screens are being implemented UI-only first; storage/wiring for pending Codex32 state is deferred until after visual review (Option A planned).
