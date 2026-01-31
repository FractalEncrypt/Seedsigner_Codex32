# SeedSigner Codex32

Convert [Codex32 (BIP-93)](https://github.com/bitcoin/bips/blob/master/bip-0093.mediawiki) shares to BIP39 mnemonics for use with any Bitcoin wallet.

**→ [Setup & Usage](codex32_terminal/README.md)**

## Why?

Codex32 lets you create and verify Bitcoin seed backups entirely by hand—no electronics needed. But wallet support is nearly nonexistent. This tool bridges the gap: enter your Codex32 shares and get a standard 12-word BIP39 mnemonic.

## Ecosystem

| Resource | Description |
|----------|-------------|
| [BIP-93](https://github.com/bitcoin/bips/blob/master/bip-0093.mediawiki) | Codex32 specification |
| [secretcodex32.com](https://secretcodex32.com) | Official paper worksheets & volvelles |
| [rust-codex32](https://github.com/apoelstra/rust-codex32) | Rust reference implementation (Andrew Poelstra) |
| [python-codex32](https://github.com/benwestgate/python-codex32) | Python library (Ben Westgate) |
| [Bails](https://github.com/BenWestgate/Bails) | First wallet with native codex32 support |
| [SeedSigner](https://github.com/SeedSigner/seedsigner) | Target platform for this integration |

## Credits

- **FractalEncrypt** — This project
- **Leon Olsson Curr & Pearlwort Sneed** — Codex32 creators
- **Andrew Poelstra** — Rust reference, Blockstream Research
- **Ben Westgate** — python-codex32 library, Bails wallet

## License

MIT
