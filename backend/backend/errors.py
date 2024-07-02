from contextlib import contextmanager
from typing import Callable, Generic, ParamSpec, TypeVar, Type
from logging import getLogger
from functools import update_wrapper


P = ParamSpec("P")
T = TypeVar("T")
log = getLogger("backend_logger")


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

    def __init__(self, err: Exception | None) -> None:
        self.original_error = err


class InfraError(AppError):
    """
    This error is raised when an error occurs in the infrastructure layer. In practice,
    these are errors that are out of the control of the application code, such as
    network errors, database errors, etc.
    """

    def __init__(self, err: Exception) -> None:
        super().__init__(err)
        self.msg = "An error occurred in the infrastructure layer"

    def __str__(self) -> str:
        return self.msg


class MaximumSpendError(AppError):
    """Raised when the maximum spend for the day has been reached.
    The maximum spend is configurable through the `MAX_SPEND` environment variable.

    """

    def __init__(self) -> None:
        super().__init__(None)
        self.msg = "The maximum spend for the day has been reached"

    def __str__(self) -> str:
        return self.msg


class InputError(AppError):
    """Raised when the input provided by the user is invalid. These are cases
    that are not caught by the validation logic in the API layer (Pydantic models).
    """

    def __init__(
        self, message: str | None = None, err: Exception | None = None
    ) -> None:
        if message:
            self.msg = message
        else:
            self.msg = "The input you provided is invalid"
        super().__init__(err)

    def __str__(self) -> str:
        return self.msg


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
            raise self._map_to(err=e) from e


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
        raise map_to(err=e) from e
