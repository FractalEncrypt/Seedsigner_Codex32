# Codex32 SeedSigner OS Build Worklog (2026-02-02)

## Goal
Integrate the Codex32 Python dependency chain into the SeedSigner OS (v0.8.6, Pi Zero) Buildroot environment and produce a bootable image with the updated SeedSigner app, then diagnose boot issues.

## Current Status
- **Build completes**, image is generated, but **boot screen never appears** on Pi Zero after flashing.
- Next step: hardware debugging (UART vs USB data) + validate boot files and power/SD integrity.

## Key Changes (Buildroot / OS)
### New external packages (opt/external-packages)
- **libsecp256k1**
  - `opt/external-packages/libsecp256k1/Config.in`
  - `opt/external-packages/libsecp256k1/libsecp256k1.mk`
  - `opt/external-packages/libsecp256k1/libsecp256k1.hash`
- **python-coincurve** (depends on libsecp256k1, python-cffi, python-asn1crypto)
  - `opt/external-packages/python-coincurve/Config.in`
  - `opt/external-packages/python-coincurve/python-coincurve.mk`
  - `opt/external-packages/python-coincurve/python-coincurve.hash`
- **python-bip32** (depends on python-coincurve)
  - `opt/external-packages/python-bip32/Config.in`
  - `opt/external-packages/python-bip32/python-bip32.mk`
  - `opt/external-packages/python-bip32/python-bip32.hash`
- **python-codex32** (depends on python-bip32)
  - `opt/external-packages/python-codex32/Config.in`
  - `opt/external-packages/python-codex32/python-codex32.mk`
  - `opt/external-packages/python-codex32/python-codex32.hash`

### Pi0 external tree updates
- Added new external package Config.in includes:
  - `opt/pi0/Config.in`
- Enabled packages in Pi Zero defconfig:
  - `opt/pi0/configs/pi0_defconfig` enables `libsecp256k1`, `python-coincurve`, `python-bip32`, `python-codex32`.

### Buildroot Python packaging fixes
- **python-setuptools** bumped to **80.10.2**
  - `opt/buildroot/package/python-setuptools/python-setuptools.mk`
  - `opt/buildroot/package/python-setuptools/python-setuptools.hash`
- **Removed obsolete patch** for setuptools `--executable` support
  - `opt/buildroot/package/python-setuptools/0001-add-executable.patch` (deleted)
- **pkg-python.mk changes**
  - `SETUPTOOLS_USE_DISTUTILS` set to `local` for setuptools packages
  - `--executable` option removed due to setuptools 80.10.2
  - `opt/buildroot/package/pkg-python.mk`
- **python-numpy** override
  - Set `SETUPTOOLS_USE_DISTUTILS=stdlib` for numpy
  - `opt/buildroot/package/python-numpy/python-numpy.mk`
- **python-pypa-build** dependency fix
  - Added `host-python-toml` (replaced `host-python-tomli` to avoid circular dependency)
  - `opt/buildroot/package/python-pypa-build/python-pypa-build.mk`
- **python-setuptools-scm**
  - Switched to **pep517** build and added `host-python-tomli`
  - `opt/buildroot/package/python-setuptools-scm/python-setuptools-scm.mk`
- **python-packaging** bumped to **24.2** (required by setuptools >=77)
  - `opt/buildroot/package/python-packaging/python-packaging.mk`
  - `opt/buildroot/package/python-packaging/python-packaging.hash`

### Disk image size fix
- **post-image** script updated to avoid FAT disk full error during boot file copy
  - `opt/pi0/board/post-image-seedsigner.sh`
  - `dd if=/dev/zero of=disk.img bs=1M count=128`

## Build Commands Used
(Executed inside docker container `seedsigner-os-stock-build-images-1`)

**Copy modified SeedSigner app into rootfs overlay + build:**
```
docker exec seedsigner-os-stock-build-images-1 bash -lc \
  "rm -rf /opt/rootfs-overlay/opt/src/seedsigner && \
   rsync -a --delete \
     --exclude='.git' --exclude='.github' --exclude='tests' --exclude='docs' \
     --exclude='*.md' --exclude='__pycache__' --exclude='*.pyc' \
     --exclude='.pytest_cache' --exclude='.ruff_cache' \
     /opt/src/seedsigner-local/ /opt/rootfs-overlay/opt/src/seedsigner/ && \
   cd /opt && ./build.sh --pi0 --app-branch=0.8.6 --skip-repo"
```

## Known Issues Encountered (Resolved)
- setuptools 80.10.2 removed `--executable` option → removed usage in Buildroot.
- numpy build required `SETUPTOOLS_USE_DISTUTILS=stdlib` override.
- host-python-pypa-build required toml/tomli dependency (circular dependency resolved).
- host-python-setuptools-scm required packaging>=24.2 → bumped python-packaging.
- libsecp256k1 hash mismatch → corrected tarball hash name.
- post-image FAT partition disk full → increased disk image size (now 128MB).

## Current Open Issue
**Pi Zero boots to black screen (no boot splash).**
- Need hardware debug: UART serial vs USB power/data cable diagnostics.
- Verify:
  - SD card image integrity, correct partitioning, and `seedsigner_os.img` content.
  - Power supply stability / cable quality.
  - Whether boot files are present on FAT partition.

## Suggested Next Actions
1. **UART debug** (recommended if available) to capture boot logs.
2. Inspect the generated image and confirm boot partition contents (bootcode.bin, start_x.elf, cmdline.txt, config.txt, zImage, dtb files).
3. Try alternative SD card / power cable.

---
**Note**: This document summarizes the changes performed to integrate Codex32 dependency chain and fix Buildroot packaging issues leading to a successful build output, prior to investigating the remaining boot failure.
