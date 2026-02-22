"""Unit tests for ingestion authentication."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from talkingcode.app import create_app
from talkingcode.config import AppConfig
from talkingcode.dependencies import get_config, get_factory
from talkingcode.domain.models import IngestionStatus, RepositoryInfo, IngestionRunInfo


@pytest.fixture
def mock_config():
    """Mock application configuration."""
    config = MagicMock(spec=AppConfig)
    config.ingestion_api_key = "secret-key"
    return config


@pytest.fixture
def mock_factory():
    """Mock application factory."""
    factory = MagicMock()
    
    # Ingestion Controller
    ingestion_controller = MagicMock()
    factory.get_ingestion_controller.return_value = ingestion_controller
    
    # Chat Controller
    chat_controller = MagicMock()
    factory.get_chat_controller.return_value = chat_controller
    
    # Mock return values for ingestion controller methods
    now = datetime.now(timezone.utc)
    
    repo = RepositoryInfo(
        id=1,
        provider="github",
        owner="test-owner",
        name="test-repo",
        default_branch="main",
        last_ingested_at=None,
        created_at=now,
    )
    ingestion_controller.register_repo = AsyncMock(return_value=repo)
    ingestion_controller.get_repo = AsyncMock(return_value=repo)
    ingestion_controller.list_repos = AsyncMock(return_value=[repo])
    
    run = IngestionRunInfo(
        id=1,
        repository_id=1,
        status=IngestionStatus.RUNNING,
        started_at=now,
        completed_at=None,
        error_message=None,
    )
    ingestion_controller.start_ingestion = AsyncMock(return_value=run)
    ingestion_controller.start_owned_repo_ingestion = AsyncMock(return_value=[run])
    ingestion_controller.list_ingestion_runs = AsyncMock(return_value=[run])
    
    return factory


@pytest.fixture
def client(mock_config, mock_factory):
    """Test client with mocked dependencies."""
    app = create_app()
    app.dependency_overrides[get_config] = lambda: mock_config
    app.dependency_overrides[get_factory] = lambda: mock_factory
    # Mock DB session for chat routes that require it
    from talkingcode.dependencies import get_db_session
    app.dependency_overrides[get_db_session] = lambda: MagicMock()
    return TestClient(app)


def test_public_routes_allow_anonymous(client):
    """Test that public routes allow anonymous access."""
    routes = [
        ("GET", "/repos"),
        ("GET", "/repos/test-owner/test-repo"),
        ("GET", "/repos/test-owner/test-repo/runs"),
        ("GET", "/health"),
    ]
    
    for method, path in routes:
        resp = client.request(method, path)
        assert resp.status_code == 200, f"{method} {path} should be 200 (public)"

    # Chat routes should not fail with 401 Ingestion key error
    # They might fail with 422 (validation) or 500 (other mocks), but NOT 401
    # Actually, if we mock correctly they might return 200 or 500.
    # We just want to ensure NO ingestion auth dependency is triggered.
    
    # We can check that the ingestion auth dependency is NOT in the dependencies for these routes.
    # But integration test is better: call it and ensure it doesn't ask for key.
    
    # POST /chat/agentic requires body
    resp = client.post("/chat/agentic", json={"question": "hi"})
    assert resp.status_code != 401, "/chat/agentic should not require ingestion key"
    
    # GET /chat/timeline requires query param
    resp = client.get("/chat/timeline?conversation_id=123e4567-e89b-12d3-a456-426614174000")
    assert resp.status_code != 401, "/chat/timeline should not require ingestion key"


def test_protected_routes_require_auth(client):
    """Test that protected routes require authentication."""
    routes = [
        ("POST", "/repos", {"owner": "o", "name": "n"}),
        ("POST", "/repos/o/n/ingest", {}),
        ("POST", "/repos/ingest-owned", {}),
    ]

    for method, path, json_body in routes:
        # 1. No key
        resp = client.request(method, path, json=json_body)
        assert resp.status_code == 401, f"{method} {path} should be 401 without key"
        
        # 2. Wrong key via Header
        resp = client.request(method, path, json=json_body, headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401, f"{method} {path} should be 401 with wrong key"
        
        # 3. Wrong key via Query
        char = "&" if "?" in path else "?"
        resp = client.request(method, f"{path}{char}api_key=wrong", json=json_body)
        assert resp.status_code == 401, f"{method} {path} should be 401 with wrong key"


def test_protected_routes_accept_valid_key(client):
    """Test that protected routes accept valid authentication."""
    routes = [
        ("POST", "/repos", {"owner": "test-owner", "name": "test-repo"}),
        ("POST", "/repos/test-owner/test-repo/ingest", {}),
        ("POST", "/repos/ingest-owned", {}),
    ]

    for method, path, json_body in routes:
        # 1. Correct Header
        resp = client.request(method, path, json=json_body, headers={"X-API-Key": "secret-key"})
        assert resp.status_code == 200, f"{method} {path} failed with header auth: {resp.text}"
        
        # 2. Correct Query
        char = "&" if "?" in path else "?"
        resp = client.request(method, f"{path}{char}api_key=secret-key", json=json_body)
        assert resp.status_code == 200, f"{method} {path} failed with query auth: {resp.text}"
