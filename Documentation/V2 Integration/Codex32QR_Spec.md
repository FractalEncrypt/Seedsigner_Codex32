---
description: Codex32QR format specification aligned to SeedSigner V2 implementation with explanatory guidance and extended vectors
---

# Codex32QR Format Specification (SeedSigner V2 Profile)

This document defines the Codex32 QR profile implemented in SeedSigner V2 and is intended to help developers port compatible support into other hardware wallets and airgapped tools.

Like the SeedQR specification, this write-up balances strict interoperability rules with practical, human-centered workflow guidance.

The keywords **MUST**, **SHOULD**, and **MAY** are normative in this document.

---

## 1) Scope and profile summary

This specification covers:

1. A single-frame textual Codex32 QR payload profile (`Codex32QR/v1-48`).
2. Import behavior for direct scan and multi-share collection mode.
3. Export behavior for share selection and labeling.
4. Validation and fail-safe behavior.
5. Reference vectors for interop testing.

This specification does **not** define:

1. Compact/binary Codex32 QR transport.
2. Animated/multipart Codex32 QR transport.
3. Codex32 payloads longer than the 48-character profile.

Implemented profile constraints in SeedSigner V2:

- Canonical payload length: **48 chars**
- QR version: **3**
- QR module size: **29x29**
- Error correction: **L**
- Max split shares in collection: **5**

---

## 2) Quick review of Codex32 share strings

Codex32 shares are human-readable strings. In this profile they are carried directly as plain text in a QR.

Example:

```text
MS12WSFPARFG0AFNHER0NAE08R0FNA0EFN83WMZT0A5AP6ZK
```

Conceptual components:

1. `ms` human-readable part (HRP)
2. `1` separator
3. `k` threshold character
4. 4-character identifier (share set tag)
5. Share index (for example `A`, `C`, `S`)
6. Data + checksum body

Notes:

- Codex32 is canonically lowercase, but all-uppercase payloads are valid and are used as display canonical form in this implementation profile.
- For this profile, payloads are normalized to uppercase without separators for display/compare/export.

---

## 3) Normative payload profile (`Codex32QR/v1-48`)

### 3.1 Canonical payload form

The canonical payload is a **48-character Codex32 share string**:

- Prefix: `MS1`
- Canonical display form: uppercase
- Separators: none
- Example shape: `MS1.............................................` (48 total chars)

### 3.2 Input normalization rules

Implementations SHOULD accept user input with whitespace and hyphens, then normalize by:

1. Removing all whitespace.
2. Removing hyphen separators.
3. Validating checksum against normalized content.

### 3.3 Validation requirements

A payload MUST satisfy all of the following:

1. Exact length = 48 characters.
2. Single-case input (all lower or all upper) before canonicalization.
3. Prefix `MS1` (case-insensitive pre-check).
4. Valid Codex32 parse and checksum.
5. Valid Codex32 HRP (`ms`).

Any validation failure MUST be treated as invalid Codex32 input.

---

## 4) QR encoding profile and sizing rationale

For `Codex32QR/v1-48`, emit a static single-frame QR code with:

1. Text payload: canonical Codex32 string.
2. Error correction: `L`.
3. Version: `3`.
4. Module size: `29x29`.
5. Standard quiet zone.
6. Black/white modules only.

### 4.1 Why 29x29 is used

This format stores the Codex32 string directly as QR text data. The payload length is fixed:

```text
48 characters
```

At error correction level `L`, Version 3 (29x29) comfortably supports this textual size in common QR text modes, while remaining practical for printed and hand-transcribed workflows.

### 4.2 Phone-readable text output

Because this profile stores plain text, generic phone QR scanners will normally decode the exact Codex32 string. This is useful for interop checks:

1. Scan the QR on a phone.
2. Confirm the decoded text equals the expected Codex32 payload.
3. Compare using canonical uppercase/no-separator normalization.

---

## 5) Import behavior

### 5.1 Direct scan mode

In direct scan mode:

1. If `share_idx = s`, the seed MAY be loaded immediately.
2. If `share_idx != s`, the implementation MUST transition into multi-share collection flow for that share set (`k` + identifier) instead of hard-rejecting the scan.
3. UX MUST prompt for additional shares and allow either scan or manual entry until recoverability is reached.

### 5.2 Multi-share collection mode

In collection mode, split shares are accepted and accumulated for recovery.

Collection rules:

1. Share headers (`k`, identifier) MUST match collection context.
2. Threshold `k` MUST be an integer >= 2.
3. A maximum of **5 split shares** is supported.
4. Duplicate index, same payload: idempotent (no-op).
5. Duplicate index, different payload: MUST require explicit user confirmation before replacement.

When enough compatible shares are present, implementations recover `S` via Codex32 interpolation and validate recovered `S` as a 48-character secret share before loading.

---

## 6) Export behavior

### 6.1 Recoverability gate

Multi-share export MUST only be enabled when a valid recoverable `S` is available.

No partial-share export is allowed before recoverability.

### 6.2 Export share set

Export candidate set consists of:

1. Entered shares currently present in collection metadata.
2. Recovered `S` if `S` was not originally entered.

`S` source labeling:

- `entered`: user provided `S` directly.
- `derived`: `S` recovered from split shares.

### 6.3 Export ordering

Display/export ordering MUST be:

1. `S` first (if present), then
2. remaining split-share indices in sorted order.

If `S` is derived, UX MUST visibly label it as **Derived** (for example: `S Share (Derived)`).

---

## 7) Failure handling requirements

1. Invalid Codex32-like payloads MUST resolve to invalid status (no fallback into unrelated QR types).
2. No auto-correction of payload characters on parse/checksum failure.
3. Metadata inconsistencies in export state (invalid payload, index mismatch, unsupported overflow) MUST fail closed and route to unavailable-export behavior.

---

## 8) Recoverability model

This profile intentionally favors recoverability through readable text transport:

1. Most phone scanners can decode the QR into a plain Codex32 string.
2. A user can manually transcribe that string if required.
3. Another compatible tool can validate checksum and parse the share directly from text.

For split sets, practical recovery still requires preserving at least `k` valid shares from the same identifier set.

This is the same recoverability principle used by Standard SeedQR: the encoded QR data remains directly visible and transferable without proprietary binary decoding.

---

## 9) Interoperability checklist for other projects

To implement compatible support in another device/app:

1. Treat payload as plain-text Codex32.
2. Enforce the 48-char profile and checksum validity.
3. Normalize to uppercase for display/compare/export.
4. Route non-`s` direct scans into collection mode with mixed scan/manual continuation.
5. Preserve explicit `entered` vs `derived` source semantics for `S`.
6. Keep export gating tied to successful `S` recoverability.

---

## 10) Reference test vectors

The style below mirrors BIP-93 style vectors with implementation-focused metadata.

### Test vector 1 (2-of-N, identifier `L0VE`)

This vector demonstrates recovering `S` from two split shares (`A` and `C`), and exporting multisig cosigner data.

```text
Share A: MS12L0VEAARWENFLUFFYTAFLCATQTTGGERGGM0C6A8FRJE57
Share C: MS12L0VECGREGGTTQTACLFATYFFULFNEWRAWFG0DZCVNPVSE
Recovered S: MS12L0VESNR0FEXZ5X5VKQ5ZSQYGKYZCCRXEHDEMFNYQDH2U
```

Multisig cosigner export:

- Script: Native Segwit (BIP84)
- Network: testnet4
- Fingerprint: `a6c4da6d`
- Derivation: `m/48'/1'/0'/2'`
- Xpub: `tpubDEZFDLpFnphqgS5xcYwrTgZr8Z57vf3HyxKv6W2rWoRjNmyUwAXU48YyXUBiTf2cKZdU9wpGavpngQq25uWVDptDZF1bXb8qjgYRsmwsJmF`

QR examples:

| Share A QR | Share C QR |
|---|---|
| ![L0VE Share A](../QRs/Split%20Shares/love_share_a.png) | ![L0VE Share C](../QRs/Split%20Shares/love_share_c.png) |

---

### Test vector 2 (2-of-N, identifier `WSFP`)

This vector demonstrates split-share recovery and multisig cosigner export from the recovered key.

```text
Share A: MS12WSFPARFG0AFNHER0NAE08R0FNA0EFN83WMZT0A5AP6ZK
Share C: MS12WSFPC8NFE0ANF0R80EAN0REHNFA0GFRYUQYKDKJJPYV5
S Share (Master Codex32 key): MS12WSFPSASMA35NSTR6MR88JRAWNQRT62ELZ3NSQ592PAXE
```

Multisig cosigner export:

- Script: Native Segwit (BIP84)
- Network: testnet4
- Fingerprint: `c17858e9`
- Derivation: `m/48'/1'/0'/2'`
- Xpub: `tpubDEdZTjm4ctaVZ1rrQ6aothXSPMERU4aMVHcjKoMDoWY5Sw6kfoSct4pkt5Np1112GGWz7c3nr2X4Q`

QR examples:

| Share A QR | Share C QR |
|---|---|
| ![WSFP Share A](../QRs/Split%20Shares/wsfp_share_a.png) | ![WSFP Share C](../QRs/Split%20Shares/wsfp_share_c.png) |

---

### Test vector 3 (4-of-N, identifier `F0UR`)

This vector demonstrates a larger split set and single-sig export from recovered `S`.

```text
Share A: MS14F0URATWENTYSXCHARACTERSC0DEX32GAFTTAVTH203CW
Share C: MS14F0URCG23XED0CSRETCARAHCXSYTNEWTHFYZQ3ZRYNTTD
Share D: MS14F0URDCTERSC0DEX32GTWENTYSXCHARA8GXQMPD8VZ7NX
Share E: MS14F0URENTYSXCHARACTERSC0DEX32GTWEKCHMRL3FDC6VV
S Share (Master Codex32 key): MS14F0URSHTV9MFHTA5G8XDV4SUPMLS4LSECR334Y0CUHVXQ
```

Single-sig export:

- Script: Native Segwit (BIP84)
- Network: testnet4
- Fingerprint: `04b3384e`
- Derivation: `m/84'/1'/0'`
- Xpub: `tpubDCWvnrJKbRrdfij6mQozuWNg9VsCMQQd8cTBoTCQntKxKzdNCydvRVK7YrMwnRpnYMV8mMNdtfyJarK3j2AhGZGwXy7yZ2nAgdiBdW78Qad`

QR examples:

| Share A QR | Share C QR |
|---|---|
| ![F0UR Share A](../QRs/Split%20Shares/f0ur_share_a.png) | ![F0UR Share C](../QRs/Split%20Shares/f0ur_share_c.png) |

| Share D QR | Share E QR |
|---|---|
| ![F0UR Share D](../QRs/Split%20Shares/f0ur_share_d.png) | ![F0UR Share E](../QRs/Split%20Shares/f0ur_share_e.png) |

---

### Test vector 4 (single-share import example)

This vector demonstrates direct `S` share loading (no additional share collection required).

```text
S Share: MS12SEEDSAEFE4J44NR4FRNEZ7ZKEPA46XMJ4J2YXYJTC9YC
```

Multisig cosigner export:

- Script: Native Segwit (BIP84)
- Network: testnet4
- Fingerprint: `0e549ffd`
- Derivation: `m/48'/1'/0'/2'`
- Xpub: `tpubDExD4dQSADRK255J6TvHv7pqNH3WY4PmFyQyKtYdnpnRBxLDMSoe7ECSscP578zPYmf3TFj4gu2MKX8ay7fZDqWrjaWES8KDZwZxEHmCKv8`

QR example:

![Single-share S vector QR](../QRs/S%20Shares/codex32_s_share_1.png)

---

## 11) Additional QR assets in this repository

In addition to split-share QR images above (and the single-share S example already shown), the following S-share PNGs are available in this repository for scan testing:

- `../QRs/S Shares/codex32_s_share_2.png`
- `../QRs/S Shares/codex32_s_share_3.png`

These assets are black/white and generated for practical device testing of the `Codex32QR/v1-48` textual profile.

---

## 12) Why this profile is intentionally constrained

### 12.1 48-character support

This specification intentionally standardizes the 48-character profile because it maps to publicly available Codex32 materials and current demand.

### 12.2 Maximum of 5 split shares

This implementation caps split-share support at 5 shares. In practical manual workflows, creating and verifying larger sets is increasingly error-prone and uncommon.

### 12.3 29x29 and no compact mode

The current format uses a 29x29 QR because it reliably carries the supported textual payload with current constraints. A compact Codex32 QR mode may be possible in the future, but is out of scope here.

---

## 13) Acknowledgements

Special thanks to **Ben Westgate** and **Perlwort Snead** for guidance that materially improved this implementation profile.
