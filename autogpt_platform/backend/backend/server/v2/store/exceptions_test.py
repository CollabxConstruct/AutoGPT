import pytest

import backend.server.v2.store.exceptions


def test_media_upload_error_hierarchy() -> None:
    """All media-related errors inherit from MediaUploadError."""
    media_error_classes = [
        backend.server.v2.store.exceptions.InvalidFileTypeError,
        backend.server.v2.store.exceptions.FileSizeTooLargeError,
        backend.server.v2.store.exceptions.FileReadError,
        backend.server.v2.store.exceptions.StorageConfigError,
        backend.server.v2.store.exceptions.StorageUploadError,
        backend.server.v2.store.exceptions.VirusDetectedError,
        backend.server.v2.store.exceptions.VirusScanError,
    ]
    for error_class in media_error_classes:
        assert issubclass(
            error_class,
            backend.server.v2.store.exceptions.MediaUploadError,
        ), f"{error_class.__name__} should inherit from MediaUploadError"

    # Also verify MediaUploadError itself inherits from Exception
    assert issubclass(
        backend.server.v2.store.exceptions.MediaUploadError, Exception
    )


def test_media_upload_error_is_catchable() -> None:
    """MediaUploadError subclasses can be caught by the base class."""
    with pytest.raises(backend.server.v2.store.exceptions.MediaUploadError):
        raise backend.server.v2.store.exceptions.InvalidFileTypeError(
            "Unsupported file type: .exe"
        )

    with pytest.raises(backend.server.v2.store.exceptions.MediaUploadError):
        raise backend.server.v2.store.exceptions.FileSizeTooLargeError(
            "File exceeds 10MB limit"
        )


def test_virus_detected_error_message() -> None:
    """VirusDetectedError stores threat_name and generates a message."""
    error = backend.server.v2.store.exceptions.VirusDetectedError(
        threat_name="EICAR-Test-File"
    )
    assert error.threat_name == "EICAR-Test-File"
    assert "EICAR-Test-File" in str(error)


def test_virus_detected_error_custom_message() -> None:
    """VirusDetectedError can accept a custom message."""
    error = backend.server.v2.store.exceptions.VirusDetectedError(
        threat_name="Trojan.Gen",
        message="Custom virus message",
    )
    assert error.threat_name == "Trojan.Gen"
    assert str(error) == "Custom virus message"


def test_store_error_hierarchy() -> None:
    """All store-related errors inherit from StoreError."""
    store_error_classes = [
        backend.server.v2.store.exceptions.AgentNotFoundError,
        backend.server.v2.store.exceptions.CreatorNotFoundError,
        backend.server.v2.store.exceptions.ListingExistsError,
        backend.server.v2.store.exceptions.DatabaseError,
        backend.server.v2.store.exceptions.ProfileNotFoundError,
        backend.server.v2.store.exceptions.ListingNotFoundError,
        backend.server.v2.store.exceptions.SubmissionNotFoundError,
        backend.server.v2.store.exceptions.InvalidOperationError,
        backend.server.v2.store.exceptions.UnauthorizedError,
    ]
    for error_class in store_error_classes:
        assert issubclass(
            error_class,
            backend.server.v2.store.exceptions.StoreError,
        ), f"{error_class.__name__} should inherit from StoreError"

    # Also verify StoreError itself inherits from Exception
    assert issubclass(
        backend.server.v2.store.exceptions.StoreError, Exception
    )


def test_database_error() -> None:
    """DatabaseError is a StoreError and can be raised/caught."""
    with pytest.raises(backend.server.v2.store.exceptions.StoreError):
        raise backend.server.v2.store.exceptions.DatabaseError(
            "Connection timeout"
        )

    error = backend.server.v2.store.exceptions.DatabaseError("Query failed")
    assert isinstance(error, backend.server.v2.store.exceptions.StoreError)
    assert isinstance(error, Exception)
    assert str(error) == "Query failed"


def test_store_errors_are_independent_from_media_errors() -> None:
    """StoreError and MediaUploadError are separate hierarchies."""
    assert not issubclass(
        backend.server.v2.store.exceptions.StoreError,
        backend.server.v2.store.exceptions.MediaUploadError,
    )
    assert not issubclass(
        backend.server.v2.store.exceptions.MediaUploadError,
        backend.server.v2.store.exceptions.StoreError,
    )
