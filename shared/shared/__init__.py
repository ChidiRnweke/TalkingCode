from shared import database
from shared import log
from dotenv import load_dotenv


def setup_env(logger_name: str) -> None:
    logger = log.setup_custom_logger(logger_name)
    found = load_dotenv("../config/.env.secret")
    if not found:
        logger.warning("No .env file found")


__all__ = ["database", "log", "setup_env"]
