# Codex32 Terminal MVP

This folder contains a terminal-based MVP for validating Codex32 shares, recovering a secret `S` share from `k-of-n` shares, and converting the master seed into a 12-word BIP39 mnemonic (display-only).

## Current status (Jan 31, 2026)

✅ Terminal MVP complete for:

- Box-by-box entry (with backspace)
- Full-share paste mode (`--full`)
- Checksum + header validation
- `k-of-n` share recovery via interpolation
- Display recovered `S` share, seed hex, and BIP39 mnemonic

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
pip freeze > .\codex32_terminal\requirements.txt
```

> Note: Use a semicolon between `Activate.ps1` and subsequent commands in PowerShell.

## Run

### Box-by-box entry (default)

**macOS / Linux:**
```bash
source venv/bin/activate
python src/main.py
```

**Windows PowerShell:**
```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1 ; python .\codex32_terminal\src\main.py
```

Features:

- Prefix `MS1` is pre-filled.
- Enter one character per box.
- Backspace: press Enter on empty input or type `<` to go back.
- Ctrl+C cancels entry.

### Full-share paste mode

**macOS / Linux:**
```bash
source venv/bin/activate
python src/main.py --full
```

**Windows PowerShell:**
```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1 ; python .\codex32_terminal\src\main.py --full
```

Paste full shares in sequence. For `k-of-n` shares, the tool will ask for additional shares until the threshold is met.

## Run Tests

Run all test files:

**macOS / Linux:**
```bash
cd codex32_terminal
source venv/bin/activate
python tests/test_vectors.py
python tests/test_share_recovery.py
python tests/test_validation.py
python tests/test_invalid_vectors.py
```

**Windows PowerShell:**
```powershell
.\codex32_terminal\venv\Scripts\Activate.ps1
python tests/test_vectors.py
python tests/test_share_recovery.py
python tests/test_validation.py
python tests/test_invalid_vectors.py
```

### Expected output

When all tests pass, you should see:

```
vector2: seed OK -> spice afford liquid stool forest agent choose draw clinic cram obvious enough
vector3: seed OK -> zoo ivory industry jar praise service talk skirt during october lounge absurd
test_vector2_share_recovery: PASS
test_vector3_share_recovery: PASS
test_vector3_different_share_combination: PASS

All share recovery tests passed!
test_invalid_checksum_rejected: PASS
test_wrong_length_rejected: PASS
test_empty_input_rejected: PASS
test_non_s_share_rejected_for_s_share_validation: PASS
test_sanitize_input: PASS
test_valid_share_accepted: PASS
test_case_insensitive_but_consistent: PASS

All validation tests passed!
test_invalid_checksum_vectors: PASS (3 vectors rejected)
test_bip93_invalid_vectors: PASS (4 vectors rejected)
test_corrupted_single_char: PASS (7 corruptions detected)

All invalid vector tests passed!
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

### Vector 3 (k=3, cash)

- Share a: `ms13casha320zyxwvutsrqpnmlkjhgfedca2a8d0zehn8a0t`
- Share c: `ms13cashcacdefghjklmnpqrstuvwxyz023949xq35my48dr`
- Share d: `ms13cashd0wsedstcdcts64cd7wvy4m90lm28w4ffupqs7rm`

Expected output:

- Recovered S-share: `ms13cashsllhdmn9m42vcsamx24zrxgs3qqjzqud4m0d6nln`
- Seed hex: `ffeeddccbbaa99887766554433221100`
- BIP39 mnemonic: `zoo ivory industry jar praise service talk skirt during october lounge absurd`

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
  - Manual harness for BIP-93 vectors 2/3

- `tests/test_share_recovery.py`
  - Tests 2-of-n and 3-of-n share recovery with BIP-93 vectors

- `tests/test_validation.py`
  - Tests input validation (checksum, length, empty input, sanitization)

- `tests/test_invalid_vectors.py`
  - Tests rejection of BIP-93 invalid test vectors

### Implementation rationale

- **Validation** uses `codex32.Codex32String`, which enforces checksum + header correctness.
- **Recovery** uses `Codex32String.interpolate_at` to reconstruct the `S` share from `k` valid shares.
- **BIP39 mnemonic** is a display encoding of the 16-byte master seed (no PBKDF2). This mirrors BIP-93 guidance.

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
