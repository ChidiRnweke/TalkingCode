"""Tool registry and executor."""
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Protocol

import structlog

from talkingcode.domain.models import ToolExecutionResult, ExecuteToolGroupInput

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

ToolFunction = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


class ToolContractError(Exception):
    """Tool contract validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class IToolRegistry(Protocol):
    """Protocol for tool registry."""
    
    def register_tool(self, tool_instance: Any, timeout: int = 15) -> None:
        """Register a tool."""
        ...
    
    def get_tool_definitions(self) -> list[dict]:
        """Get tool definitions for OpenRouter."""
        ...
    
    async def execute_group(self, input_data: ExecuteToolGroupInput) -> list[ToolExecutionResult]:
        """Execute a group of tool calls."""
        ...


class IToolExecutor(Protocol):
    """Protocol for tool executor."""
    
    async def execute_group(self, input_data: ExecuteToolGroupInput) -> list[ToolExecutionResult]:
        """Execute a group of tool calls with parallel/sequential handling."""
        ...


@dataclass(slots=True)
class ToolRegistry:
    """Registry for tool definitions."""
    
    _tools: dict[str, ToolFunction] = field(default_factory=dict)
    _schemas: dict[str, dict] = field(default_factory=dict)
    _timeouts: dict[str, int] = field(default_factory=dict)
    
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
            raise ToolContractError("unknown_tool", f"Unknown tool: {tool_name}")

        self._validate_tool_arguments(tool_name, arguments)

        return await self._tools[tool_name](**arguments)

    def _validate_tool_arguments(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Validate tool call arguments against registered schema."""
        schema = self._schemas.get(tool_name, {})
        parameters = schema.get("parameters", {})

        if not parameters:
            return

        self._validate_value_against_schema(
            value=arguments,
            schema=parameters,
            path="arguments",
            strict_unknown=True,
        )

    def _validate_value_against_schema(
        self,
        *,
        value: Any,
        schema: dict[str, Any],
        path: str,
        strict_unknown: bool,
    ) -> None:
        expected_type = schema.get("type")

        if expected_type == "object":
            if not isinstance(value, dict):
                raise ToolContractError(
                    "invalid_tool_arguments",
                    f"{path} must be an object",
                )

            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for key in required:
                if key not in value:
                    raise ToolContractError(
                        "invalid_tool_arguments",
                        f"Missing required argument: {path}.{key}",
                    )

            if strict_unknown or schema.get("additionalProperties") is False:
                unknown_keys = [k for k in value if k not in properties]
                if unknown_keys:
                    raise ToolContractError(
                        "invalid_tool_arguments",
                        f"Unknown argument(s): {', '.join(f'{path}.{k}' for k in unknown_keys)}",
                    )

            for key, child_schema in properties.items():
                if key in value:
                    self._validate_value_against_schema(
                        value=value[key],
                        schema=child_schema,
                        path=f"{path}.{key}",
                        strict_unknown=True,
                    )
            return

        if expected_type == "array":
            if not isinstance(value, list):
                raise ToolContractError(
                    "invalid_tool_arguments",
                    f"{path} must be an array",
                )

            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for idx, item in enumerate(value):
                    self._validate_value_against_schema(
                        value=item,
                        schema=item_schema,
                        path=f"{path}[{idx}]",
                        strict_unknown=True,
                    )
            return

        if expected_type == "string" and not isinstance(value, str):
            raise ToolContractError("invalid_tool_arguments", f"{path} must be a string")

        if expected_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            raise ToolContractError("invalid_tool_arguments", f"{path} must be an integer")

        if expected_type == "number" and (
            (not isinstance(value, (int, float))) or isinstance(value, bool)
        ):
            raise ToolContractError("invalid_tool_arguments", f"{path} must be a number")

        if expected_type == "boolean" and not isinstance(value, bool):
            raise ToolContractError("invalid_tool_arguments", f"{path} must be a boolean")
    
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
                timeout_seconds = self._timeouts.get(tool_name, input_data.timeout_seconds)
                result = await asyncio.wait_for(
                    self.execute_tool(tool_name, arguments),
                    timeout=timeout_seconds,
                )
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
                    error_code="tool_timeout",
                )
            except ToolContractError as e:
                duration_ms = int((time.time() - start) * 1000)
                return ToolExecutionResult(
                    call_id=call_id,
                    tool_name=tool_name,
                    success=False,
                    payload_json="{}",
                    duration_ms=duration_ms,
                    error=str(e),
                    error_code=e.code,
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
                    error_code="tool_execution_error",
                )
        
        if input_data.parallel:
            # Execute in parallel with TaskGroup
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(execute_single(
                        call.get("call_id", f"{input_data.group_name}_{i}"),
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
                    call.get("call_id", f"{input_data.group_name}_{i}"),
                    call["tool_name"],
                    call.get("arguments", {}),
                    call.get("non_blocking", False),
                )
                results.append(result)
                
                # Stop on failure unless non-blocking
                if not result.success and not call.get("non_blocking", False):
                    break
        
        return results
