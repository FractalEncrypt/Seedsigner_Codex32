---
# Codex32 SeedSigner Dev Flow (SeedSigner + seedsigner-os-stock)

This document captures the working development workflow for Codex32 integration.

## Repos
- **App code (edit here):**
  - `C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner`
- **OS build repo (build here):**
  - `C:\Users\FractalEncrypt\Documents\Windsurf\seedsigner-os-stock`

## Workflow Overview
1. **Edit app code** in the SeedSigner repo.
2. **Sync app code into rootfs-overlay** in `seedsigner-os-stock`.
3. **Build the OS image** with the skip-repo/no-clean command.
4. **Flash the image** from `seedsigner-os-stock\images` to SD and test on device.

## 1) Edit app code
Work only in the app repo:
```
C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner
```

## 2) Sync app into rootfs-overlay
Sync the full app package so imports are consistent:
```powershell
robocopy "C:\Users\FractalEncrypt\Documents\Windsurf\SeedSigner\src\seedsigner" `
  "C:\Users\FractalEncrypt\Documents\Windsurf\seedsigner-os-stock\opt\rootfs-overlay\opt\src\seedsigner" `
  /MIR /XD "__pycache__" ".pytest_cache" ".ruff_cache" /XF "*.pyc"
```

Notes:
- This copies **only** `src/seedsigner` (not tests/docs), which avoids missing-symbol import errors.
- If you want to include extra resources, add them under `src/seedsigner` in the app repo.

## 3) Build image (skip-repo/no-clean)
From the `seedsigner-os-stock` repo folder:
```powershell
$env:DOCKER_DEFAULT_PLATFORM = 'linux/amd64'
$env:SS_ARGS = "--pi0 --skip-repo --no-clean"
docker compose up --force-recreate --build
```

If you need to stop the build:
```powershell
docker compose down
```

## 4) Flash image and test
The image will be created under:
```
C:\Users\FractalEncrypt\Documents\Windsurf\seedsigner-os-stock\images
```
Flash the newest `seedsigner_os.*.pi0.img` to the SD card and test on device.

## Troubleshooting
- **ImportError after boot**: usually indicates the overlay app code is older than the repo.
  - Re-run the robocopy sync to refresh overlay.
- **Build errors with missing hashes**: use the repo that already builds (currently `seedsigner-os-stock`).
