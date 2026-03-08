"""Secure memory handling for sensitive cryptographic material.

On hardware wallets and air-gapped devices, seed bytes and private keys
must not linger in memory after use.  Python's garbage collector offers
no timing guarantees, so this module provides explicit zeroing via
ctypes.memset and a context-manager interface for automatic cleanup.
"""

from __future__ import annotations

import ctypes
from typing import Optional


class SecureBytes:
    """A bytes-like wrapper that zeros its backing buffer on cleanup.

    Usage::

        with SecureBytes(seed_bytes) as sb:
            root = bip32.HDKey.from_seed(sb.get())
            # ... use root ...
        # buffer is zeroed here

    Or manually::

        sb = SecureBytes(data)
        try:
            do_work(sb.get())
        finally:
            sb.wipe()
    """

    def __init__(self, data: bytes) -> None:
        self._buf = bytearray(data)
        self._wiped = False

    def get(self) -> bytes:
        """Return the underlying bytes (read-only view)."""
        if self._wiped:
            raise ValueError("SecureBytes has already been wiped")
        return bytes(self._buf)

    def wipe(self) -> None:
        """Zero the backing buffer using ctypes.memset."""
        if self._wiped:
            return
        if len(self._buf) > 0:
            buf_addr = (ctypes.c_char * len(self._buf)).from_buffer(self._buf)
            ctypes.memset(buf_addr, 0, len(self._buf))
        self._wiped = True

    @property
    def is_wiped(self) -> bool:
        return self._wiped

    def __enter__(self) -> "SecureBytes":
        return self

    def __exit__(self, *exc) -> None:
        self.wipe()

    def __del__(self) -> None:
        self.wipe()

    def __len__(self) -> int:
        return len(self._buf)

    def __repr__(self) -> str:
        if self._wiped:
            return "SecureBytes(<wiped>)"
        return f"SecureBytes({len(self._buf)} bytes)"
