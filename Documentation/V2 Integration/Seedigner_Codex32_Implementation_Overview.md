# SeedSigner & Codex32: Implementation Overview

## 1) Introduction

As Bitcoin self-custody evolves, the standard for what it means to be a "sovereign user" continues to rise. For years, the gold standard has been hardware wallets using BIP39 seed phrases. However, two powerful tools have emerged that challenge this paradigm by removing trust in electronics and persistent memory: **SeedSigner** and **Codex32**.

This document explains what these tools are, why bringing them together creates a uniquely powerful self-custody model, and exactly how we implemented this integration.

### What is SeedSigner?
SeedSigner is a DIY, air-gapped, and **stateless** Bitcoin signing device. Built from off-the-shelf, general-purpose components (like a Raspberry Pi Zero), it is designed to be assembled by the user, removing supply chain risks associated with specialized hardware wallets. Because it is stateless, it forgets everything the moment it is turned off. It holds no memory of your keys, meaning a physical theft of the device compromises nothing.

### What is Codex32?
Codex32 (BIP93) is a cryptographic standard for generating, verifying, and splitting Bitcoin master seeds using only **pencil, paper, and dice**. It uses a human-readable format and incorporates a robust checksum (like Bech32 Bitcoin addresses). More importantly, it uses a form of Shamir's Secret Sharing (SSSS) designed to be calculated by hand, allowing users to split a master secret into multiple shares without ever typing the secret into a computer.

---

## 2) The Philosophy: The "Why"

True self-custody requires removing blind trust in hardware and software. 

When you use a traditional hardware wallet to generate a seed phrase, you are trusting the device's random number generator (RNG) and its software. If the device is compromised, your Bitcoin is at risk. 

By combining Codex32 and SeedSigner, we establish a **Trustless Analog-to-Digital Bridge**:

1. **Analog Generation:** You generate your Codex32 master secret and split shares entirely offline, using dice and paper worksheets. You calculate the checksums yourself. No silicon, no electricity, no potential for malware.
2. **Stateless Digital Signing:** When you need to spend Bitcoin, you temporarily bring your analog key into the digital realm by entering it into the SeedSigner. The SeedSigner uses the key to sign your transaction (PSBT), and as soon as you pull the power cord, the device suffers total amnesia. 

This integration means you can rely on the unhackable nature of paper and math for your long-term cold storage, while retaining the convenience of an electronic signer when you actually need to move funds.

---

## 3) The Mechanics: The "How"

Codex32 relies on finite field math (specifically Galois Field 32) that has been simplified into lookup tables so a human can calculate it by hand. 

### Anatomy of a Codex32 Share
A standard Codex32 share we implemented is a 48-character string that looks something like this:
`MS12WSFPARFG0AFNHER0NAE08R0FNA0EFN83WMZT0A5AP6ZK`

Even though it looks like random letters, it is highly structured:
- **`MS`** (Human-readable part): Identifies this as a Master Seed string.
- **`1`**: A separator.
- **`2`** (Threshold `k`): The number of shares needed to recover the secret (in this case, 2). If this is `0`, the string is a single un-split master secret.
- **`WSFP`** (Identifier): A 4-character label that groups related shares together.
- **`A`** (Index): Identifies which specific share this is (e.g., Share A, Share C, or `S` for the Master Secret).
- **The Payload**: The actual secret data.
- **The Checksum**: The final characters, mathematically derived from the rest of the string to detect errors.

### Split-Sharing (k-of-N)
If you want to secure your Bitcoin such that losing one backup doesn't lose your funds, Codex32 lets you split the secret. For example, a 2-of-3 setup creates Share A, Share C, and Share D. Any two of those shares can be mathematically combined to reconstruct the Master Secret (`S` share).

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
- It notes the share identifier (`WSFP`) and the threshold (`k=2`).
- It prompts the user to enter or scan the next required share.
- If a user tries to scan a share from a *different* set, the device catches the mismatch and alerts the user.
- Once the threshold is met (e.g., Share A and Share C are entered), SeedSigner performs the Codex32 interpolation math to automatically recover the Master Secret (`S` share).

### 4.4. Seed Loading and Export
Once the `S` share is successfully recovered (or directly entered), SeedSigner loads it into active memory as the active signing seed. From here, the user can:
- Sign Partially Signed Bitcoin Transactions (PSBTs) normally.
- Generate and verify receive addresses.
- **Export Backups:** The user can navigate to the Backup menu and export the `S` share, or any of the entered split shares, visually on the screen or as a dynamically generated Codex32QR code to be transcribed onto paper or etched into metal.

---

## 5) Conclusion

The SeedSigner + Codex32 integration represents a massive leap forward for analog self-custody. By strictly adhering to the mathematical constraints of Codex32 while leveraging the stateless, optical air-gap of SeedSigner, we have created a workflow where a user can generate a seed phrase entirely offline by hand, perfectly verify its math without a computer, and securely use it to sign transactions without ever putting the master key on a persistent, internet-connected device. 

This implementation brings the "don't trust, verify" ethos to the very generation and storage of the private key itself.
