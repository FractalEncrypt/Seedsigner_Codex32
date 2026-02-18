"""Terminal CLI for Codex32-native BIP32 workflow."""

from __future__ import annotations

import argparse

import controller


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex32-native terminal workflow")
    parser.add_argument(
        "share",
        nargs="?",
        help="Optional initial codex32 share (S-share or split share) to start from.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Use full-share paste mode instead of box-by-box entry.",
    )
    parser.add_argument(
        "--network",
        default="mainnet",
        choices=["mainnet", "testnet4"],
        help="Descriptor/xpub network (default: mainnet).",
    )
    return parser.parse_args()


def main() -> int:
    """CLI runner."""
    args = parse_args()
    entry_mode = "full" if args.full else "box"
    return controller.run(
        entry_mode=entry_mode,
        network=args.network,
        initial_share=args.share,
    )


if __name__ == "__main__":
    raise SystemExit(main())
