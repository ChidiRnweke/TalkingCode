"""Planner service with structured output."""
import json
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import structlog

from talkingcode.domain.models import PlannerInput, PlannerOutput, RetrievalFilters, StopRules, ToolGroupPlan, PlannedToolCall
from talkingcode.enums import Area, FileType

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


class IPlannerService(Protocol):
    """Protocol for planner service."""
    
    async def plan(self, input_data: PlannerInput) -> PlannerOutput:
        """Generate a plan for the given question."""
        ...

PLANNER_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "description": "The user's intent"},
        "filters": {
            "type": "object",
            "properties": {
                "areas": {"type": "array", "items": {"type": "string", "enum": [a.value for a in Area]}},
                "languages": {"type": "array", "items": {"type": "string"}},
                "file_types": {"type": "array", "items": {"type": "string", "enum": [ft.value for ft in FileType]}},
                "path_globs": {"type": "array", "items": {"type": "string"}},
                "repo_scopes": {"type": "array", "items": {"type": "string"}},
                "symbol_hints": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["areas", "languages", "file_types", "path_globs", "repo_scopes", "symbol_hints", "tags"],
        },
        "tool_groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "calls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_name": {"type": "string"},
                                "arguments": {"type": "object"},
                                "non_blocking": {"type": "boolean"},
                            },
                            "required": ["tool_name", "arguments"],
                        },
                    },
                    "parallel": {"type": "boolean"},
                },
                "required": ["name", "calls", "parallel"],
            },
        },
        "stop_rules": {
            "type": "object",
            "properties": {
                "max_iterations": {"type": "integer"},
                "max_tools_per_turn": {"type": "integer"},
            },
            "required": ["max_iterations", "max_tools_per_turn"],
        },
    },
    "required": ["intent", "filters", "tool_groups", "stop_rules"],
}


@dataclass(slots=True)
class PlannerService:
    """Planner service with OpenRouter integration."""
    
    openrouter_api_key: str
    default_model: str
    fallback_model: str
    
    async def plan(self, input_data: PlannerInput) -> PlannerOutput:
        """Generate plan with fallback."""
        model = input_data.selected_model or self.default_model
        
        try:
            return await self._try_plan(input_data.question, model)
        except Exception as e:
            logger.warning("Planner failed, retrying", model=model, error=str(e))
            
            # Retry once on same model
            try:
                return await self._try_plan(input_data.question, model)
            except Exception:
                logger.warning("Planner retry failed, falling back", fallback=self.fallback_model)
                # Fallback to gemini-3-flash
                return await self._try_plan(input_data.question, self.fallback_model)
    
    async def _try_plan(self, question: str, model: str) -> PlannerOutput:
        """Attempt to get plan from LLM."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://talkingcode.dev",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a code understanding planner. Analyze the question and create a plan with filters and tool calls.",
                        },
                        {"role": "user", "content": question},
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "planner_output",
                            "strict": True,
                            "schema": PLANNER_SCHEMA,
                        },
                    },
                },
                timeout=30.0,
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            return self._parse_output(parsed)
    
    def _parse_output(self, data: dict[str, Any]) -> PlannerOutput:
        """Parse planner output."""
        filters_data = data.get("filters", {})
        filters = RetrievalFilters(
            areas=[Area(a) for a in filters_data.get("areas", [])],
            languages=filters_data.get("languages", []),
            file_types=[FileType(ft) for ft in filters_data.get("file_types", [])],
            path_globs=filters_data.get("path_globs", []),
            repo_scopes=filters_data.get("repo_scopes", []),
            symbol_hints=filters_data.get("symbol_hints", []),
            tags=filters_data.get("tags", []),
        )
        
        tool_groups = []
        for group_data in data.get("tool_groups", []):
            calls = [
                PlannedToolCall(
                    tool_name=call["tool_name"],
                    arguments=call.get("arguments", {}),
                    non_blocking=call.get("non_blocking", False),
                )
                for call in group_data.get("calls", [])
            ]
            tool_groups.append(ToolGroupPlan(
                name=group_data["name"],
                calls=calls,
                parallel=group_data.get("parallel", False),
            ))
        
        stop_rules_data = data.get("stop_rules", {})
        stop_rules = StopRules(
            max_iterations=stop_rules_data.get("max_iterations", 8),
            max_tools_per_turn=stop_rules_data.get("max_tools_per_turn", 3),
        )
        
        return PlannerOutput(
            intent=data.get("intent", ""),
            filters=filters,
            tool_groups=tool_groups,
            stop_rules=stop_rules,
        )
