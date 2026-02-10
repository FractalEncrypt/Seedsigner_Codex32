# SeedSigner Windows Development Setup Guide

This guide describes how to set up a development environment for SeedSigner on Windows, specifically addressing the challenges with Pillow, RAQM, and DLL dependencies required for pixel-perfect screenshot generation.

## Prerequisites

*   **Python 3.11** (Ensure it is added to your PATH)
*   **Git**
*   **PowerShell** (Recommended terminal)

## Standard Setup

1.  **Clone the Repository**
    ```powershell
    git clone https://github.com/SeedSigner/SeedSigner.git
    cd SeedSigner
    ```

2.  **Create a Virtual Environment**
    ```powershell
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment**
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```

4.  **Install Dependencies**
    ```powershell
    pip install -r requirements.txt
    ```

## Enabling RAQM Support (Fixed Text Layout)

SeedSigner uses `libraqm` for complex text layout (e.g., for multi-language support). On Windows, the standard Pillow wheels often lack proper RAQM support or have DLL linkage issues. Without this, screenshot generation will fail or look incorrect.

### The Issue
*   Pillow requires `raqm.dll`, `harfbuzz.dll`, `fribidi.dll`, and `freetype.dll` to be present in the DLL search path.
*   Common builds of these DLLs (e.g., from vcpkg) may link against Debug versions (e.g., `freetyped.dll`) even in Release builds, causing "Module not found" errors when only Release DLLs (`freetype.dll`) are present.

### The Fix

We need to provide the correct Release-mode DLLs and ensure `raqm-0.dll` links against them correctly.

#### 1. Acquire the DLLs
You need the following DLLs (x64 Release versions):
*   `freetype.dll`
*   `harfbuzz.dll`
*   `raqm-0.dll` (or `raqm.dll`)
*   `fribidi-0.dll` (or `fribidi.dll`)
*   `libpng16.dll`
*   `zlib1.dll`
*   `brotlicommon.dll`
*   `brotlidec.dll`
*   `bz2.dll`

These can be built using `vcpkg` or obtained from a known good source.

#### 2. Install DLLs
Copy these DLLs into **two** locations to ensure Python and Pillow can find them:
1.  `.\.venv\Scripts\`
2.  `.\.venv\Lib\site-packages\PIL\`

#### 3. Binary Patch `raqm-0.dll` (If necessary)
If you are using DLLs where `raqm-0.dll` was built linking against `freetyped.dll` (Debug) but you only have `freetype.dll` (Release):

1.  Open `raqm-0.dll` in a hex editor or use a Python script.
2.  Search for the ASCII string `freetyped.dll`.
3.  Replace it with `freetype.dll` followed by a null byte (`00`).
    *   Old: `freetyped.dll` (13 bytes)
    *   New: `freetype.dll\0` (13 bytes)
4.  Save the file.

**Note:** This patch allows the DLL to load using the available Release dependency.

### Verifying Support

Create a small script `verify_raqm.py`:

```python
from PIL import features, ImageFont
print(f"RAQM Support: {features.check('raqm')}")
```

Run it:
```powershell
python verify_raqm.py
```
Output should be `RAQM Support: True`.

## Running the Screenshot Generator

Once RAQM is enabled, you can run the screenshot generator:

```powershell
$env:SEEDSIGNER_SCREENSHOT_SIZE="320x240"
pytest tests/screenshot_generator/generator.py --locale en
```

Screenshots will be generated in `seedsigner-screenshots/en/`.
