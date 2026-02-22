"""Error hierarchy for TalkingCode backend.

Per python-swe conventions:
- Domain errors never contain HTTP status codes
- Error mapping to HTTP responses happens in error_handlers.py only
"""


class AppError(Exception):
    """Base for all domain errors. Never use directly."""


class InputError(AppError):
    """Input validation error."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """Resource not found error."""
    
    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} not found")
        self.resource = resource


class InfraError(AppError):
    """Infrastructure failure (DB down, external API timeout, etc.)."""
    pass


class UnauthorisedError(AppError):
    """Authentication/authorization error."""
    pass


# Keep backward compatibility aliases during migration
TalkingCodeError = AppError
ValidationError = InputError
