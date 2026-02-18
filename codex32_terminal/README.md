# Codex32 Terminal Tool (BIP32-native)

This folder contains a terminal-based Codex32 workflow for validating shares, recovering a secret `S` share from `k-of-n` shares, and exporting BIP32 artifacts (fingerprint, xpub, descriptors) without BIP39 conversion.

## Current status (Feb 16, 2026)

✅ Terminal MVP complete for:

- Box-by-box entry (with backspace)
- Full-share paste mode (`--full`)
- Checksum + header validation
- `k-of-n` share recovery via interpolation
- Display recovered `S` share, seed hex, and fingerprint
- Network selection (`--network mainnet|testnet4`)
- Single-sig descriptor export (Nested Segwit / Native Segwit / Taproot)
- Multisig cosigner export (Nested Segwit / Native Segwit)
- PSBT signing with loaded Codex32 seed (base64/hex/file input)
- ✅ Integrated into SeedSigner (Codex32 share entry, validation, and recovery UI)

⚠️ Not an ECW yet (no error correction). The tool does **not** provide substitution/erasure correction, so it does not attempt it. Error-correction should be implemented separately before advertising ECW behavior.

## Setup (Windows PowerShell)

From the repo root:

```powershell
python -m venv .\codex32_terminal\venv
.\codex32_terminal\venv\Scripts\python -m pip install -r .\codex32_terminal\requirements.txt
```

> Note: You can skip activation and run commands directly with `./venv/Scripts/python` as shown below.

After setup, the examples below assume your shell is in `codex32_terminal`:

```powershell
Set-Location .\codex32_terminal
```

## Run

### Box-by-box entry (default)

```powershell
.\venv\Scripts\python .\src\main.py
```

Features:

- Prefix `MS1` is pre-filled.
- Enter one character per box.
- Backspace: press Enter on empty input or type `<` to go back.
- Ctrl+C, `/cancel`, or `/exit` cancels entry.

### Full-share paste mode

```powershell
.\venv\Scripts\python .\src\main.py --full
```

Paste full shares in sequence. For `k-of-n` shares, the tool will ask for additional shares until the threshold is met.

### Select network profile

```powershell
.\venv\Scripts\python .\src\main.py --network testnet4
```

Supported values: `mainnet` (default) and `testnet4`.

### Descriptor export menu (after seed load)

After entering a valid share set, choose:

1. Export single-sig descriptor
2. Export multisig cosigner
3. Sign PSBT
4. Show loaded seed details
5. Load new key
6. Show loaded keys
7. Exit

Menu header also shows:

- Active key fingerprint
- Loaded key count

After `Show loaded keys`, choose which key becomes active using either:

- list index (for example `2`)
- fingerprint (for example `0e549ffd`)

Single-sig export prints:

- Fingerprint
- Account derivation path
- Account xpub/tpub
- Receive descriptor (`.../0/*`)
- Change descriptor (`.../1/*`)

Multisig cosigner export prints:

- BIP48 derivation path (`m/48'/coin_type'/0'/1'` nested or `.../2'` native)
- Account xpub/tpub and key origin (`[fingerprint/path]xpub`)
- Cosigner receive/change keys
- Optional descriptor templates if you provide policy `m/n` (example `2/3`)

### PSBT signing (Phase D)

From the session menu choose `3) Sign PSBT`, then provide one of:

- base64 PSBT string
- hex PSBT string
- local file path containing raw PSBT bytes, base64, or hex

Output:

- signatures added count
- total signatures count
- signed PSBT in base64 (printed)
- optional save to binary `.psbt` file (Sparrow-compatible)
- signed output preserves full PSBT metadata for sequential multisig signing

If a PSBT is missing required input UTXO fields (`witness_utxo`/`non_witness_utxo`), signing is rejected with a clear error message instead of a traceback.

Sparrow export compatibility:

- Supported directly: Base64 PSBT, Hex PSBT, or `.psbt` file path
- Not supported directly: UR-encoded or BBQr-encoded text blobs
- In Sparrow use: **File -> Save PSBT -> To Clipboard -> As Base64** (recommended), or **As Hex**
- Alternatively export/save a `.psbt` file and paste that file path into this tool

Example PSBT file workflow:

1. Save or copy an unsigned PSBT to a file (for example `unsigned.psbt`, raw bytes).

2. Launch the terminal app and load your seed.
3. Choose `3) Sign PSBT`.
4. Paste file path, for example:

```text
C:\Users\FractalEncrypt\Desktop\unsigned.psbt
```

5. Confirm save prompt and provide:

   - Output directory (for example `C:\Users\FractalEncrypt\Desktop`)
   - Output file name **without extension** (for example `signed_test1`)
   - The tool automatically appends `.psbt`

   Resulting path example:

```text
C:\Users\FractalEncrypt\Desktop\signed_test1.psbt
```

### Build a test share (checksum helper)

Use this script to create your own Codex32 keys for testing. You decide the number of shares, the 4-character identifier, and even the payload.

The payload is the "26 random characters" that are generated through the Codex32 dice debiasing process, but for testing this tool, you can just make up those 26 characters.

Use `build_share.py` to append a valid Codex32 checksum to a header + payload.

```powershell
.\venv\Scripts\python .\src\build_share.py --header MS12MEMEC --payload YGHT84MU68S9FZX0PWQ7D890LZ
```

Interactive mode (no flags) guides you through k/identifier/payload and generates A/C/D/E/F shares automatically:

```powershell
.\venv\Scripts\python .\src\build_share.py
```

This interactive mode is the fastest way to generate random test shares.

Example output:

```
MS12MEMECYGHT84MU68S9FZX0PWQ7D890LZ{checksum}
```

Notes:
- `--header` should be `MS1 + k + ident(4) + share_idx` (6 chars after `MS1`).
- Payload must use the Codex32 charset (`qpzry9x8gf2tvdw0s3jn54khce6mua7l`).
- 128-bit shares expect a 26-character payload.
- Interactive mode supports k=2-5 and can auto-generate distinct payloads.

### End-to-end test plan (Codex32 -> Sparrow -> PSBT -> signed tx)

Use this plan to verify the full testnet4 flow from share generation to signing and broadcast.

1. **Generate fresh test shares and recover an S-share**

   ```powershell
   .\venv\Scripts\python .\src\build_share.py
   ```

   - Choose `k` (example: `2` or `3`) and a 4-char identifier.
   - Save the generated split shares (A/C/D/E/F) and the printed `S Share (Master Codex32 key)`.

2. **Load share(s) in the terminal tool (full mode + testnet4)**

   ```powershell
   .\venv\Scripts\python .\src\main.py --full --network testnet4
   ```

   - For direct single-share flow: paste the recovered `S` share.
   - For threshold recovery flow: paste `k` split shares with matching header (`k + ident`) until recovery completes.

3. **Export a descriptor for Sparrow import**

   - In the session menu choose `1) Export single-sig descriptor`.
   - Choose script type (recommended test path: `2) Native Segwit (BIP84)`).
   - Copy the printed receive descriptor (`.../0/*`) and change descriptor (`.../1/*`).

4. **Import into Sparrow (watch-only testnet wallet)**

   - Create/import a wallet in Sparrow from the exported descriptor.
   - Ensure Sparrow is set to **testnet4**.
   - Confirm the first receive address appears.

5. **Fund a receive address from a testnet4 faucet**

   - Copy one receive address from Sparrow.
   - Send testnet4 coins from a faucet.
   - Wait for the UTXO to appear (and confirm, if your policy requires confirmations before spend).

6. **Create an unsigned PSBT in Sparrow**

   - Build a small spend transaction in Sparrow.
   - Export/copy the unsigned PSBT as text (base64 is easiest for terminal paste).

7. **Sign PSBT in Codex32 terminal**

   - In the session menu choose `3) Sign PSBT`.
   - Paste the PSBT base64 from Sparrow.
   - Confirm the output shows `Signatures added` > `0`.
   - Copy the printed `Signed PSBT (base64)` (or save it as binary `.psbt` by entering output directory + file name when prompted).

8. **Finalize and broadcast in Sparrow**

   - Import/paste the signed PSBT back into Sparrow.
   - Finalize transaction and broadcast to testnet4.
   - Verify txid appears and confirms.

Optional regression checks:
- Repeat with script type `1) Nested Segwit` and `3) Taproot`.
- Repeat with split-share recovery instead of direct `S` share entry.
- Repeat by signing via file-mode input path instead of direct PSBT paste.
- For multisig, repeat signer handoff: cosigner #1 signs and exports, cosigner #2 signs the resulting `.psbt`.

### Multisig session behavior (SeedSigner-style key switching)

- The terminal now supports multiple loaded keys in one session.
- Load each cosigner key with `5) Load new key`.
- Use `6) Show loaded keys`, then choose signer by index or fingerprint.
- PSBT signing always uses the currently active key fingerprint shown in the menu.

### Canceling share entry

- During share entry (box mode or full mode), type `/cancel` (or press Ctrl+C) to return without loading a key.
- This is useful if `5) Load new key` was selected by mistake.

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

### Vector 3 (k=3, cash)

- Share a: `ms13casha320zyxwvutsrqpnmlkjhgfedca2a8d0zehn8a0t`
- Share c: `ms13cashcacdefghjklmnpqrstuvwxyz023949xq35my48dr`
- Share d: `ms13cashd0wsedstcdcts64cd7wvy4m90lm28w4ffupqs7rm`

Expected output:

- Recovered S-share: `ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln`
- Seed hex: `ffeeddccbbaa99887766554433221100`

## Codebase overview

- `src/codex32_min.py`
  - Pure-Python Codex32 implementation (checksum, encode/decode, interpolation)
  - Implements the BIP-93 reference algorithms without native dependencies

- `src/model.py`
  - Input sanitation and validation (Codex32 checksum + header)
  - Seed extraction and BIP32 export helpers (fingerprint, derivation paths, descriptors)
  - PSBT parsing and signing helpers
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
- **No BIP39 output** in this terminal tool. Codex32 shares are treated as direct BIP32 seed material.

## Next steps (SeedSigner port)

1. **Integrate with SeedSigner UI flow**
   - Replace terminal prompts with on-device screens and key input.
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
   - Add dedicated terminal unit tests for PSBT parse/signing helpers.
   - COMPLETED (`tests/test_psbt_signing.py`)

## Test commands

Run both terminal test modules:

```powershell
.\venv\Scripts\python .\tests\test_vectors.py
.\venv\Scripts\python -m unittest .\tests\test_psbt_signing.py
```

---