#!/usr/bin/env python3
"""Run all tests for codex32_terminal."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent / "tests"

TEST_FILES = [
    "test_vectors.py",
    "test_share_recovery.py",
    "test_validation.py",
    "test_invalid_vectors.py",
]


def main() -> int:
    failed = []
    passed = []

    for test_file in TEST_FILES:
        test_path = TESTS_DIR / test_file
        if not test_path.exists():
            print(f"SKIP: {test_file} (not found)")
            continue

        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print('='*60)

        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            passed.append(test_file)
        else:
            failed.append(test_file)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print(f"\nFailed tests: {', '.join(failed)}")
        return 1

    print("\nAll tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
