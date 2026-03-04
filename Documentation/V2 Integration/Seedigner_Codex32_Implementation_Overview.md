# SeedSigner & Codex32: Implementation Overview

## 1) Introduction

As Bitcoin self-custody evolves, the standard for what it means to be a sovereign user continues to evolve. For years, the gold standard has been hardware wallets using BIP39 seed phrases. However, two powerful tools have emerged that challenge this paradigm by removing trust in electronics and persistent memory: **SeedSigner** and **Codex32**.

This document explains what these tools are, why bringing them together creates a uniquely powerful self-custody model, and exactly how we implemented this integration.

### What is SeedSigner?
SeedSigner is a DIY, air-gapped, and **stateless** Bitcoin signing device. Built from off-the-shelf, general-purpose components (like a Raspberry Pi Zero), it is designed to be assembled by the user, removing supply chain risks associated with specialized hardware wallets. Because it is stateless, it forgets everything the moment it is turned off. It holds no memory of your keys, meaning a physical theft of the device compromises nothing. It is a completely airgapped bitcoin swiss army knife that never connects to wifi or bluetooth. You seeds never touch an internet connected device, and never are stored in a persistent memory.

### What is Codex32?
Codex32 (BIP93) is a cryptographic standard for generating, verifying, and splitting Bitcoin master seeds using only **pencil, paper, and dice**. It uses a human-readable format and incorporates a robust checksum (like Bech32 Bitcoin addresses). More importantly, it uses a form of Shamir's Secret Sharing (SSSS) designed to be calculated by hand, allowing users to create and split a master secret into multiple shares without ever typing the secret into a computer.

---

## 2) The Philosophy: The "Why"

True self-custody requires removing blind trust in hardware and software. 

Almost without exception, every single person who's created a bitcoin seed has trusted an electronic device to do it. When you use a traditional hardware wallet to generate a seed phrase, you are trusting the device's random number generator (RNG) and its software. If the device is compromised, your Bitcoin is at risk. 

Even those bitcoiners rolling dice, using seed picker cards, or other manual methods always enter their seed entropy into an electonic device to perform the BIP39 math to create the "last word" (the 12th or 24th words in most standard implementations). This means that even if you've manually created most of the key, it can't be finalized until you run it thorough an electronic device. Don't get me wrong, these are my people, I'm just calling it like it is.

By combining Codex32 and SeedSigner, we establish a **Trustless Analog-to-Digital Bridge**:

1. **Analog Generation:** You generate your Codex32 master secret and split shares entirely offline, using dice and paper worksheets. You calculate the checksums yourself. No silicon, no electricity, no potential for malware.
2. **Stateless Digital Signing:** When you need to receive or spend Bitcoin, you temporarily bring your analog key into the digital realm by entering it into the SeedSigner. You interact with an internet connected watch-only wallet over airgap. The seed never touches an internet connected device. Once you are done, as soon as you pull the power cord, the seed is completely wiped from the Seedsigner. 

This integration means you can rely on the unhackable nature of paper and math to create  your Bitcoin seed, while retaining the convenience of an electronic signer when you actually need to move funds.

---

## 3) The Mechanics: The "How"

Codex32 relies on finite field math (specifically Galois Field 32) that has been simplified into lookup tables so a human can calculate it by hand. 

### Anatomy of a Codex32 Share
A standard Codex32 share we implemented is a 48-character string that looks something like this:
`MS12L0VEAARWENFLUFFYTAFLCATQTTGGERGGM0C6A8FRJE57`

Even though it looks like random letters, it is highly structured:
- **`MS`** (Human-readable part): Identifies this as a Master Seed string.
- **`1`**: A separator.
- **`2`** (Threshold `k`): The number of shares needed to recover the secret (in this case, 2). If this is `0`, the string is a single un-split master secret.
- **`L0VE`** (Identifier): A self-chosen 4-character label that groups related shares together.
- **`A`** (Index): Identifies which specific share this is (e.g., Share A, Share C, or `S` for the Master Secret).
- **The Payload**: The actual secret data.
- **The Checksum**: The final characters, mathematically derived from the rest of the string to detect errors.

### Split-Sharing (k-of-N)
If you want to secure your Bitcoin such that losing one backup doesn't cause complete loss of funds, Codex32 lets you split the secret. For example, a 2-of-3 setup creates Share A, Share C, and Share D. Any two of those shares can be mathematically combined to reconstruct the Master Secret (`S` share).

### 3.1 Conceptual Walkthrough: How the Codex32 Flow Works in Practice

In our implementation, the process is intentionally **paper-first** and **air-gapped**:

1. **Create the seed by hand (offline)**
   - The user starts with paper, pencil, and dice.
   - They manually create Codex32 share data (most often as split shares, e.g., k-of-n).

2. **Verify and recover on SeedSigner**
   - The user enters or scans their manually created shares into SeedSigner.
   - SeedSigner validates each share (format/checksum), then reconstructs/derives the master secret (`S` share) once enough valid shares are present.

3. **Load seed + create durable backups**
   - Once loaded, the user can back up:
     - each split share, and/or
     - the derived `S` share.
   - Backups can be transcribed as Codex32QR by hand first, then verified.

4. **Export watch-only wallets**
   - The user exports watch-only wallet data (single-sig or multisig) to coordinator software (e.g., Sparrow and compatible mobile wallets such as SeedKeeper, Nunchuk, and BlueWallet).

5. **Receive and spend with separation of duties**
   - After watch-only setup, the coordinator can generate receive addresses and track balances **without loading private seed material**.
   - To spend, the user loads the seed into SeedSigner (manual entry or QR), signs the transaction offline, then broadcasts from the watch-only coordinator.

6. **Finalize long-term storage**
   - After backup verification, the user can transfer final backups to metal for long-term, resilient storage.

---

## 4) The Implementation: What We Built

Our implementation (completed in SeedSigner) bridges the Codex32 analog world with SeedSigner's digital capabilities. Here is exactly what we built and the user flow it enables.

### 4.1. Strict Trustless Validation
When a user manually enters a Codex32 share into the SeedSigner, the device validates the structure, length, and checksum. 
- **No Auto-correction:** To preserve the trustless nature of Codex32, SeedSigner will *not* guess or auto-correct a bad checksum. If the user's manual math on their worksheet was wrong, SeedSigner forces them to find and fix the error on paper. 

### 4.2. Codex32QR Support
Typing 48 characters with a joystick can be tedious. We engineered a specific QR code profile (`Codex32QR/v1-48`) which encodes the Codex32 text into a dense, scannable 29x29 format. 
- Users can scan these QRs directly using the SeedSigner's camera.
- Because it's plain text, a user can also scan a Codex32QR with a generic smartphone camera to verify its contents, promoting radical transparency.

### 4.3. Multi-Share Collection Mode
If a user inputs a split share (e.g., Share A of a 2-of-3 set), the SeedSigner intelligently enters a "Collection Mode." 
- It notes the share identifier (`L0VE`) and the threshold (`k=2`).
- It prompts the user to enter or scan the next required share.
- If a user tries to scan a share from a *different* set, the device catches the mismatch and alerts the user.
- Once the threshold is met (e.g., Share A and Share C are entered), SeedSigner performs the Codex32 interpolation math to automatically recover the Master Secret (`S` share).

### 4.4. Seed Loading and Export
Once the `S` share is successfully recovered (or directly entered), SeedSigner loads it into active memory as the active signing seed. From here, the user can:
- Sign Partially Signed Bitcoin Transactions (PSBTs) normally.
- Generate and verify receive addresses.
- **Export Backups:** The user can navigate to the Backup menu and export the `S` share, or any of the entered split shares, visually on the screen or as a dynamically generated Codex32QR code to be transcribed onto paper or etched into metal.

### 4.5. Codebase overview (SeedSigner Changes)

The Codex32 integration was implemented as a focused extension of SeedSigner’s existing seed, QR, and PSBT pipelines.  
Rather than introducing a parallel architecture, we added Codex32-specific logic at key model and view boundaries while preserving existing behavior for BIP39/SeedQR users.

#### Core Domain & Validation Layer

- **[src/seedsigner/models/codex32.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/codex32.py:0:0-0:0)**
  - Defines Codex32 parsing/normalization and strict input validation.
  - Locks the Codex32QR profile contract (canonical `MS1` prefix, fixed-length share payload, and QR profile constants).
  - Implements `Codex32ShareCollection`, which manages split-share collection, conflict handling, recoverability checks, and export metadata generation.

- **[src/seedsigner/models/seed.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py:0:0-0:0)**
  - Adds [Codex32Seed](cci:2://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed.py:179:0-232:48) as a seed type backed by the recovered 16-byte entropy.
  - Preserves Codex32-specific metadata needed for backup/export UX (`master_share`, export-share map, source map).
  - Explicitly keeps Codex32 seeds passphrase-free to match the Codex32 model.

- **[src/seedsigner/models/seed_storage.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/seed_storage.py:0:0-0:0)**
  - Updates duplicate-seed handling so reloading an equivalent Codex32 seed can enrich existing stored metadata instead of discarding it.

#### QR Decode/Encode Integration

- **`src/seedsigner/models/qr_type.py`**
  - Introduces a dedicated Codex32 QR type used consistently by decoder and routing logic.

- **[src/seedsigner/models/decode_qr.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/decode_qr.py:0:0-0:0)**
  - Adds Codex32 detection and canonical decode output through a dedicated Codex32 decoder path.
  - Enforces fail-closed behavior for invalid Codex32-like payloads (prevents accidental fallback into unrelated QR types such as bitcoin address parsing).

- **[src/seedsigner/models/encode_qr.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/encode_qr.py:0:0-0:0)**
  - Adds `Codex32QrEncoder` to produce deterministic, canonical Codex32 share payloads for display/export.

#### UX and Flow Wiring (Views)

- **[src/seedsigner/views/scan_views.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/views/scan_views.py:0:0-0:0)**
  - Extends scan routing so Codex32 shares can enter either direct success flow (`S` share) or multi-share collection flow (non-`S` shares).
  - Adds a dedicated collection scan view for iterative share intake.

- **[src/seedsigner/views/seed_views.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/views/seed_views.py:0:0-0:0)**
  - Extends load-seed menu with Codex32 entry/scan options.
  - Implements Codex32 manual entry flow, share conflict confirmation, and collection progression.
  - Specializes backup UX for Codex32 with:
    - view master secret (when available),
    - export as Codex32QR,
    - share-selection UI for multi-share seeds,
    - source-aware labeling (e.g., derived `S` share),
    - unavailable-state routing when metadata is insufficient.
  - Integrates Codex32 into transcribe-and-confirm scan verification flow with canonical string comparison.

#### PSBT Robustness (Supporting Work in Same Branch)

- **[src/seedsigner/models/psbt_parser.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/models/psbt_parser.py:0:0-0:0)**
  - Adds explicit missing-UTXO detection and dedicated parser error signaling.

- **[src/seedsigner/views/psbt_views.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/src/seedsigner/views/psbt_views.py:0:0-0:0)**
  - Routes missing-UTXO parse failures to user-facing warning flow.
  - Finalize/sign path preserves PSBT metadata by avoiding destructive trimming in the signed export flow.

#### Regression & Integration Test Coverage

- **[tests/test_decodepsbtqr.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/tests/test_decodepsbtqr.py:0:0-0:0)**: Codex32 decode canonicalization, invalid checksum handling, and precedence regressions.
- **[tests/test_scan_views.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/tests/test_scan_views.py:0:0-0:0)**: non-`S` scan routing into collection-mode entry.
- **[tests/test_flows_seed.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/tests/test_flows_seed.py:0:0-0:0)**: end-to-end collection, conflict replacement, backup/export menus, share selection, and confirm-scan roundtrip.
- **[tests/test_seedqr.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/tests/test_seedqr.py:0:0-0:0)**: Codex32 QR rendering profile expectations.
- **[tests/test_psbt_parser.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/tests/test_psbt_parser.py:0:0-0:0) + [tests/test_flows_psbt.py](cci:7://file:///c:/Users/FractalEncrypt/Documents/Windsurf/SeedSigner/tests/test_flows_psbt.py:0:0-0:0)**: missing-UTXO detection and warning flow coverage.

### 4.6. Scope Boundaries: Practical Subset of BIP93

Our SeedSigner implementation intentionally does **not** implement the full Codex32 space described in BIP93.

#### What we support today
- **48-character Codex32 strings only** (the fixed-length profile used by our Codex32QR workflow).
- **Up to 5 split shares** in collection/export workflows.

#### Why this scope is intentional
- The official Codex32 workbook worksheets in common circulation are focused on constructing and verifying the **48-character format**.
- Existing Codex32 guidance recommends avoiding unnecessarily large split-share sets, and in practice the strongest guidance centers around keeping share counts modest (with 5 as a practical upper bound).

#### Future expansion path
This is a deliberate product boundary, not a protocol limitation.  
If we see meaningful real-world demand for larger share sets, higher thresholds, or longer Codex32 string formats, we can extend support in a future iteration.

---

This structure keeps Codex32 support modular and testable while preserving SeedSigner’s existing seed and signing UX for non-Codex32 users.

---

## 5) Conclusion

The SeedSigner + Codex32 integration represents a massive leap forward for analog self-custody. By strictly adhering to the mathematical constraints of Codex32 while leveraging the stateless, optical air-gap of SeedSigner, we have created a workflow where a user can generate a seed phrase entirely offline by hand, perfectly verify its math without a computer, and securely use it to sign transactions without ever exposing the master key to a persistent, internet-connected device.

This implementation brings the "don't trust, verify" ethos to the very generation and storage of the private key itself.

---

## 6) Acknowledgements
A deep thanks for extremely valuable guidance and insights from Anrew Polestra, Dr. Pearlwort Snead, Ben Westgate, and "Bitcoin Butlers" that helped bring this project from thought into reality.