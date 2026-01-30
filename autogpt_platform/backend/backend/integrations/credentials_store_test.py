"""Tests for the integration credentials store.

This module tests:
- PKCE code challenge generation (SHA-256 + base64url)
- Default credential list composition
- Credential store helpers (filtering, provider listing)
"""

import base64
import hashlib

import pytest

from backend.integrations.credentials_store import IntegrationCredentialsStore


class TestGenerateCodeChallenge:
    """Tests for IntegrationCredentialsStore._generate_code_challenge."""

    def setup_method(self):
        self.store = IntegrationCredentialsStore()

    def test_code_challenge_returns_tuple(self):
        """Should return a (code_challenge, code_verifier) tuple."""
        result = self.store._generate_code_challenge()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_code_verifier_is_nonempty_string(self):
        """The code verifier should be a non-empty URL-safe string."""
        _, code_verifier = self.store._generate_code_challenge()
        assert isinstance(code_verifier, str)
        assert len(code_verifier) > 0

    def test_code_challenge_is_sha256_of_verifier(self):
        """The code challenge should be the base64url-encoded SHA-256 of the verifier."""
        code_challenge, code_verifier = self.store._generate_code_challenge()

        expected_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        expected_challenge = (
            base64.urlsafe_b64encode(expected_hash).decode("utf-8").replace("=", "")
        )
        assert code_challenge == expected_challenge

    def test_code_challenge_has_no_padding(self):
        """The code challenge should not contain base64 padding characters."""
        code_challenge, _ = self.store._generate_code_challenge()
        assert "=" not in code_challenge

    def test_code_challenge_is_url_safe(self):
        """The code challenge should only contain URL-safe characters."""
        code_challenge, _ = self.store._generate_code_challenge()
        # URL-safe base64 characters: A-Z, a-z, 0-9, -, _
        import re

        assert re.match(r"^[A-Za-z0-9_-]+$", code_challenge)

    def test_code_challenge_uniqueness(self):
        """Two calls should produce different code challenges."""
        challenge1, verifier1 = self.store._generate_code_challenge()
        challenge2, verifier2 = self.store._generate_code_challenge()
        assert verifier1 != verifier2
        assert challenge1 != challenge2


class TestDefaultCredentials:
    """Tests for the DEFAULT_CREDENTIALS list."""

    def test_default_credentials_list_is_nonempty(self):
        """The default credentials list should contain entries."""
        from backend.integrations.credentials_store import DEFAULT_CREDENTIALS

        assert len(DEFAULT_CREDENTIALS) > 0

    def test_default_credentials_have_unique_ids(self):
        """Each default credential should have a unique ID."""
        from backend.integrations.credentials_store import DEFAULT_CREDENTIALS

        ids = [c.id for c in DEFAULT_CREDENTIALS]
        assert len(ids) == len(set(ids)), "Duplicate credential IDs found"

    def test_default_credentials_have_unique_providers(self):
        """Each default credential should have a unique provider."""
        from backend.integrations.credentials_store import DEFAULT_CREDENTIALS

        providers = [c.provider for c in DEFAULT_CREDENTIALS]
        assert len(providers) == len(set(providers)), "Duplicate providers found"

    def test_ollama_credentials_are_present(self):
        """Ollama credentials should always be in the default list."""
        from backend.integrations.credentials_store import (
            DEFAULT_CREDENTIALS,
            ollama_credentials,
        )

        assert ollama_credentials in DEFAULT_CREDENTIALS

    def test_ollama_credentials_have_fake_key(self):
        """Ollama credentials should have a FAKE_API_KEY since ollama doesn't need one."""
        from backend.integrations.credentials_store import ollama_credentials

        assert ollama_credentials.api_key.get_secret_value() == "FAKE_API_KEY"

    def test_default_credentials_have_no_expiry(self):
        """All default API key credentials should have no expiration."""
        from backend.integrations.credentials_store import DEFAULT_CREDENTIALS

        for cred in DEFAULT_CREDENTIALS:
            assert cred.expires_at is None, f"Credential {cred.provider} has an expiry"


class TestIntegrationCredentialsStoreInit:
    """Tests for IntegrationCredentialsStore initialization."""

    def test_store_initializes_with_none_locks(self):
        """The store should initialize with _locks set to None."""
        store = IntegrationCredentialsStore()
        assert store._locks is None
