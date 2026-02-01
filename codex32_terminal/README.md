# Codex32 Terminal MVP

This folder contains a terminal-based MVP for validating Codex32 shares, recovering a secret `S` share from `k-of-n` shares, converting the master seed into a BIP39 mnemonic (display-only), and **correcting up to 4 character errors**.

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
- **Error correction (ECW)** - up to 4 substitution errors, user-confirmed

## Error Correction (ECW)

This tool implements BIP-93 error correction capabilities:

| Error Type | Max Correctable |
|------------|-----------------|
| Substitution errors | 4 |
| Erasure errors (known positions) | 8 |

### How It Works

When checksum validation fails, the tool offers to search for corrections:

1. User enters a codex32 string
2. If checksum fails, tool prompts: "Would you like to search for corrections?"
3. Tool searches for valid corrections (1-2 errors by default for speed)
4. Found candidates are displayed with their changes
5. **User must confirm** before any correction is applied (per BIP-93)

### Example Correction Flow

```
Error: Checksum verification failed.

Checksum validation failed.
Would you like to search for corrections? [y/N]: y
Searching for corrections (up to 2 errors)...

Found 1 potential correction(s):

[1] ms12names6xqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evw
    Changes: pos 10: 'h'->'x'

Proposed correction:
  Original:  ms12names6hqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evw
  Corrected: ms12names6xqguzttxkeqnjsjzv4jv3nz5k3kwgsphuh6evw
  Changes (1):
    Position 10: 'h' → 'x'

Accept this correction? [y/N]: y

Codex32 S-share accepted (128-bit seed).
Seed (hex): d1808e096b35b209ca12132b264662a5
BIP39 mnemonic (12 words): spice afford liquid stool forest agent choose draw clinic cram obvious enough
```

### Performance Note

Error correction search space grows exponentially:
- 1 error (48-char string): ~1,400 candidates (instant)
- 2 errors (48-char string): ~950,000 candidates (~1-2 seconds)
- 3-4 errors: May take longer; use sparingly

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
- **Error correction offered on checksum failure**

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
python tests/test_gf32.py
python tests/test_correction.py
```

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
python tests\test_vectors.py
python tests\test_256bit.py
python tests\test_gf32.py
python tests\test_correction.py
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
test_table_consistency: PASS
test_exp_table_generation: PASS
test_addition_is_xor: PASS
test_multiplication_commutativity: PASS
test_multiplication_associativity: PASS
test_distributivity: PASS
test_multiplicative_identity: PASS
test_additive_identity: PASS
test_multiplicative_zero: PASS
test_multiplicative_inverse: PASS
test_division: PASS
test_division_by_zero: PASS
test_power: PASS
test_negative_power: PASS
test_char_to_int: PASS
test_int_to_char: PASS
test_roundtrip_char_int: PASS
test_verify_tables_function: PASS

All GF(32) tests passed!
test_already_valid: PASS
test_single_error_correction: PASS
test_single_error_various_positions: PASS
test_two_error_correction: PASS
test_256bit_error_correction: PASS
test_erasure_correction: PASS
test_stop_on_first: PASS
test_no_correction_found: PASS (no crash)
test_empty_input: PASS
test_format_correction_diff: PASS
test_estimate_search_space: PASS
test_case_insensitivity: PASS
test_share_correction: PASS

All error correction tests passed!
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

### Error Correction Test

To test error correction, introduce a single character error:

- Corrupted: `MS12NAMES6HQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW` (position 10: X→H)
- Expected correction: Position 10: 'h' → 'x'
- Corrected: `MS12NAMES6XQGUZTTXKEQNJSJZV4JV3NZ5K3KWGSPHUH6EVW`

## Codebase overview

### Core modules

- `src/model.py`
  - Input sanitation and validation (Codex32 checksum + header)
  - Seed extraction and BIP39 mnemonic conversion
  - Share recovery via interpolation (`Codex32String.interpolate_at`)
  - Error correction interface (`try_correct_codex32_errors`)

- `src/controller.py`
  - Orchestrates entry flow
  - Handles box-by-box mode and full-share mode
  - Determines whether input is `S` or split shares (`k-of-n`)
  - Recovers secret share and prints results
  - Integrates error correction on validation failure

- `src/view.py`
  - Terminal UI helpers
  - Progress display, preview/confirm, prompts
  - Error correction candidate display and confirmation

### Error correction modules

- `src/gf32.py`
  - GF(32) Galois Field arithmetic for BCH codes
  - Log/exp tables, add/mul/div/inv/pow operations
  - Character ↔ integer conversion

- `src/error_correction.py`
  - Validated brute-force correction search
  - Generates candidates and validates with codex32 library
  - Supports substitution and erasure correction

- `src/bch_decoder.py`
  - BCH decoding algorithms (syndrome, Berlekamp-Massey, Chien, Forney)
  - Reference implementation for future optimization

### Test files

- `tests/test_vectors.py` - BIP-93 vectors 2/3 (128-bit)
- `tests/test_256bit.py` - 256-bit seed support (vector 4)
- `tests/test_gf32.py` - GF(32) field arithmetic (18 tests)
- `tests/test_correction.py` - Error correction end-to-end (13 tests)
- `tests/test_bch.py` - BCH decoder unit tests

### Implementation rationale

- **Validation** uses `codex32.Codex32String`, which enforces checksum + header correctness.
- **Recovery** uses `Codex32String.interpolate_at` to reconstruct the `S` share from `k` valid shares.
- **BIP39 mnemonic** is a display encoding of the master seed (no PBKDF2). 128-bit seeds produce 12 words, 256-bit seeds produce 24 words. This mirrors BIP-93 guidance.
- **Error correction** uses validated brute-force search for safety. Each candidate is verified using the codex32 library's checksum before being offered to the user.

## Next steps (SeedSigner port)

1. **Integrate with SeedSigner UI flow**
   - Replace terminal prompts with on-device screens and key input.
   - Map box-by-box input into SeedSigner's `Keypad` and display components.

2. **Share-entry UX**
   - Pre-fill `MS1` for first share, `MS1 + k + ident` for subsequent shares.
   - Enforce header consistency across shares and prevent duplicate indices.

3. **Error correction UX optimization**
   - On SeedSigner, use button navigation for correction candidate selection.
   - Consider visual diff highlighting for proposed changes.

4. **State persistence (optional)**
   - Store partial share entry progress between sessions.

5. **Unit tests**
   - Port terminal tests to SeedSigner test harness or add unit tests around recovery logic.

---

If you want to continue the port, the next concrete step is to stub SeedSigner screens for share entry and reuse `model.py` logic for validation + recovery + error correction.
