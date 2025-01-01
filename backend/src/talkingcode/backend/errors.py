from contextlib import contextmanager
from functools import update_wrapper
from typing import Callable, Generic, ParamSpec, Type, TypeVar

from structlog import getLogger

P = ParamSpec("P")
T = TypeVar("T")
log = getLogger("talkingcode")


class AppError(Exception):
    """Base class for exceptions in this module.
    The strategy for handling errors is similar to the error enum pattern in Rust
    and Scala. The idea is to have a single error type that can be used to represent
    all the different types of errors that can occur in the application.

    For example, if an error occurs in the infrastructure layer, we can raise an
    InfraError. If the maximum spend for the day has been reached, we can raise a
    MaximumSpendError. If the input provided by the user is invalid, we can raise an
    InputError.

    This allows us to handle a single error type in the application layer, which makes
    it easier to reason about the error handling logic and to provide a consistent
    error handling experience to the user.

    FastAPI provides a way to handle exceptions globally using the exception handler
    middleware. We can use this middleware to catch the AppError and return an
    appropriate response to the user.

    In practice this pattern doesn't come to life in Python as it does in Rust or Scala
    because there is no real sum type, it is mimicked with inheritance but we can't force
    exhaustive pattern matching to handle all cases this way.
    """


class InfraError(AppError):
    """
    This error is raised when an error occurs in the infrastructure layer. In practice,
    these are errors that are out of the control of the application code, such as
    network errors, database errors, etc.
    """


class MaximumSpendError(AppError):
    """Raised when the maximum spend for the day has been reached.
    The maximum spend is configurable through the `MAX_SPEND` environment variable.

    """


class InputError(AppError):
    """Raised when the input provided by the user is invalid. These are cases
    that are not caught by the validation logic in the API layer (Pydantic models).
    """


class AppStartupError(Exception):
    """Raised when an error occurs during the application startup.
    This can be used to handle errors that occur during the application initialization
    such as reading secrets, connecting to the database, etc.
    """


class TokenLimitError(Exception):
    """
    Raised when a question is asked that would exceed the token limit.
    """


P = ParamSpec("P")
T = TypeVar("T")


class MapErrors(Generic[P, T]):
    def __init__(self, func: Callable[P, T], map_to: Type[AppError] = InfraError):
        self._func = func
        self._map_to = map_to
        update_wrapper(self, func)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return self._func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in {self._func.__qualname__}: {e}", exc_info=True)
            raise self._map_to() from e


@contextmanager
def map_errors(map_to: Type[AppError] = InfraError):
    """A context manager that catches exceptions, logs them and raises them as AppError.
    Ideally, this context manager should be used in the infrastructure layer to catch
    exceptions and raise them as an AppError. This allows us to handle all errors in
    a consistent way and provide a better error handling experience to the user.

    This should have been a decorator but I gave up on it because of the type hinting
    complexity.

    Args:
        map_to (Type[AppError], optional): The type you want to map it to.
            Defaults to InfraError.

    Raises:
        (AppError): The exception mapped to the type specified in the `map_to` parameter.
    """
    try:
        yield
    except Exception as e:
        log.error(f"Error in: {e}", exc_info=True)
        raise map_to() from e
