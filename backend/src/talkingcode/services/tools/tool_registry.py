"""Tool registry and executor."""
import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

import structlog

from talkingcode.domain.models import ToolExecutionResult
from talkingcode.domain.services import ExecuteToolGroupInput

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

ToolFunction = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


@dataclass(slots=True)
class ToolRegistry:
    """Registry for tool definitions."""
    
    _tools: dict[str, ToolFunction] = None
    _schemas: dict[str, dict] = None
    _timeouts: dict[str, int] = None
    
    def __post_init__(self):
        if self._tools is None:
            self._tools = {}
        if self._schemas is None:
            self._schemas = {}
        if self._timeouts is None:
            self._timeouts = {}
    
    def register_tool(
        self,
        tool_instance: Any,
        timeout: int = 15,
    ) -> None:
        """Register a tool."""
        tool_name = getattr(tool_instance, 'name', tool_instance.__class__.__name__)
        self._tools[tool_name] = tool_instance.execute
        self._schemas[tool_name] = getattr(tool_instance, 'schema', {})
        self._timeouts[tool_name] = getattr(tool_instance, 'timeout', timeout)
    
    def get_tool_definitions(self) -> list[dict]:
        """Get tool definitions for OpenRouter."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": schema.get("description", ""),
                    "parameters": schema.get("parameters", {}),
                },
            }
            for name, schema in self._schemas.items()
        ]
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute a single tool."""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return await self._tools[tool_name](**arguments)
    
    async def execute_group(
        self,
        input_data: ExecuteToolGroupInput,
    ) -> list[ToolExecutionResult]:
        """Execute a group of tool calls."""
        results = []
        
        async def execute_single(
            call_id: str,
            tool_name: str,
            arguments: dict,
            non_blocking: bool,
        ) -> ToolExecutionResult:
            import time
            import json
            
            start = time.time()
            try:
                result = await self.execute_tool(tool_name, arguments)
                duration_ms = int((time.time() - start) * 1000)
                
                return ToolExecutionResult(
                    call_id=call_id,
                    tool_name=tool_name,
                    success=True,
                    payload_json=json.dumps(result),
                    duration_ms=duration_ms,
                )
            except asyncio.TimeoutError:
                duration_ms = int((time.time() - start) * 1000)
                return ToolExecutionResult(
                    call_id=call_id,
                    tool_name=tool_name,
                    success=False,
                    payload_json="{}",
                    duration_ms=duration_ms,
                    error="Tool execution timeout",
                )
            except Exception as e:
                duration_ms = int((time.time() - start) * 1000)
                return ToolExecutionResult(
                    call_id=call_id,
                    tool_name=tool_name,
                    success=False,
                    payload_json="{}",
                    duration_ms=duration_ms,
                    error=str(e),
                )
        
        if input_data.parallel:
            # Execute in parallel with TaskGroup
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(execute_single(
                        f"{input_data.group_name}_{i}",
                        call["tool_name"],
                        call.get("arguments", {}),
                        call.get("non_blocking", False),
                    ))
                    for i, call in enumerate(input_data.calls)
                ]
            
            results = [t.result() for t in tasks]
        else:
            # Execute sequentially
            for i, call in enumerate(input_data.calls):
                result = await execute_single(
                    f"{input_data.group_name}_{i}",
                    call["tool_name"],
                    call.get("arguments", {}),
                    call.get("non_blocking", False),
                )
                results.append(result)
                
                # Stop on failure unless non-blocking
                if not result.success and not call.get("non_blocking", False):
                    break
        
        return results
