class InfraError(Exception):
    def __init__(self, msg: str | None = None) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg or "An error occurred in the infrastructure layer"


class MaximumSpendError(Exception):
    def __init__(self, msg: str | None = None) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg or "The maximum spend for the day has been reached"


class InputError(Exception):
    def __init__(self, msg: str | None = None) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg or "Your input is invalid"
