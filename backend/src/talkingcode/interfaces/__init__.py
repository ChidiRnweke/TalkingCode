"""Protocol interfaces."""
from typing import AsyncGenerator, Protocol

from talkingcode.domain.models import (
    DocumentClassificationOutput,
    PlannerOutput,
    ToolExecutionResult,
    WhiteboxEvent,
)
from talkingcode.domain.services import (
    AgentTurnInput,
    DocumentClassificationInput,
    ExecuteToolGroupInput,
    PlannerInput,
)


class IPlannerService(Protocol):
    """Planner service protocol."""
    
    async def plan(self, input_data: PlannerInput) -> PlannerOutput:
        """Generate a plan for the given question."""
        ...


class IDocumentClassifier(Protocol):
    """Document classifier service protocol."""
    
    async def classify(
        self, input_data: DocumentClassificationInput
    ) -> DocumentClassificationOutput:
        """Classify a document."""
        ...


class IToolRegistry(Protocol):
    """Tool registry protocol."""
    
    def get_tool_definitions(self) -> list[dict]:
        """Get tool definitions for OpenRouter."""
        ...
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute a single tool."""
        ...


class IToolExecutor(Protocol):
    """Tool executor protocol."""
    
    async def execute_group(
        self, input_data: ExecuteToolGroupInput
    ) -> list[ToolExecutionResult]:
        """Execute a group of tool calls."""
        ...


class IAgentLoopService(Protocol):
    """Agent loop service protocol."""
    
    async def run_turn(
        self, input_data: AgentTurnInput
    ) -> AsyncGenerator[WhiteboxEvent, None]:
        """Run an agent turn and stream events."""
        ...
