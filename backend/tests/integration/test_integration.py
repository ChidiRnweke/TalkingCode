"""Integration tests with testcontainers."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from talkingcode.config import AppConfig
from talkingcode.factory import AppFactory
from talkingcode.models.orm import Base
from talkingcode.repository.conversation_repository import ConversationRepository
from testcontainers.postgres import PostgresContainer


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session using testcontainers."""
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        connection_url = postgres.get_connection_url()

        # Create engine and tables
        engine = create_async_engine(connection_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            yield session

        await engine.dispose()


@pytest_asyncio.fixture
async def app_config():
    """Create test app config."""
    return AppConfig(
        database_url="postgresql+asyncpg://test:test@localhost/test",
        openrouter_api_key="test-key",
        github_token="test-token",
        ingestion_api_key="test-ingestion-key",
        environment="test",
        log_level="DEBUG",
        default_model="test-model",
        fallback_model="fallback-model",
        max_iterations=8,
        max_tools_per_turn=3,
        default_tool_timeout=15,
        embedding_model="test-embedding",
        embedding_dimensions=1536,
        intent_extraction_model="test-intent",
        curated_models="test-curated",
        default_chat_model="test-chat",
        phoenix_base_url="",
        phoenix_api_key="",
        phoenix_project_name="test",
        otel_exporter_endpoint="",
        otel_service_name="test",
        otel_environment="test",
    )


@pytest.mark.asyncio
async def test_factory_creates_components(db_session, app_config):
    """Test that factory creates all components without errors."""
    factory = AppFactory(session=db_session, config=app_config)

    conversation_repo = factory.get_conversation_repository()
    assert conversation_repo is not None

    document_repo = factory.get_document_repository()
    assert document_repo is not None

    chat_controller = await factory.get_chat_controller()
    assert chat_controller is not None


@pytest.mark.asyncio
async def test_repository_crud(db_session):
    """Test repository CRUD operations."""

    repo = ConversationRepository(db_session)

    # Create a turn
    turn = await repo.create_turn(
        conversation_id=None,
        question="Test question",
        selected_model="test-model",
        planner_model_used="test-model",
    )

    assert turn.question == "Test question"
    assert turn.selected_model == "test-model"

    # Get the turn
    retrieved = await repo.get_turn(turn.id)
    assert retrieved is not None
    assert retrieved.question == "Test question"

