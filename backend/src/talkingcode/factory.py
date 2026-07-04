"""Application factory."""

from dataclasses import dataclass

import structlog
from agents import Tool, function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.config import AppConfig
from talkingcode.controllers.chat_controller import ChatController
from talkingcode.controllers.health_controller import HealthController
from talkingcode.services.agent.agent_service import ChatAgentService
from talkingcode.controllers.ingestion_controller import IngestionController
from talkingcode.repository.conversation_repository import ConversationRepository
from talkingcode.repository.database import get_engine, get_session_maker
from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.repository.health_repository import HealthRepository
from talkingcode.repository.repo_repository import RepoRepository
from talkingcode.services.classification.document_classifier import DocumentClassifier
from talkingcode.services.health_service import ExternalHealthClient, HealthService
from talkingcode.services.ingestion.chunker import LineChunker
from talkingcode.services.ingestion.embedder import OpenRouterEmbedder
from talkingcode.services.ingestion.github_fetcher import GitHubFetcher
from talkingcode.services.ingestion.ingestion_service import IngestionService
from talkingcode.services.tools.project_descriptions_tool import ProjectDescriptionsTool
from talkingcode.services.tools.query_intent import QueryIntentExtractor
from talkingcode.services.tools.read_file_tool import ReadFileTool
from talkingcode.services.tools.retriever_tool import RetrieverTool

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

    def get_health_repository(self) -> HealthRepository:
        """Get health repository."""
        return HealthRepository(self.session)

    def get_document_classifier(self) -> DocumentClassifier:
        """Get document classifier."""
        return DocumentClassifier(
            openrouter_api_key=self.config.openrouter_api_key,
        )

    async def get_agent_tools(self) -> list[Tool]:
        """Get OpenAI Agents SDK tools backed by application services."""
        document_repo = self.get_document_repository()
        repo_repo = self.get_repo_repository()

        repos = await repo_repo.list_all()
        available_repos = [f"{r.owner}/{r.name}" for r in repos]

        retriever = RetrieverTool(
            document_repository=document_repo,
            embedder=self.get_embedder(),
            intent_extractor=QueryIntentExtractor(),
            openrouter_api_key=self.config.openrouter_api_key,
            intent_model=self.config.intent_extraction_model,
            available_repos=available_repos,
        )

        project_descriptions = ProjectDescriptionsTool(
            document_repository=document_repo,
            embedder=self.get_embedder(),
        )

        read_file_tool = ReadFileTool(
            document_repository=document_repo,
            repo_repository=repo_repo,
        )

        async def search_github(query: str) -> dict:
            """Semantic search across indexed GitHub repositories."""
            return await retriever.execute(query=query)

        async def get_project_descriptions(query: str = "") -> dict:
            """Get descriptions and names of indexed GitHub projects."""
            return await project_descriptions.execute(query=query)

        async def read_file(repository: str, file_path: str) -> dict:
            """Read a file from an indexed repository."""
            return await read_file_tool.execute(
                repository=repository,
                file_path=file_path,
            )

        timeout = float(self.config.default_tool_timeout)
        return [
            function_tool(
                search_github,
                name_override="search_github",
                timeout=timeout,
            ),
            function_tool(
                get_project_descriptions,
                name_override="get_project_descriptions",
                timeout=timeout,
            ),
            function_tool(
                read_file,
                name_override="read_file",
                timeout=timeout,
            ),
        ]

    async def get_chat_controller(self) -> "ChatController":
        """Get chat controller."""
        conversation_repo = self.get_conversation_repository()
        agent_service = ChatAgentService(
            tools=await self.get_agent_tools(),
            openrouter_api_key=self.config.openrouter_api_key,
            max_iterations=self.config.max_iterations,
            engine=get_engine(self.config.database_url),
        )

        return ChatController(
            agent_service=agent_service,
            conversation_repository=conversation_repo,
            default_model=self.config.default_model,
        )

    def get_health_service(self) -> HealthService:
        """Get health check service."""
        return HealthService(
            health_repository=self.get_health_repository(),
            config=self.config,
            external_client=ExternalHealthClient(),
        )

    def get_health_controller(self) -> HealthController:
        """Get health controller."""
        return HealthController(health_service=self.get_health_service())

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
        return OpenRouterEmbedder(
            api_key=self.config.openrouter_api_key,
            model=self.config.embedding_model,
            dimensions=self.config.embedding_dimensions,
        )

    def get_ingestion_service(self) -> IngestionService:
        """Get ingestion orchestrator service."""
        engine = get_engine(self.config.database_url)
        session_maker = get_session_maker(engine)
        return IngestionService(
            repo_repository=self.get_repo_repository(),
            document_repository=self.get_document_repository(),
            github_fetcher=self.get_github_fetcher(),
            classifier=self.get_document_classifier(),
            chunker=self.get_chunker(),
            embedder=self.get_embedder(),
            session_maker=session_maker,
        )

    def get_ingestion_controller(self) -> "IngestionController":
        """Get ingestion controller."""

        return IngestionController(
            repo_repository=self.get_repo_repository(),
            ingestion_service=self.get_ingestion_service(),
        )
