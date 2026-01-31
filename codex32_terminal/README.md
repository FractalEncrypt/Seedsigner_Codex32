# Codex32 Terminal MVP

This folder contains a terminal-based MVP for validating Codex32 shares, recovering a secret `S` share from `k-of-n` shares, and converting the master seed into a BIP39 mnemonic (display-only).

## Supported Seed Sizes

| Seed Size | Codex32 Length | BIP39 Output |
|-----------|----------------|--------------|
| 128-bit   | 48 characters  | 12 words     |
| 256-bit   | 74 characters  | 24 words     |

## Current status (Jan 31, 2026)

✅ Terminal MVP complete for:

- Box-by-box entry (with backspace)
- Full-share paste mode (`--full`)
- Checksum + header validation
- `k-of-n` share recovery via interpolation
- Display recovered `S` share, seed hex, and BIP39 mnemonic
- **128-bit and 256-bit seed support** (auto-detected)

⚠️ Not an ECW yet (no error correction). The codex32 Python library does **not** provide substitution/erasure correction, so this tool does not attempt it. Error-correction should be implemented separately before advertising ECW behavior.

## Setup

### macOS / Linux

```bash
cd codex32_terminal
python3 -m venv venv
source venv/bin/activate
pip install codex32 embit
```

### Windows PowerShell

From the repo root:

```powershell
python -m venv .\codex32_terminal\venv
.\codex32_terminal\venv\Scripts\Activate.ps1 ; pip install codex32 embit
```

## Run

### Box-by-box entry (default)

**macOS / Linux:**
```bash
source venv/bin/activate
python src/main.py
```

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1 ; python src\main.py
```

Features:

- Prompts for seed size (128-bit or 256-bit) at start
- Prefix `MS1` is pre-filled
- Enter one character per box
- Backspace: press Enter on empty input or type `<` to go back
- Ctrl+C cancels entry

### Full-share paste mode

**macOS / Linux:**
```bash
source venv/bin/activate
python src/main.py --full
```

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1 ; python src\main.py --full
```

Paste full shares in sequence. Seed size is auto-detected from string length (48 or 74 chars). For `k-of-n` shares, the tool will ask for additional shares until the threshold is met.

## Run Tests

**macOS / Linux:**
```bash
source venv/bin/activate
python tests/test_vectors.py
python tests/test_256bit.py
```

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
python tests\test_vectors.py
python tests\test_256bit.py
```

### Expected test output

```
vector2: seed OK -> spice afford liquid stool forest agent choose draw clinic cram obvious enough
vector3: seed OK -> zoo ivory industry jar praise service talk skirt during october lounge absurd
test_valid_lengths_constant: PASS
test_256bit_parse: PASS
test_256bit_validate_s_share: PASS
test_256bit_seed_extraction: PASS
test_256bit_to_mnemonic: PASS (24 words)
  Mnemonic: zoo ivory industry jar praise service talk skirt during october lounge acid year humble cream inspire office dry sunset pride drip much dune arm
test_128bit_still_works: PASS (12 words)
test_auto_detect_length: PASS
test_invalid_length_rejected: PASS
test_seed_bytes_to_mnemonic_both_sizes: PASS

All 256-bit tests passed!
```

## Test vectors

Use BIP-93 test vectors to validate recovery:

### Vector 2 (k=2, NAME)

- Share A: `MS12NAMEA320ZYXWVUTSRQPNMLKJHGFEDCAXRPP870HKKQRM`
- Share C: `MS12NAMECACDEFGHJKLMNPQRSTUVWXYZ023FTR2GDZMPY6PN`

Expected output:

- Recovered S-share: `MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW`
- Seed hex: `d1808e096b35b209ca12132b264662a5`
- BIP39 mnemonic: `spice afford liquid stool forest agent choose draw clinic cram obvious enough`

### Vector 3 (k=3, cash, 128-bit)

- Share a: `ms13casha320zyxwvutsrqpnmlkjhgfedca2a8d0zehn8a0t`
- Share c: `ms13cashcacdefghjklmnpqrstuvwxyz023949xq35my48dr`
- Share d: `ms13cashd0wsedstcdcts64cd7wvy4m90lm28w4ffupqs7rm`

Expected output:

- Recovered S-share: `ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln`
- Seed hex: `ffeeddccbbaa99887766554433221100`
- BIP39 mnemonic (12 words): `zoo ivory industry jar praise service talk skirt during october lounge absurd`

### Vector 4 (256-bit seed)

- S-share: `ms10leetsllhdmn9m42vcsamx24zrxgs3qrl7ahwvhw4fnzrhve25gvezzyqqtum9pgv99ycma`

Expected output:

- Seed hex: `ffeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100`
- BIP39 mnemonic (24 words): `zoo ivory industry jar praise service talk skirt during october lounge acid year humble cream inspire office dry sunset pride drip much dune arm`

## Codebase overview

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
  - Manual harness for BIP-93 vectors 2/3 (128-bit)

- `tests/test_256bit.py`
  - Tests for 256-bit seed support (BIP-93 vector 4)
  - Verifies both 128-bit and 256-bit paths work correctly

### Implementation rationale

- **Validation** uses `codex32.Codex32String`, which enforces checksum + header correctness.
- **Recovery** uses `Codex32String.interpolate_at` to reconstruct the `S` share from `k` valid shares.
- **BIP39 mnemonic** is a display encoding of the master seed (no PBKDF2). 128-bit seeds produce 12 words, 256-bit seeds produce 24 words. This mirrors BIP-93 guidance.

## Next steps (SeedSigner port)

1. **Integrate with SeedSigner UI flow**
   - Replace terminal prompts with on-device screens and key input.
   - Map box-by-box input into SeedSigner’s `Keypad` and display components.

2. **Share-entry UX**
   - Pre-fill `MS1` for first share, `MS1 + k + ident` for subsequent shares.
   - Enforce header consistency across shares and prevent duplicate indices.

3. **Error-correction (ECW work)**
   - Implement the BIP-93 requirement for up to 4 substitution/erasure corrections.
   - Add user-confirmed correction candidates; do not auto-apply.

4. **State persistence (optional)**
   - Store partial share entry progress between sessions.

5. **Unit tests**
   - Port terminal tests to SeedSigner test harness or add unit tests around recovery logic.

---

If you want to continue the port, the next concrete step is to stub SeedSigner screens for share entry and reuse `model.py` logic for validation + recovery.
