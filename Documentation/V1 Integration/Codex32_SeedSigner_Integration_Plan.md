---
description: Codex32 SeedSigner integration plan
---

# Codex32 → SeedSigner Integration Plan (Happy Path First)

## 1) Goal & scope
- **Goal:** Wire Codex32 seed import into SeedSigner using existing UI screens and SeedSigner conventions, with a safe incremental rollout.
- **Phase 1 (Complete):** Single 48‑char **S** share (unshared secret), checksum+header validation, conversion to master seed bytes, and normal SeedSigner finalize flow.
- **Phase 2 (Planned):** Multi‑share recovery (k‑of‑n shares) using interpolation, share‑entry UX, duplicate‑index guardrails.
- **Future scope:** Error‑correction (ECW), 256‑bit (74‑char) secrets, and persistent recovery progress.

## 2) Current assets & integration touchpoints
**Already in SeedSigner:**
- Codex32 entry, validation, and status screens wired in `seed_views.py` and `seed_screens.py`. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/views/seed_views.py#276-468 @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/gui/screens/seed_screens.py#558-1003
- Codex32 keyboard flow supports box navigation, arrow paging, review/edit restore, and OK highlighting. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/gui/screens/seed_screens.py#558-1003
- `Codex32Seed` model (raw seed bytes, no PBKDF2) in `seed.py`. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py#180-205
- Codex32 parsing/validation + recovery helper in `models/codex32.py` using vendored `codex32_min.py`. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32.py#1-119
- Existing seed flows and storage in `seed_storage.py` + `Seed` model. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed_storage.py#1-106 @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py#1-205

**Available reference implementation:**
- Codex32 terminal tool model logic for validation, share recovery, and mnemonic display. @c:/Users/FractalEncrypt/Documents/Windsurf/Seedsigner_Codex32/codex32_terminal/src/model.py#1-81

**Spec guidance:**
- Wallets must validate checksum + header; do not apply BIP39 PBKDF2; use raw master seed bytes for BIP32. @c:/Users/FractalEncrypt/Documents/Windsurf/Seedsigner_Codex32/Documentation/wallets.md#25-82

## 3) Key decisions (resolved)
1) **Seed representation:** Implemented `Codex32Seed` with raw seed bytes (no PBKDF2). @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py#180-205
2) **Passphrase support:** Disabled for Codex32 seeds (raising on non‑empty passphrase). @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py#197-205
3) **Dependency strategy:** Vendored minimal Codex32 implementation (`codex32_min.py`) to avoid external dependency. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32_min.py#1-400
4) **Share length support:** Enforced 48‑character (128‑bit) shares in Phase 1. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32.py#51-87

## 4) Integration architecture (happy path first)
### 4.1 Codex32 module (pure logic)
Implemented `seedsigner/models/codex32.py` mirroring terminal behavior:
- `sanitize_codex32_input()`
- `parse_codex32_share()`
- `validate_codex32_s_share()`
- `codex32_to_seed_bytes()`
- `seed_bytes_to_mnemonic()` (display‑only; do **not** use for seed generation)
- `recover_secret_share()` (Phase 2)

**Notes:** Module is pure and testable (no UI references). @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32.py#1-119

### 4.2 Storage additions (Phase 2)
Phase 1 uses `SeedStorage.set_pending_seed()` directly with `Codex32Seed`. For Phase 2 we still need:
- `pending_codex32_shares: list[Codex32String | str]`
- `pending_codex32_header: {threshold, identifier, length, share_indices}`
- Helper methods:
  - `init_pending_codex32()`
  - `add_codex32_share()`
  - `clear_pending_codex32()`
  - `get_pending_codex32_status()` (entered/total)

### 4.3 Codex32 seed model
Implement a Codex32 seed class that uses raw seed bytes:
- `Codex32Seed(seed_bytes)`
  - `seed_bytes` set directly (no PBKDF2)
  - `mnemonic_display` property from `seed_bytes_to_mnemonic()` for display only
  - `passphrase_supported = False` (if we decide to disable passphrase)

Integrate it into `SeedStorage` finalize flow so Codex32 seeds appear alongside standard BIP39 seeds.

## 5) Implementation phases

### Phase 1 — Happy path: single S‑share (complete)
**Goal:** Enter a 48‑char S‑share, validate it, load seed, finalize.

**Completed work:**
1) **Model layer**
   - `seedsigner/models/codex32.py` implemented from terminal logic. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32.py#1-119
2) **Seed model**
   - `Codex32Seed` added for raw seed bytes (no PBKDF2). @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py#180-205
3) **View wiring**
   - `Codex32EntryView` validates S‑share and routes success/error. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/views/seed_views.py#276-468
4) **UI/UX refinements**
   - Box navigation, arrow paging, OK highlighting, review/edit restore. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/gui/screens/seed_screens.py#558-1003
5) **Finalize flow**
   - Codex32 seeds finalize via standard flow; passphrases disabled at model level.
6) **Device test**
   - Happy path validated on device (share entry → success → seed loaded).

**Exit criteria:** ✅ S‑share import works on device and adds a usable seed to the SeedSigner menu.

### Phase 2 — Multi‑share recovery (k‑of‑n)
**Goal:** Enter k shares (same header), recover S share, finalize.

1) **Header enforcement & prefill**
   - On first share, store header (k + identifier + length).
   - For subsequent shares, prefill header in entry UI (k + identifier) and disallow repeated share indices.
2) **Share progress UI**
   - After each valid share: show `Codex32ShareSuccessView` with `entered_shares/total_shares`.
3) **Recovery**
   - Once `k` shares entered, call `recover_secret_share()` to recover the S share. @c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32.py#111-118
   - Validate recovered S share and then follow Phase 1 flow.
4) **Abort paths**
   - `Discard` clears pending shares, returns to main menu.

**Exit criteria:** k‑of‑n shares produce the expected S share and seed on device.

## 6) Testing strategy
- **Unit tests (host):**
  - Port terminal test vectors for S‑share and k‑of‑n recovery.
  - Validate `seed_bytes_to_mnemonic()` output for known vectors.
- **Integration tests (host):**
  - Minimal: validate `Codex32EntryView` routing for valid/invalid paths.
- **Device tests:**
  - Run after Phase 1 and Phase 2 to verify actual input UX and persistence.

## 7) Implementation checklist (per phase)
- [x] Vendored Codex32 implementation (`codex32_min.py`).
- [x] Add `seedsigner/models/codex32.py` module.
- [x] Implement `Codex32Seed` class (raw seed bytes, no PBKDF2).
- [x] Wire `Codex32EntryView` validation + routing.
- [x] Wire success/invalid/discard views to new logic.
- [x] Device validation on real hardware (happy path).
- [ ] Extend `SeedStorage` for pending codex32 shares (Phase 2).
- [ ] Add multi‑share entry views + progress UI (Phase 2).
- [ ] Implement recovery flow using `recover_secret_share()` (Phase 2).
- [ ] Unit tests for model + recovery.

## 8) Open questions / decisions needed
1) **Storage representation:** Where should multi‑share state live (SeedStorage vs separate Codex32 session object)?
2) **UI copy:** Do we want dedicated error screens for header/data/checksum distinctions (beyond the current invalid share screen)?
3) **Share‑entry UX:** Should the “X shares left” view show after every valid share, or only when threshold not met?
4) **Share confirmation:** Do we want a “confirm share details” step before accepting each share?

## 9) Proposed incremental build/test cadence
- **After Phase 1:** Build image → flash → confirm S‑share import.
- **After Phase 2:** Build image → flash → confirm k‑of‑n recovery and finalize flow.
- **After Phase 3/4:** Build image → flash → test error correction and 256‑bit support.

## 10) Development build workflow (Windows + Docker)
Use this for **fast rebuilds** while iterating on Codex32 changes.

**Prereqs**
- Local SeedSigner repo with changes: `C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner`
- SeedSigner OS build repo: `C:\Users\FractalEncrypt\Documents\Windsurf\seedsigner-os-2`
- Docker container created from `seedsigner-os-2` (via `docker compose up -d`)
- `docker-compose.yml` includes the local mount:
  ```yaml
  - C:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner:/opt/src/seedsigner-local
  ```

**One‑liner rebuild (PowerShell):**
```powershell
docker exec seedsigner-os-2-build-images-1 bash -lc "rm -rf /opt/rootfs-overlay/opt/src/seedsigner && cp -R /opt/src/seedsigner-local /opt/rootfs-overlay/opt/src/seedsigner && cd /opt && ./build.sh --pi0 --app-branch=0.8.6 --no-clean --skip-repo"
```

**Output image:**
`C:\Users\FractalEncrypt\Documents\Windsurf\seedsigner-os-2\images\seedsigner_os.0.8.6.pi0.img`

**Notes**
- If you hit `mkfs.fat ... Disk full`, increase `opt/pi0/board/post-image-seedsigner.sh` image size (e.g., `count=256`).
