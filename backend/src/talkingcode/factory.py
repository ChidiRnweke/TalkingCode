"""Application factory."""
from dataclasses import dataclass
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.config import AppConfig
from talkingcode.repository.conversation_repository import ConversationRepository
from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.services.agent.agent_loop import AgentLoopService
from talkingcode.services.agent.timeline_repository import TimelineRepository
from talkingcode.services.classification.document_classifier import DocumentClassifier
from talkingcode.services.planner.planner_service import PlannerService
from talkingcode.services.tools.retriever_tool import RetrieverTool
from talkingcode.services.tools.tool_registry import ToolRegistry

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
            openai_api_key=self.config.openai_api_key,
        )
    
    def get_planner_service(self) -> PlannerService:
        """Get planner service."""
        return PlannerService(
            openrouter_api_key=self.config.openrouter_api_key,
            default_model=self.config.default_model,
            fallback_model=self.config.fallback_model,
        )
    
    def get_tool_registry(self) -> ToolRegistry:
        """Get tool registry with all tools."""
        document_repo = self.get_document_repository()
        retriever = RetrieverTool(document_repo)
        
        registry = ToolRegistry()
        registry.register_tool(retriever)
        
        return registry
    
    def get_agent_loop_service(self) -> AgentLoopService:
        """Get agent loop service."""
        planner = self.get_planner_service()
        tool_registry = self.get_tool_registry()
        timeline_repo = self.get_timeline_repository()
        
        return AgentLoopService(
            planner=planner,
            tool_registry=tool_registry,
            timeline_repository=timeline_repo,
            max_iterations=self.config.max_iterations,
            max_tools_per_turn=self.config.max_tools_per_turn,
            default_tool_timeout=self.config.default_tool_timeout,
        )
    
    def get_chat_controller(self) -> "ChatController":
        """Get chat controller."""
        from talkingcode.controllers.chat_controller import ChatController
        
        agent_service = self.get_agent_loop_service()
        timeline_repo = self.get_timeline_repository()
        conversation_repo = self.get_conversation_repository()
        
        return ChatController(
            agent_service=agent_service,
            timeline_repository=timeline_repo,
            conversation_repository=conversation_repo,
            config=self.config,
        )
