"""Unit tests for src/main_app/core/crypto.py module."""

from __future__ import annotations

import pytest
from src.main_app.services.core.crypto import CryptoService


def test_encrypt_decrypt_roundtrip():
    msg = "secret message"
    token = CryptoService().encrypt(msg)
    assert isinstance(token, bytes | bytearray)
    plain = CryptoService().decrypt(token)
    assert plain == msg


class TestEncryptDecrypt:
    def test_round_trip(self):
        plaintext = "hello world"
        token = CryptoService().encrypt(plaintext)
        assert isinstance(token, bytes)
        assert CryptoService().decrypt(token) == plaintext

    def test_empty_string(self):
        token = CryptoService().encrypt("")
        assert CryptoService().decrypt(token) == ""

    def test_unicode_content(self):
        plaintext = "Ünïcödé 日本語"
        token = CryptoService().encrypt(plaintext)
        assert CryptoService().decrypt(token) == plaintext

    def test_long_string(self):
        plaintext = "A" * 10_000
        token = CryptoService().encrypt(plaintext)
        assert CryptoService().decrypt(token) == plaintext

    def test_encrypted_is_different_from_plaintext(self):
        plaintext = "secret-oauth-token"
        token = CryptoService().encrypt(plaintext)
        assert plaintext.encode() not in token

    def test_decrypt_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Unable to decrypt"):
            CryptoService().decrypt(b"not-a-valid-fernet-token")

    def test_different_encryptions_produce_different_tokens(self):
        """Fernet uses a random IV, so same input should give different ciphertext."""
        plaintext = "same-value"
        token1 = CryptoService().encrypt(plaintext)
        token2 = CryptoService().encrypt(plaintext)
        assert token1 != token2
        assert CryptoService().decrypt(token1) == CryptoService().decrypt(token2)
