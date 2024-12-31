import asyncio
import logging
import os

from talkingcode.pipelines.orchestration import run_pipeline_on_schedule
from talkingcode.shared.telemetry import configure_telemetry


async def main() -> None:
    await run_pipeline_on_schedule(00, 00)


if __name__ == "__main__":
    app_logger = logging.getLogger("app_logger")
    app_logger.setLevel(logging.DEBUG)
    if not app_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)

    telemetry_enabled = bool(os.getenv("TELEMETRY_ENABLED"))
    if telemetry_enabled:
        telemetry_endpoint = os.getenv("TELEMETRY_ENDPOINT")
        if not telemetry_endpoint:
            raise ValueError(
                "Telemetry endpoint is required when telemetry is enabled."
            )
        configure_telemetry(telemetry_endpoint)

    asyncio.run(main())
