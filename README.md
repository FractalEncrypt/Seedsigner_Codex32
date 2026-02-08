# Codex32 Terminal MVP

This folder contains a terminal-based MVP for validating Codex32 shares, recovering a secret `S` share from `k-of-n` shares, and converting the master seed into a 12-word BIP39 mnemonic (display-only).

## Current status (Feb 2, 2026)

✅ Terminal MVP complete for:

- Box-by-box entry (with backspace)
- Full-share paste mode (`--full`)
- Checksum + header validation
- `k-of-n` share recovery via interpolation
- Display recovered `S` share, seed hex, and BIP39 mnemonic
- ✅ Integrated into SeedSigner (Codex32 share entry, validation, and recovery UI)

⚠️ Not an ECW yet (no error correction). The tool does **not** provide substitution/erasure correction, so it does not attempt it. Error-correction should be implemented separately before advertising ECW behavior.

## Setup (Windows PowerShell)

From the repo root:

```powershell
python -m venv .\codex32_terminal\venv
.\codex32_terminal\venv\Scripts\python -m pip install -r .\codex32_terminal\requirements.txt
```

> Note: Use a semicolon between `Activate.ps1` and subsequent commands in PowerShell.

## Run

### Box-by-box entry (default)

```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1 ; python .\codex32_terminal\src\main.py
```

Features:

- Prefix `MS1` is pre-filled.
- Enter one character per box.
- Backspace: press Enter on empty input or type `<` to go back.
- Ctrl+C cancels entry.

### Full-share paste mode

```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1 ; python .\codex32_terminal\src\main.py --full
```

Paste full shares in sequence. For `k-of-n` shares, the tool will ask for additional shares until the threshold is met.

### Build a test share (checksum helper)

Use `build_share.py` to append a valid Codex32 checksum to a header + payload.

```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1 ; python .\codex32_terminal\src\build_share.py --header MS12MEMEC --payload YGHT84MU68S9FZX0PWQ7D890LZ
```

Interactive mode (no flags) guides you through k/identifier/payload and generates A/C/D/E/F shares automatically:

```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1 ; python .\codex32_terminal\src\build_share.py
```

Example output:

```
MS12MEMECYGHT84MU68S9FZX0PWQ7D890LZ{checksum}
```

Notes:
- `--header` should be `MS1 + k + ident(4) + share_idx` (6 chars after `MS1`).
- Payload must use the Codex32 charset (`qpzry9x8gf2tvdw0s3jn54khce6mua7l`).
- 128-bit shares expect a 26-character payload.
- Interactive mode supports k=2-5 and can auto-generate distinct payloads.

### SeedSigner entry tips

- Printable share cards: `C:\Users\FractalEncrypt\Documents\Windsurf\Seedsigner_Codex32\Printable Codex32 Share backup cards`
  - Fill a card and enter the share using the grid (one box per character).
- Text editor method: keep the share in a monospaced editor and use the **Col** value as the SeedSigner share box number while entering box-by-box.

## Test vectors

Use BIP-93 test vectors to validate recovery:

### Vector 2 (k=2, NAME)

- Share A: `MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDCAXRPP870HKKQRM`
- Share C: `MS12NAMECACDEFGHJKLMNPQRSTUVWXYZ023FTR2GDZMPY6PN`

Expected output:

- Recovered S-share: `MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW`
- Seed hex: `d1808e096b35b209ca12132b264662a5`
- BIP39 mnemonic: `spice afford liquid stool forest agent choose draw clinic cram obvious enough`

### Vector 3 (k=3, cash)

- Share a: `ms13casha320zyxwvutsrqpnmlkjhgfedca2a8d0zehn8a0t`
- Share c: `ms13cashcacdefghjklmnpqrstuvwxyz023949xq35my48dr`
- Share d: `ms13cashd0wsedstcdcts64cd7wvy4m90lm28w4ffupqs7rm`

Expected output:

- Recovered S-share: `ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln`
- Seed hex: `ffeeddccbbaa99887766554433221100`
- BIP39 mnemonic: `zoo ivory industry jar praise service talk skirt during october lounge absurd`

## Codebase overview

- `src/codex32_min.py`
  - Pure-Python Codex32 implementation (checksum, encode/decode, interpolation)
  - Implements the BIP-93 reference algorithms without native dependencies

- `src/model.py`
  - Input sanitation and validation (Codex32 checksum + header)
  - Seed extraction and BIP39 mnemonic conversion
  - Share recovery via interpolation (`Codex32String.interpolate_at`)

- `src/controller.py`
  - Orchestrates entry flow
  - Handles box-by-box mode and full-share mode
  - Determines whether input is `S` or split shares (`k-of-n`)
  - Recovers secret share and prints results

- `src/view.py`
  - Terminal UI helpers
  - Progress display, preview/confirm, prompts

- `tests/test_vectors.py`
  - Manual harness for BIP-93 vectors 2/3

### Implementation rationale

- **Validation** uses the vendored `codex32_min.Codex32String`, which enforces checksum + header correctness.
- **Recovery** uses `Codex32String.interpolate_at` to reconstruct the `S` share from `k` valid shares.
- **BIP39 mnemonic** is a display encoding of the 16-byte master seed (no PBKDF2). This mirrors BIP-93 guidance.

## Next steps (SeedSigner port)

1. **Integrate with SeedSigner UI flow**
   - Replace terminal prompts with on-device screens and key input.
   - Map box-by-box input into SeedSigner’s `Keypad` and display components.
   - COMPLETED

2. **Share-entry UX**
   - Pre-fill `MS1` for first share, `MS1 + k + ident` for subsequent shares.
   - Enforce header consistency across shares and prevent duplicate indices.
   - COMPLETED

3. **Error-correction (ECW work)**
   - Implement the BIP-93 requirement for up to 4 substitution/erasure corrections.
   - Add user-confirmed correction candidates; do not auto-apply.
   - This is waiting for formal documentation and implementation specs from the Codex32 cryptography team

4. **Backup S Share (optional)**
   - Add a new button in the "Backup Seed" screen so the user can backup the Codex32 S share master secret.

5. **Unit tests**
   - Port terminal tests to SeedSigner test harness or add unit tests around recovery logic.

---


