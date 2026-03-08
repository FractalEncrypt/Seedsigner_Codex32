"""Tests for SecureBytes memory wiping."""

import pytest
from secure_bytes import SecureBytes


class TestSecureBytes:
    def test_get_returns_original_data(self):
        data = b"\xde\xad\xbe\xef" * 4
        sb = SecureBytes(data)
        assert sb.get() == data

    def test_wipe_zeros_buffer(self):
        data = b"\xff" * 16
        sb = SecureBytes(data)
        sb.wipe()
        assert sb._buf == bytearray(16)
        assert all(b == 0 for b in sb._buf)

    def test_get_after_wipe_raises(self):
        sb = SecureBytes(b"\x01\x02\x03")
        sb.wipe()
        with pytest.raises(ValueError, match="wiped"):
            sb.get()

    def test_double_wipe_is_safe(self):
        sb = SecureBytes(b"\xaa" * 8)
        sb.wipe()
        sb.wipe()
        assert sb.is_wiped

    def test_context_manager_wipes_on_exit(self):
        data = b"\xca\xfe" * 8
        with SecureBytes(data) as sb:
            assert sb.get() == data
        assert sb.is_wiped
        assert all(b == 0 for b in sb._buf)

    def test_context_manager_wipes_on_exception(self):
        sb = SecureBytes(b"\xbb" * 4)
        with pytest.raises(RuntimeError):
            with sb:
                raise RuntimeError("boom")
        assert sb.is_wiped

    def test_empty_bytes(self):
        sb = SecureBytes(b"")
        sb.wipe()
        assert sb.is_wiped

    def test_len(self):
        sb = SecureBytes(b"\x00" * 32)
        assert len(sb) == 32

    def test_repr_before_and_after_wipe(self):
        sb = SecureBytes(b"\x01" * 16)
        assert "16 bytes" in repr(sb)
        sb.wipe()
        assert "wiped" in repr(sb)
