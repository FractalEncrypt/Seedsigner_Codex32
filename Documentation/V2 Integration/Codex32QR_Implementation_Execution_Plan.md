---
description: Execution-ready Codex32QR implementation plan for SeedSigner (phased tasks, file map, and test gates)
---

# Codex32QR Implementation Execution Plan (SeedSigner)

## 1) Phase count and delivery model

We will run **5 development phases total**:

1. **Phase 0**: Type plumbing and profile constants (required)
2. **Phase 1**: Decode + scan import behavior (required)
3. **Phase 2**: Export + transcription + 29x29 guarantee test (required)
4. **Phase 3**: Validation hardening + regressions (required)
5. **Phase 4**: Post-MVP enhancements (optional)

For practical coding, treat this as **4 required phases + 1 optional**.

---

## 2) Locked implementation decisions

These are fixed for this execution plan:

- Codex32QR decode/encode contract is a **canonical share string** (not mnemonic).
- Detection precedence in `detect_segment_type()` is **last** (to minimize regressions).
- Source-of-truth code repo is **SeedSigner**; planning/spec docs remain in `Seedsigner_Codex32`.
- `Scan SeedQR` will accept Codex32QR for now.
- Codex32 backup menu will keep `View Codex32 Secret` and add `Export as Codex32QR`.
- Confirm-scan compare uses uppercase, separator-stripped exact match.
- Non-S share in MVP scan path is a hard error.
- QR EC level remains **L** in MVP.
- Codex32 decode tests go in `tests/test_decodepsbtqr.py`.
- Add a Phase 2 unit test that guarantees **Version 3 / 29x29** for canonical 48-char payload.

### Locked non-S share error copy

- **Title:** `Error`
- **Headline:** `Non-S Share Not Supported`
- **Body:** `This QR is a Codex32 split share. SeedSigner MVP can only scan S-shares. Use Codex32 multi-share recovery to combine shares and recover the S-share.`
- **Action button:** `Back`

---

## 3) Execution status

- [x] Phase 0 - Prep and type plumbing
- [x] Phase 1 - Decode + import (including 1B scan routing and 1C regression fixes)
- [x] Phase 2 - Export + transcription + 29x29 guarantee
- [x] Phase 3 - Validation hardening + regressions
- [ ] Phase 4 - Optional post-MVP enhancements

Latest targeted regression gate:

```powershell
pytest tests/test_seedqr.py tests/test_decodepsbtqr.py tests/test_flows_tools.py tests/test_flows_seed.py
# 63 passed
```

---

## 4) Execution phases with exact tasks

## Phase 0 — Prep and type plumbing

### Code tasks
1. Add `QRType.SEED__CODEX32`.
2. Add Codex32QR profile constants (length=48, prefix=`MS1`, module target=29, EC policy marker `L`).

### File map
- `SeedSigner/src/seedsigner/models/qr_type.py`
- `SeedSigner/src/seedsigner/models/codex32.py`

### Tests
- `SeedSigner/tests/test_seed.py` (or `test_codex32_qr.py` if later split)

### Test names and assertions
1. `test_codex32_qr_profile_constants`
   - Assert `prefix == "MS1"`, `length == 48`, `module_target == 29`, `ec == "L"`.
2. `test_codex32_qr_normalization_is_canonical_uppercase`
   - Input mixed separators/case.
   - Assert normalized output is uppercase with separators removed.

### Exit criteria
- Type compiles and no scanner behavior changes yet.

---

## Phase 1 — Decode + import (MVP core)

### Phase 1A: decode contract + detection

#### Code tasks
1. Add Codex32 detection at the **end** of `detect_segment_type()`.
2. Add single-frame `Codex32QrDecoder`.
3. Integrate into `DecodeQR.add_data()`.
4. Add `DecodeQR.get_codex32_share()`.
5. Add `DecodeQR.is_codex32` property.
6. Include `SEED__CODEX32` in `DecodeQR.is_seed`.

#### File map
- `SeedSigner/src/seedsigner/models/decode_qr.py`

#### Tests (in agreed file)
- `SeedSigner/tests/test_decodepsbtqr.py`

#### Test names and assertions
1. `test_codex32qr_decode_returns_canonical_s_share`
   - Valid S-share input (allow lowercase/separators input form).
   - Assert: `DecodeQRStatus.COMPLETE`.
   - Assert: `qr_type == QRType.SEED__CODEX32`.
   - Assert: `is_seed is True` and `is_codex32 is True`.
   - Assert: `get_codex32_share()` equals canonical uppercase, separator-stripped string.
2. `test_codex32qr_decode_accepts_non_s_share_for_routing`
   - Valid non-S share input.
   - Assert: `DecodeQRStatus.COMPLETE` and `qr_type == QRType.SEED__CODEX32`.
   - Assert: returned share parses to index != `s` (routing handles rejection).
3. `test_codex32qr_decode_invalid_checksum_returns_invalid`
   - Mutate one char in checksum.
   - Assert: `DecodeQRStatus.INVALID`.
4. `test_codex32qr_detection_precedence_regressions`
   - Assert unchanged classification for representative existing inputs:
     - base64 PSBT => `PSBT__BASE64`
     - numeric SeedQR => `SEED__SEEDQR`
     - mnemonic => `SEED__MNEMONIC`
     - bitcoin address => `BITCOIN_ADDRESS`

### Phase 1B: scan routing

#### Code tasks
1. In `ScanView.run()`, add Codex32 branch:
   - S-share: create `Codex32Seed`, set pending seed, route to Codex32 success flow.
   - Non-S share: route to `ErrorView` with locked copy.
2. Preserve all existing non-Codex32 scan behavior.

#### File map
- `SeedSigner/src/seedsigner/views/scan_views.py`

#### Tests
- `SeedSigner/tests/test_flows_tools.py`
- `SeedSigner/tests/test_scan_views.py` (new file for copy lock)

#### Test names and assertions
1. `test__address_explorer__scan_codex32_s_share__sideflow`
   - Simulate scanning Codex32 S-share in `ScanSeedQRView` flow.
   - Assert destination reaches Codex32 success/finalize path.
   - Assert pending seed is `Codex32Seed` and stored master share is canonical uppercase.
2. `test__address_explorer__scan_codex32_non_s_share__routes_to_error`
   - Simulate scanning non-S share in `ScanSeedQRView` flow.
   - Assert `ErrorView` route.
3. `test_scan_seedqr_non_s_error_copy_is_locked`
   - Assert exact title/headline/body/button text match locked copy.

### Exit criteria
- Valid Codex32 S-share scan loads seed.
- Non-S scan yields deterministic hard error.
- No behavior regressions in basic decode tests.

---

## Phase 2 — Export + transcription + 29x29 guarantee

### Code tasks
1. Add `Export as Codex32QR` action to Codex32 backup path.
2. Reuse existing whole/zoomed QR transcription screens where possible.
3. Add Codex32 confirm-scan compare using canonical uppercase string compare.
4. Keep EC at `L` for MVP.

### File map
- `SeedSigner/src/seedsigner/views/seed_views.py`
- `SeedSigner/src/seedsigner/models/encode_qr.py` (if dedicated encoder helper needed)
- `SeedSigner/src/seedsigner/gui/screens/seed_screens.py` (minimal change expected)

### Tests
- `SeedSigner/tests/test_flows_seed.py`
- `SeedSigner/tests/test_seedqr.py`

### Test names and assertions
1. `test_codex32_backup_menu_includes_export_as_codex32qr`
   - Assert Codex32 backup menu includes export action while retaining view-secret behavior.
2. `test_codex32_export_transcribe_confirm_roundtrip`
   - Simulate export -> confirm scan path.
   - Assert success route only when scanned canonical payload matches.
3. `test_codex32qr_mvp_payload_renders_version3_29x29`
   - Use canonical 48-char S-share payload.
   - Assert QR version is 3 and module count is 29.
   - Assert EC policy is L.

### Exit criteria
- Export/transcribe/confirm flow works for Codex32 S-share.
- 29x29 module guarantee test passes.

---

## Phase 3 — Validation hardening and full regressions

### Code tasks
1. Tighten invalid-path handling and error classification messages.
2. Ensure no accidental fallback behavior on invalid Codex32 candidates.

### File map
- `SeedSigner/src/seedsigner/models/decode_qr.py`
- `SeedSigner/src/seedsigner/views/scan_views.py`

### Tests
- Expand existing files:
  - `SeedSigner/tests/test_decodepsbtqr.py`
  - `SeedSigner/tests/test_flows_seed.py`
  - `SeedSigner/tests/test_flows_tools.py`

### Exit criteria
- All targeted Codex32 + QR + flow regressions pass.
- Existing SeedQR/PSBT/address/descriptor decode behavior remains green.

---

## Phase 4 — Optional post-MVP enhancements

1. Split-share QR recovery path (`k=2..5`) via scan-assisted collection.
2. Configurable EC level (L/M).
3. Optional advanced diagnostics UX for scan failures.

---

## 5) Suggested PR slicing

1. **PR-1:** Phase 0 only (types/constants + unit tests)
2. **PR-2:** Phase 1A decode + `test_decodepsbtqr.py` additions
3. **PR-3:** Phase 1B scan routing + flow/copy tests
4. **PR-4:** Phase 2 export/transcribe + 29x29 test
5. **PR-5:** Phase 3 hardening/regressions

---

## 6) Fast test command set

```powershell
pytest tests/test_decodepsbtqr.py -k codex32qr
pytest tests/test_flows_tools.py -k codex32
pytest tests/test_flows_seed.py -k codex32
pytest tests/test_seedqr.py -k codex32qr_mvp_payload_renders_version3_29x29
```

---

## 7) Start coding recommendation

Start with **PR-1 (Phase 0)** immediately. It is low-risk and unlocks the decode work in Phase 1.
