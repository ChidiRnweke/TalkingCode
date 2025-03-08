from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import typer
import uvicorn
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn

from talkingcode.backend.main import create_app
from talkingcode.cli.config import CLIConfig, DatabaseType, QdrantMode
from talkingcode.cli.ui import console, show_help, show_options, show_summary
from talkingcode.pipelines.orchestration import download_and_persist_data


class SetupService(Protocol):
    """Service for handling the setup workflow"""

    async def setup(self) -> None:
        """Run the setup process"""
        ...


class IngestionService(Protocol):
    """Service for handling data ingestion"""

    async def ingest(self) -> None:
        """Run the ingestion process"""
        ...


class ServerService(Protocol):
    """Service for handling the server operations"""

    async def serve(self, host: str, port: int) -> None:
        """Start the server"""
        ...


@dataclass(frozen=True, slots=True)
class InteractiveSetupService(SetupService):
    """Interactive CLI setup workflow implementation"""

    async def setup(self) -> None:
        console.print(
            "[bold cyan]TalkingCode Setup[/bold cyan]\n"
            "This wizard will help you set up your GitHub code analysis environment.\n"
        )

        github_token = await self._configure_github()
        openai_key = await self._configure_openai()
        db_config = await self._configure_database()
        qdrant_config = await self._configure_qdrant()

        config = CLIConfig(
            github_token=github_token,
            openai_key=openai_key,
            db_type=db_config["type"],
            db_url=db_config["url"],
            qdrant_mode=qdrant_config["mode"],
            qdrant_url=qdrant_config["url"],
        )

        config.save()
        show_summary(
            "PostgreSQL" if config.db_type == DatabaseType.postgres else "SQLite",
            "Remote Server"
            if config.qdrant_mode == QdrantMode.server
            else "Local Storage",
        )

    async def _configure_github(self) -> str:
        while True:
            console.print("\n[bold]GitHub Configuration[/bold]")
            console.print("We need a GitHub token to access your repositories\n")

            action = show_options(
                [
                    "Enter GitHub token",
                    "Learn how to create a token",
                    "Open GitHub tokens page",
                ]
            )

            if action == 0:
                return typer.prompt("Enter your GitHub personal access token")
            elif action == 1:
                show_help("github_pat")
            else:
                typer.launch("https://github.com/settings/tokens?type=beta")

    async def _configure_openai(self) -> str:
        while True:
            console.print("\n[bold]AI Configuration[/bold]")
            console.print("TalkingCode uses OpenAI's APIs for embeddings and chat\n")

            action = show_options(
                [
                    "Enter OpenAI API key",
                    "Learn how to get an API key",
                    "Open OpenAI dashboard",
                ]
            )

            if action == 0:
                return typer.prompt("Enter your OpenAI API key")
            elif action == 1:
                show_help("openai_key")
            else:
                typer.launch("https://platform.openai.com/api-keys")

    async def _configure_database(self) -> dict:
        console.print("\n[bold]Database Configuration[/bold]")
        show_help("database")

        db_choice = show_options(
            [
                "SQLite (recommended for local development)",
                "PostgreSQL (recommended for production)",
            ]
        )

        db_type = DatabaseType.postgres if db_choice == 1 else DatabaseType.sqlite
        db_url = None

        if db_type == DatabaseType.postgres:
            db_url = typer.prompt("Enter your PostgreSQL connection URL")
            console.print("Example: postgresql://user:pass@localhost:5432/dbname")

        return {"type": db_type, "url": db_url}

    async def _configure_qdrant(self) -> dict:
        console.print("\n[bold]Vector Store Configuration[/bold]")
        show_help("qdrant")

        qdrant_choice = show_options(
            ["Local storage (recommended for personal use)", "Remote Qdrant server"]
        )

        qdrant_mode = QdrantMode.server if qdrant_choice == 1 else QdrantMode.local
        qdrant_url = None

        if qdrant_mode == QdrantMode.server:
            qdrant_url = typer.prompt("Enter your Qdrant server URL")

        return {"mode": qdrant_mode, "url": qdrant_url}


@dataclass(frozen=True, slots=True)
class CLIIngestionService(IngestionService):
    """Service implementation for data ingestion"""

    async def ingest(self) -> None:
        """Run the ingestion pipeline"""
        console.print("\n🚀 [bold]Starting data ingestion[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "Downloading and processing repositories...", total=None
            )
            try:
                config_dir = Path.home() / ".talkingcode"
                load_dotenv(dotenv_path=config_dir / ".env")
                await download_and_persist_data()
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]Error during ingestion:[/red] {str(e)}")
                raise typer.Exit(1)

        console.print(
            "[green]Data ingestion complete![/green]\n"
            "Run [bold]talkingcode serve[/bold] to start using your processed repositories"
        )


@dataclass(frozen=True, slots=True)
class CLIServerService(ServerService):
    """Service implementation for server operations"""

    async def serve(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Start the TalkingCode server"""
        console.print("\n🌟 [bold]Starting TalkingCode server[/bold]\n")

        try:
            config_dir = Path.home() / ".talkingcode"
            load_dotenv(dotenv_path=config_dir / ".env")
            fastapi_app = create_app()
            console.print(f"Server running at http://{host}:{port}")
            uvicorn.run(fastapi_app, host=host, port=port)
        except Exception as e:
            console.print(f"[red]Error starting server:[/red] {str(e)}")
            raise typer.Exit(1)
