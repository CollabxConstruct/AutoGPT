"""Tests for the API key manager.

This module tests:
- API key generation format, prefix, postfix, and hash
- Uniqueness of generated keys
- Verification of valid and invalid keys
- Rejection of keys with wrong prefix or tampered content
"""

import hashlib

import pytest

from autogpt_libs.api_key.key_manager import APIKeyManager


class TestGenerateApiKey:
    """Tests for the generate_api_key method."""

    def setup_method(self):
        self.manager = APIKeyManager()

    def test_generate_api_key_format(self):
        """Generated API key raw value starts with 'agpt_'."""
        key = self.manager.generate_api_key()
        assert key.raw.startswith("agpt_")

    def test_generate_api_key_prefix_length(self):
        """The prefix field is exactly 8 characters long."""
        key = self.manager.generate_api_key()
        assert len(key.prefix) == 8

    def test_generate_api_key_postfix_length(self):
        """The postfix field is exactly 8 characters long."""
        key = self.manager.generate_api_key()
        assert len(key.postfix) == 8

    def test_generate_api_key_hash(self):
        """The hash field matches the SHA-256 hex digest of the raw key."""
        key = self.manager.generate_api_key()
        expected_hash = hashlib.sha256(key.raw.encode()).hexdigest()
        assert key.hash == expected_hash

    def test_generate_api_key_prefix_is_start_of_raw(self):
        """The prefix field is the first 8 characters of the raw key."""
        key = self.manager.generate_api_key()
        assert key.prefix == key.raw[:8]

    def test_generate_api_key_postfix_is_end_of_raw(self):
        """The postfix field is the last 8 characters of the raw key."""
        key = self.manager.generate_api_key()
        assert key.postfix == key.raw[-8:]

    def test_generate_api_key_uniqueness(self):
        """Two generated keys must have different raw values."""
        key1 = self.manager.generate_api_key()
        key2 = self.manager.generate_api_key()
        assert key1.raw != key2.raw
        assert key1.hash != key2.hash


class TestVerifyApiKey:
    """Tests for the verify_api_key method."""

    def setup_method(self):
        self.manager = APIKeyManager()

    def test_verify_api_key_valid(self):
        """A generated key verifies successfully against its own hash."""
        key = self.manager.generate_api_key()
        assert self.manager.verify_api_key(key.raw, key.hash) is True

    def test_verify_api_key_wrong_key(self):
        """A completely different key fails verification."""
        key = self.manager.generate_api_key()
        other_key = self.manager.generate_api_key()
        assert self.manager.verify_api_key(other_key.raw, key.hash) is False

    def test_verify_api_key_wrong_prefix(self):
        """A key without the 'agpt_' prefix fails verification."""
        key = self.manager.generate_api_key()
        bad_key = "xxxx_" + key.raw[5:]
        assert self.manager.verify_api_key(bad_key, key.hash) is False

    def test_verify_api_key_tampered(self):
        """A key with modified characters fails verification."""
        key = self.manager.generate_api_key()
        # Tamper with the key by changing a character near the end
        tampered = key.raw[:-1] + ("a" if key.raw[-1] != "a" else "b")
        assert self.manager.verify_api_key(tampered, key.hash) is False
