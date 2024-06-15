import os
from logging import Logger
from .log import setup_custom_logger

from dotenv import load_dotenv


def setup_env(logger_name: str) -> None:
    logger = setup_custom_logger(logger_name)
    if not os.getenv("PRODUCTION"):
        logger.warning("Running in development mode")
        found = load_dotenv("../config/.env.secret.dev")
        if not found:
            logger.warning("No .env file found")


def env_var_or_default(var_name: str, default: str, log: Logger | None = None) -> str:
    value = os.getenv(var_name)
    if value is None:
        if log is not None:
            log.warning(
                f"{var_name} environment variable is not set. Fallback to default."
            )
        value = default
    return value


def env_var_or_throw(var_name: str, log: Logger | None = None) -> str:
    value = os.getenv(var_name)
    if value is None:
        if log is not None:
            log.error(f"{var_name} environment variable is not set. Cannot start app.")
        raise ValueError(
            f"{var_name} environment variable is not set. Cannot start app."
        )
    return value
