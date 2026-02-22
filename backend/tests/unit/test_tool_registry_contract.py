"""Tool registry strict contract tests."""

import asyncio
from dataclasses import dataclass
from typing import Any

import pytest

from talkingcode.domain.models import ExecuteToolGroupInput
from talkingcode.services.tools.tool_registry import ToolRegistry


@dataclass(slots=True)
class _ExampleTool:
    name: str = "example_tool"
    timeout: int = 15

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "description": "Example tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
            },
        }

    async def execute(self, query: str, top_k: int = 10) -> dict[str, Any]:
        return {"query": query, "top_k": top_k}


@dataclass(slots=True)
class _SlowTool:
    name: str = "slow_tool"
    timeout: int = 0

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "description": "Slow tool",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }

    async def execute(self, query: str) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"query": query}


@pytest.mark.asyncio
async def test_execute_group_returns_unknown_tool_error_code() -> None:
    registry = ToolRegistry()

    results = await registry.execute_group(
        ExecuteToolGroupInput(
            group_name="test",
            calls=[{"tool_name": "missing_tool", "arguments": {"query": "hello"}}],
            parallel=False,
        )
    )

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error_code == "unknown_tool"


@pytest.mark.asyncio
async def test_execute_group_rejects_invalid_arguments() -> None:
    registry = ToolRegistry()
    registry.register_tool(_ExampleTool())

    results = await registry.execute_group(
        ExecuteToolGroupInput(
            group_name="test",
            calls=[
                {
                    "tool_name": "example_tool",
                    "arguments": {"query": "hello", "top_k": "10", "extra": "x"},
                }
            ],
            parallel=False,
        )
    )

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error_code == "invalid_tool_arguments"


@pytest.mark.asyncio
async def test_execute_group_enforces_timeout() -> None:
    registry = ToolRegistry()
    registry.register_tool(_SlowTool(), timeout=0)

    results = await registry.execute_group(
        ExecuteToolGroupInput(
            group_name="test",
            calls=[{"tool_name": "slow_tool", "arguments": {"query": "hello"}}],
            parallel=False,
        )
    )

    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error_code == "tool_timeout"
