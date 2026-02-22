"""Error definitions."""
from typing import Any


class TalkingCodeError(Exception):
    """Base application error."""
    
    def __init__(self, message: str, code: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or "unknown_error"
        self.details = details or {}


class ValidationError(TalkingCodeError):
    """Input validation error."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="validation_error", details=details)


class NotFoundError(TalkingCodeError):
    """Resource not found error."""
    
    def __init__(self, message: str, resource_type: str | None = None):
        super().__init__(message, code="not_found", details={"resource_type": resource_type})


class LLMError(TalkingCodeError):
    """LLM API error."""
    
    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message, code="llm_error", details={"provider": provider})


class ToolError(TalkingCodeError):
    """Tool execution error."""
    
    def __init__(self, message: str, tool_name: str | None = None):
        super().__init__(message, code="tool_error", details={"tool_name": tool_name})


class TimeoutError(TalkingCodeError):
    """Operation timeout error."""
    
    def __init__(self, message: str, operation: str | None = None):
        super().__init__(message, code="timeout", details={"operation": operation})


class PlannerError(TalkingCodeError):
    """Planner execution error."""
    
    def __init__(self, message: str):
        super().__init__(message, code="planner_error")
