from typing import Callable, Generic, ParamSpec, TypeVar, Type
from logging import getLogger
from functools import update_wrapper


P = ParamSpec("P")
T = TypeVar("T")
log = getLogger("backend_logger")


class AppError(Exception):
    def __init__(self, err: Exception | None) -> None:
        self.original_error = err


class InfraError(AppError):
    def __init__(self, err: Exception) -> None:
        super().__init__(err)
        self.msg = "An error occurred in the infrastructure layer"

    def __str__(self) -> str:
        return self.msg


class MaximumSpendError(AppError):
    def __init__(self, err: Exception) -> None:
        super().__init__(err)
        self.msg = "The maximum spend for the day has been reached"

    def __str__(self) -> str:
        return self.msg


class InputError(AppError):
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


class map_errors(Generic[P, T]):
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
