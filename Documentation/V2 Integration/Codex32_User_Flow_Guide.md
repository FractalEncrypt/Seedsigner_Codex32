# Codex32 User Flow Guide (SeedSigner V2)

## 1) Who this guide is for

This guide is for users who are working with Codex32 shares created by hand (worksheet + pencil), and want to safely import, verify, recover, and back up in SeedSigner.

This specifically covers your scenario:

- User has split shares (for example 2-of-N) from worksheets
- User may **not** have completed the extra checksum-validation worksheet yet
- User may not have an `S` share yet

SeedSigner is used to **verify** and recover from hand-calculated shares. It does not short-circuit the trustless process by computing a replacement checksum for users.

---

## 2) Codex32 screens list (user-facing)

## Entry points

1. **Load a Seed** menu
   - `Enter Codex32 Seed`
   - `Scan Codex32 Share`

## Core Codex32 entry/recovery flow

2. `Codex32EntryView` (manual character entry in numbered boxes)
3. `ScanCodex32ShareView` (camera scan for Codex32 share)
4. `Codex32ShareInvalidView` (invalid header/data/length/checksum)
5. `Codex32ShareConflictConfirmView` (same index, different share)
6. `Codex32ShareSuccessView` (share accepted, continue flow)
7. `Codex32DiscardAllSharesConfirmView`
8. `Codex32MasterShareSuccessView` (threshold reached, `S` recovered or validated)
9. `Codex32MasterSecretWarningView`
10. `Codex32MasterSecretDisplayView` (Boxes 1-24, then 25-48)

## Backup/export after seed is loaded

11. `SeedBackupView` (Codex32 options appear for Codex32Seed)
12. `Codex32BackupShareSelectView` (choose `S` or split share QR export)
13. `Codex32BackupUnavailableView` (if export metadata is missing/inconsistent)
14. `SeedTranscribeSeedQRWarningView` (Codex32QR warning path)
15. `SeedTranscribeSeedQRWholeQRView`
16. `SeedTranscribeSeedQRZoomedInView`
17. `SeedTranscribeSeedQRConfirmQRPromptView` (Confirm Codex32QR)
18. `SeedTranscribeSeedQRConfirmScanView`
19. `SeedTranscribeSeedQRConfirmWrongSeedView`
20. `SeedTranscribeSeedQRConfirmInvalidQRView`
21. `SeedTranscribeSeedQRConfirmSuccessView`

---

## 3) End-to-end flow: paper shares -> recovered secret -> loaded seed

## Phase A: Prepare from worksheets / printable cards

1. From your worksheet, copy each share exactly as written.
2. If needed, pre-stage each share on printable cards so manual entry is easier:
   - `Seedsigner_Codex32/Printable Codex32 Share backup cards/`
   - Box numbering matches worksheet/SeedSigner box numbering.
3. If you have not done worksheet checksum verification yet, continue anyway: SeedSigner can verify by validating the full share string during entry.
   - If verification fails in the seedsigner of a share that you've not verified manually, then you'll need to go back to the worksheet and recompute the share.

## Phase B: Start import in SeedSigner

Choose either:

1. `Load a Seed -> Enter Codex32 Seed` (manual first share), or
2. `Load a Seed -> Scan Codex32 Share` (scanned first share).

Both routes converge to Codex32 share validation + collection.

## Phase C: Share validation behavior (important trust model)

When a share is submitted, SeedSigner validates:

- format/header (`MS1`, threshold/index structure)
- length
- data/checksum

If invalid -> `Codex32ShareInvalidView`

User choices there:

1. **Review & edit** (fix the entered characters)
2. **Discard invalid share** (re-enter same share slot from blank)
3. **Discard all shares**

This preserves the trustless process: the user fixes worksheet/math/input; SeedSigner does not generate a substitute checksum share.

## Phase D: Build up to threshold `k`

After each valid share, `Codex32ShareSuccessView` offers:

1. **Enter next share** (manual)
2. **Scan next share**
3. **Discard**

So users can alternate manual + scan for each subsequent share.

### Duplicate index conflict path

If a new share uses an already-entered index but different content:

- `Codex32ShareConflictConfirmView`
- User chooses either:
  1. **Replace existing share**, or
  2. **Keep existing share** and continue

## Phase E: Threshold reached

Once `k` valid compatible shares are present, SeedSigner recovers/validates `S` and routes to:

- `Codex32MasterShareSuccessView`

User can then:

1. **Show Codex32 Key** -> warning -> two-page master display (boxes 1-24 then 25-48)
2. **Load seed** -> continue to finalize and load into SeedSigner

---

## 4) Path for users who already have an `S` share

If user enters/scans a valid `S` share directly:

- Seed can be loaded without split-share collection
- User still gets the master-share success and display/load options

---

## 5) After loading: what user can do

After `Finalize`, user lands in `SeedOptionsView` and can use the seed like any other loaded seed:

1. Scan/sign PSBTs
2. Export xpub
3. Address explorer
4. Sign message
5. Backup seed

For Codex32 backups specifically:

- `Backup seed -> View Codex32 Secret` (display in numbered boxes)
- `Backup seed -> Export as Codex32QR`
  - If multiple shares available, `Codex32BackupShareSelectView` lets user choose which share QR to transcribe/export.

---

## 6) Printable cards workflow recommendations

Practical operator workflow:

1. Keep worksheet as source of truth.
2. Copy share to printable card (temporary transport layer).
3. Enter/scan into SeedSigner for validation.
4. If invalid, return to worksheet process and recompute/rewrite (do not trust ad-hoc edits).
5. After recovery, back up `S` and required split shares onto durable media (e.g., metal), using printable cards only as staging.

---

## 7) Quick flow map

1. Prepare handwritten share(s) -> optional printable card staging
2. Load Seed -> Enter or Scan Codex32
3. Invalid? -> fix/re-enter (or discard)
4. Valid -> success screen -> enter/scan next share
5. Repeat until `k` valid shares
6. Master share success -> display key and/or load seed
7. Finalize seed
8. Use seed for normal SeedSigner operations
9. Backup via Codex32 secret display and/or Codex32QR export + confirmation scan
