"""Application factory."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.config import AppConfig
from talkingcode.repository.conversation_repository import ConversationRepository
from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.repository.repo_repository import RepoRepository
from talkingcode.services.agent.agent_loop import AgentLoopService
from talkingcode.services.agent.timeline_repository import TimelineRepository
from talkingcode.services.classification.document_classifier import DocumentClassifier
from talkingcode.services.ingestion.chunker import LineChunker
from talkingcode.services.ingestion.embedder import OpenRouterEmbedder
from talkingcode.services.ingestion.github_fetcher import GitHubFetcher
from talkingcode.services.ingestion.ingestion_service import IngestionService
from talkingcode.services.llm.openrouter_client import OpenRouterClient
from talkingcode.services.planner.planner_service import PlannerService
from talkingcode.services.tools.retriever_tool import RetrieverTool
from talkingcode.services.tools.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from talkingcode.controllers.chat_controller import ChatController
    from talkingcode.controllers.ingestion_controller import IngestionController

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class AppFactory:
    """Factory for assembling application components."""

    session: AsyncSession
    config: AppConfig

    def get_conversation_repository(self) -> ConversationRepository:
        """Get conversation repository."""
        return ConversationRepository(self.session)

    def get_document_repository(self) -> DocumentRepository:
        """Get document repository."""
        return DocumentRepository(self.session)

    def get_timeline_repository(self) -> TimelineRepository:
        """Get timeline repository."""
        return TimelineRepository(self.session)

    def get_document_classifier(self) -> DocumentClassifier:
        """Get document classifier."""
        return DocumentClassifier(
            openrouter_client=self.get_openrouter_client(),
        )

    def get_openrouter_client(self) -> OpenRouterClient:
        """Get OpenRouter SDK client adapter."""
        return OpenRouterClient(api_key=self.config.openrouter_api_key)

    def get_planner_service(self) -> PlannerService:
        """Get planner service."""
        return PlannerService(
            openrouter_client=self.get_openrouter_client(),
            default_model=self.config.default_model,
            fallback_model=self.config.fallback_model,
        )

    async def get_tool_registry(self) -> ToolRegistry:
        """Get tool registry with all tools."""
        document_repo = self.get_document_repository()
        repo_repo = self.get_repo_repository()

        # Fetch available repo names for intent extraction
        repos = await repo_repo.list_all()
        available_repos = [f"{r.owner}/{r.name}" for r in repos]

        retriever = RetrieverTool(
            document_repository=document_repo,
            openrouter_client=self.get_openrouter_client(),
            embedding_model=self.config.embedding_model,
            embedding_dimensions=self.config.embedding_dimensions,
            intent_model=self.config.intent_extraction_model,
            available_repos=available_repos,
        )

        registry = ToolRegistry()
        registry.register_tool(retriever)

        return registry

    async def get_agent_loop_service(self) -> AgentLoopService:
        """Get agent loop service."""
        tool_registry = await self.get_tool_registry()
        timeline_repo = self.get_timeline_repository()

        return AgentLoopService(
            openrouter_client=self.get_openrouter_client(),
            tool_registry=tool_registry,
            timeline_repository=timeline_repo,
            default_model=self.config.default_model,
            max_iterations=self.config.max_iterations,
            max_tools_per_turn=self.config.max_tools_per_turn,
            default_tool_timeout=self.config.default_tool_timeout,
        )

    async def get_chat_controller(self) -> "ChatController":
        """Get chat controller."""
        from talkingcode.controllers.chat_controller import ChatController

        agent_service = await self.get_agent_loop_service()
        timeline_repo = self.get_timeline_repository()
        conversation_repo = self.get_conversation_repository()

        return ChatController(
            agent_service=agent_service,
            timeline_repository=timeline_repo,
            conversation_repository=conversation_repo,
        )

    def get_repo_repository(self) -> RepoRepository:
        """Get repo repository."""
        return RepoRepository(self.session)

    def get_github_fetcher(self) -> GitHubFetcher:
        """Get GitHub file fetcher."""
        return GitHubFetcher(github_token=self.config.github_token)

    def get_chunker(self) -> LineChunker:
        """Get document chunker."""
        return LineChunker()

    def get_embedder(self) -> OpenRouterEmbedder:
        """Get embedding generator."""
        model = self.config.embedding_model
        dimensions = self.config.embedding_dimensions

        if model == "text-embedding-3-small" or model == "openai/text-embedding-3-small":
            model = "openai/text-embedding-3-large"
            dimensions = 3072

        return OpenRouterEmbedder(
            openrouter_client=self.get_openrouter_client(),
            model=model,
            dimensions=dimensions,
        )

    def get_ingestion_service(self) -> IngestionService:
        """Get ingestion orchestrator service."""
        return IngestionService(
            repo_repository=self.get_repo_repository(),
            document_repository=self.get_document_repository(),
            github_fetcher=self.get_github_fetcher(),
            classifier=self.get_document_classifier(),
            chunker=self.get_chunker(),
            embedder=self.get_embedder(),
            database_url=self.config.database_url,
        )

    def get_ingestion_controller(self) -> "IngestionController":
        """Get ingestion controller."""
        from talkingcode.controllers.ingestion_controller import IngestionController

        return IngestionController(
            repo_repository=self.get_repo_repository(),
            ingestion_service=self.get_ingestion_service(),
        )
