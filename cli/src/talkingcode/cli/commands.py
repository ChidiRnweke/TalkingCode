import asyncio

from talkingcode.cli.services import (
    CLIIngestionService,
    CLIServerService,
    InteractiveSetupService,
    ServerService,
    SetupService,
)
from talkingcode.cli.validation import (
    validate_ingest_requirements,
    validate_serve_requirements,
)


def setup_command() -> None:
    """Initialize TalkingCode interactively"""
    setup_service: SetupService = InteractiveSetupService()
    asyncio.run(setup_service.setup())


def ingest_command() -> None:
    """Run the data ingestion pipeline"""
    # Validate configuration exists
    validate_ingest_requirements()

    # Run ingestion
    ingestion_service = CLIIngestionService()
    asyncio.run(ingestion_service.ingest())


def serve_command(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the TalkingCode server"""
    # Validate all requirements are met
    validate_serve_requirements()

    # Start server
    server_service: ServerService = CLIServerService()
    asyncio.run(server_service.serve(host, port))
