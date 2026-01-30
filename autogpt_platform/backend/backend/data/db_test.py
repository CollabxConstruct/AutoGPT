"""Tests for backend.data.db utility functions and models."""

import uuid
from unittest.mock import patch
from urllib.parse import parse_qsl, urlparse

from backend.data.db import BaseDbModel, add_param


class TestAddParam:
    def test_add_param_basic(self):
        """add_param adds a query parameter to a URL with no existing params."""
        result = add_param("http://localhost:5432", "key", "value")
        parsed = urlparse(result)
        params = dict(parse_qsl(parsed.query))
        assert params == {"key": "value"}
        assert parsed.scheme == "http"
        assert parsed.netloc == "localhost:5432"

    def test_add_param_existing_params(self):
        """add_param appends to a URL that already has query parameters."""
        result = add_param(
            "http://localhost:5432?existing=param", "new_key", "new_value"
        )
        parsed = urlparse(result)
        params = dict(parse_qsl(parsed.query))
        assert params == {"existing": "param", "new_key": "new_value"}

    def test_add_param_overwrites(self):
        """add_param overwrites an existing key with the new value."""
        result = add_param("http://localhost:5432?key=old", "key", "new")
        parsed = urlparse(result)
        params = dict(parse_qsl(parsed.query))
        assert params == {"key": "new"}


class TestGetDatabaseSchema:
    def test_get_database_schema_default(self):
        """Returns 'public' when DATABASE_URL has no schema query parameter."""
        with patch(
            "backend.data.db.DATABASE_URL", "postgresql://localhost:5432/mydb"
        ):
            from backend.data.db import get_database_schema

            result = get_database_schema()
            assert result == "public"

    def test_get_database_schema_custom(self):
        """Returns the custom schema when DATABASE_URL has a schema query parameter."""
        with patch(
            "backend.data.db.DATABASE_URL",
            "postgresql://localhost:5432/mydb?schema=custom_schema",
        ):
            from backend.data.db import get_database_schema

            result = get_database_schema()
            assert result == "custom_schema"


class TestBaseDbModel:
    def test_base_db_model_auto_id(self):
        """BaseDbModel generates a valid UUID id when none is provided."""
        model = BaseDbModel()
        # Verify it is a valid UUID string
        parsed = uuid.UUID(model.id)
        assert str(parsed) == model.id

    def test_base_db_model_provided_id(self):
        """BaseDbModel keeps a provided id value."""
        model = BaseDbModel(id="custom-id-123")
        assert model.id == "custom-id-123"

    def test_base_db_model_empty_id(self):
        """BaseDbModel generates a new UUID when an empty string id is provided."""
        model = BaseDbModel(id="")
        assert model.id != ""
        # Verify the generated id is a valid UUID
        parsed = uuid.UUID(model.id)
        assert str(parsed) == model.id
