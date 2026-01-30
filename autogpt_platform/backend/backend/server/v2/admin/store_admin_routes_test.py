import datetime
import typing

import autogpt_libs.auth.depends
import autogpt_libs.auth.middleware
import autogpt_libs.auth.models
import fastapi
import fastapi.testclient
import prisma.enums
import pytest_mock

import backend.server.v2.admin.store_admin_routes
import backend.server.v2.store.model

# Using a fixed timestamp for reproducible tests
FIXED_NOW = datetime.datetime(2023, 1, 1, 0, 0, 0)

app = fastapi.FastAPI()
app.include_router(backend.server.v2.admin.store_admin_routes.router)

client = fastapi.testclient.TestClient(app)


def override_auth_middleware() -> dict[str, str]:
    """Override auth middleware for testing"""
    return {"sub": "test-admin-id", "role": "admin"}


def override_requires_admin_user() -> autogpt_libs.auth.models.User:
    """Override requires_admin_user for testing"""
    return autogpt_libs.auth.models.User(
        user_id="test-admin-id",
        email="admin@test.com",
        phone_number="",
        role="admin",
    )


app.dependency_overrides[autogpt_libs.auth.middleware.auth_middleware] = (
    override_auth_middleware
)
app.dependency_overrides[autogpt_libs.auth.depends.requires_admin_user] = (
    override_requires_admin_user
)


def test_get_admin_listings_success(
    mocker: pytest_mock.MockFixture,
) -> None:
    mocked_value = backend.server.v2.store.model.StoreListingsWithVersionsResponse(
        listings=[
            backend.server.v2.store.model.StoreListingWithVersions(
                listing_id="listing-1",
                slug="test-agent",
                agent_id="agent-1",
                agent_version=1,
                active_version_id="version-1",
                has_approved_version=True,
                creator_email="creator@test.com",
                latest_version=backend.server.v2.store.model.StoreSubmission(
                    agent_id="agent-1",
                    agent_version=1,
                    name="Test Agent",
                    sub_heading="A test agent",
                    slug="test-agent",
                    description="Test agent description",
                    image_urls=["image1.jpg"],
                    date_submitted=FIXED_NOW,
                    status=prisma.enums.SubmissionStatus.APPROVED,
                    runs=100,
                    rating=4.5,
                ),
                versions=[],
            )
        ],
        pagination=backend.server.v2.store.model.Pagination(
            current_page=1,
            total_items=1,
            total_pages=1,
            page_size=20,
        ),
    )
    mock_db_call = mocker.patch(
        "backend.server.v2.store.db.get_admin_listings_with_versions"
    )
    mock_db_call.return_value = mocked_value

    response = client.get("/admin/listings")
    assert response.status_code == 200

    data = (
        backend.server.v2.store.model.StoreListingsWithVersionsResponse.model_validate(
            response.json()
        )
    )
    assert len(data.listings) == 1
    assert data.listings[0].listing_id == "listing-1"
    assert data.listings[0].slug == "test-agent"
    assert data.pagination.total_items == 1

    mock_db_call.assert_called_once_with(
        status=None,
        search_query=None,
        page=1,
        page_size=20,
    )


def test_get_admin_listings_with_filters(
    mocker: pytest_mock.MockFixture,
) -> None:
    mocked_value = backend.server.v2.store.model.StoreListingsWithVersionsResponse(
        listings=[
            backend.server.v2.store.model.StoreListingWithVersions(
                listing_id="listing-2",
                slug="pending-agent",
                agent_id="agent-2",
                agent_version=1,
                has_approved_version=False,
                creator_email="pending@test.com",
                latest_version=backend.server.v2.store.model.StoreSubmission(
                    agent_id="agent-2",
                    agent_version=1,
                    name="Pending Agent",
                    sub_heading="A pending agent",
                    slug="pending-agent",
                    description="Pending agent description",
                    image_urls=[],
                    date_submitted=FIXED_NOW,
                    status=prisma.enums.SubmissionStatus.PENDING,
                    runs=0,
                    rating=0.0,
                ),
                versions=[],
            )
        ],
        pagination=backend.server.v2.store.model.Pagination(
            current_page=1,
            total_items=1,
            total_pages=1,
            page_size=20,
        ),
    )
    mock_db_call = mocker.patch(
        "backend.server.v2.store.db.get_admin_listings_with_versions"
    )
    mock_db_call.return_value = mocked_value

    response = client.get("/admin/listings?status=PENDING&search=pending")
    assert response.status_code == 200

    data = (
        backend.server.v2.store.model.StoreListingsWithVersionsResponse.model_validate(
            response.json()
        )
    )
    assert len(data.listings) == 1
    assert data.listings[0].slug == "pending-agent"

    mock_db_call.assert_called_once_with(
        status=prisma.enums.SubmissionStatus.PENDING,
        search_query="pending",
        page=1,
        page_size=20,
    )


def test_review_submission_success(
    mocker: pytest_mock.MockFixture,
) -> None:
    mocked_value = backend.server.v2.store.model.StoreSubmission(
        agent_id="agent-1",
        agent_version=1,
        name="Reviewed Agent",
        sub_heading="A reviewed agent",
        slug="reviewed-agent",
        description="Reviewed agent description",
        image_urls=["image1.jpg"],
        date_submitted=FIXED_NOW,
        status=prisma.enums.SubmissionStatus.APPROVED,
        runs=50,
        rating=4.0,
        store_listing_version_id="version-1",
        reviewer_id="test-admin-id",
        review_comments="Looks good",
    )
    mock_db_call = mocker.patch(
        "backend.server.v2.store.db.review_store_submission"
    )
    mock_db_call.return_value = mocked_value

    response = client.post(
        "/admin/submissions/version-1/review",
        json={
            "store_listing_version_id": "version-1",
            "is_approved": True,
            "comments": "Looks good",
            "internal_comments": "All checks passed",
        },
    )
    assert response.status_code == 200

    data = backend.server.v2.store.model.StoreSubmission.model_validate(
        response.json()
    )
    assert data.name == "Reviewed Agent"
    assert data.status == prisma.enums.SubmissionStatus.APPROVED
    assert data.reviewer_id == "test-admin-id"

    mock_db_call.assert_called_once_with(
        store_listing_version_id="version-1",
        is_approved=True,
        external_comments="Looks good",
        internal_comments="All checks passed",
        reviewer_id="test-admin-id",
    )


def test_review_submission_error(
    mocker: pytest_mock.MockFixture,
) -> None:
    mock_db_call = mocker.patch(
        "backend.server.v2.store.db.review_store_submission"
    )
    mock_db_call.side_effect = Exception("Database connection failed")

    response = client.post(
        "/admin/submissions/version-1/review",
        json={
            "store_listing_version_id": "version-1",
            "is_approved": False,
            "comments": "Rejected",
        },
    )
    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()
