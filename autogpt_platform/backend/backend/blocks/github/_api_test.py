import pytest
from pydantic import SecretStr

from backend.blocks.github._api import (
    _convert_to_api_url,
    _get_headers,
    convert_comment_url_to_api_endpoint,
    get_api,
)
from backend.data.model import APIKeyCredentials
from backend.util.request import Requests


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_credentials() -> APIKeyCredentials:
    return APIKeyCredentials(
        id="01234567-89ab-cdef-0123-456789abcdef",
        provider="github",
        api_key=SecretStr("test-api-key"),
        title="Test GitHub API key",
        expires_at=None,
    )


# ── _convert_to_api_url ──────────────────────────────────────────────────────


def test_convert_repo_url():
    result = _convert_to_api_url("https://github.com/owner/repo")
    assert result == "https://api.github.com/repos/owner/repo"


def test_convert_issue_url():
    result = _convert_to_api_url("https://github.com/owner/repo/issues/1")
    assert result == "https://api.github.com/repos/owner/repo/issues/1"


def test_convert_pr_url():
    result = _convert_to_api_url("https://github.com/owner/repo/pull/1")
    assert result == "https://api.github.com/repos/owner/repo/pull/1"


def test_convert_invalid_url():
    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        _convert_to_api_url("https://github.com/only-owner")


# ── convert_comment_url_to_api_endpoint ───────────────────────────────────────


def test_convert_comment_url_issuecomment():
    url = "https://github.com/owner/repo/issues/42#issuecomment-123"
    result = convert_comment_url_to_api_endpoint(url)
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/123"


def test_convert_comment_url_issuecomment_on_pull():
    """A PR comment URL with #issuecomment should convert /pull/ to /issues/."""
    url = "https://github.com/owner/repo/pull/7#issuecomment-456"
    result = convert_comment_url_to_api_endpoint(url)
    assert result == "https://api.github.com/repos/owner/repo/issues/comments/456"


def test_convert_comment_url_discussion():
    url = "https://github.com/owner/repo/pull/10#discussion_r789"
    result = convert_comment_url_to_api_endpoint(url)
    assert result == "https://api.github.com/repos/owner/repo/pulls/comments/789"


def test_convert_comment_url_already_api():
    api_url = "https://api.github.com/repos/owner/repo/issues/comments/999"
    result = convert_comment_url_to_api_endpoint(api_url)
    assert result == api_url


def test_convert_comment_url_no_fragment_falls_back():
    """A plain issue URL with no comment fragment falls back to _convert_to_api_url."""
    url = "https://github.com/owner/repo/issues/5"
    result = convert_comment_url_to_api_endpoint(url)
    assert result == "https://api.github.com/repos/owner/repo/issues/5"


# ── _get_headers ──────────────────────────────────────────────────────────────


def test_get_headers(mock_credentials: APIKeyCredentials):
    headers = _get_headers(mock_credentials)
    assert headers["Authorization"] == "Bearer test-api-key"
    assert headers["Accept"] == "application/vnd.github.v3+json"
    assert len(headers) == 2


# ── get_api ───────────────────────────────────────────────────────────────────


def test_get_api_returns_requests(mock_credentials: APIKeyCredentials):
    api = get_api(mock_credentials)
    assert isinstance(api, Requests)


def test_get_api_sets_trusted_origins(mock_credentials: APIKeyCredentials):
    api = get_api(mock_credentials)
    assert "api.github.com" in api.trusted_origins
    assert "github.com" in api.trusted_origins


def test_get_api_sets_extra_headers(mock_credentials: APIKeyCredentials):
    api = get_api(mock_credentials)
    assert api.extra_headers is not None
    assert api.extra_headers["Authorization"] == "Bearer test-api-key"
    assert api.extra_headers["Accept"] == "application/vnd.github.v3+json"


def test_get_api_with_convert_urls_true(mock_credentials: APIKeyCredentials):
    api = get_api(mock_credentials, convert_urls=True)
    assert api.extra_url_validator is not None


def test_get_api_with_convert_urls_false(mock_credentials: APIKeyCredentials):
    api = get_api(mock_credentials, convert_urls=False)
    assert api.extra_url_validator is None
