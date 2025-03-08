from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console

console = Console()


def check_config_exists() -> Tuple[bool, Optional[str]]:
    """Check if configuration exists"""
    config_path = Path.home() / ".talkingcode" / ".env"
    if not config_path.exists():
        return False, "Configuration not found. Please run 'talkingcode setup' first."
    return True, None


def check_database_exists() -> Tuple[bool, Optional[str]]:
    """Check if database exists and has been initialized"""
    config_dir = Path.home() / ".talkingcode"
    sqlite_path = config_dir / "talkingcode.db"

    if not sqlite_path.exists():
        return False, "Database not found. Please run 'talkingcode ingest' first."

    if sqlite_path.stat().st_size < 100:
        return False, "Database appears empty. Please run 'talkingcode ingest' first."

    return True, None


def check_qdrant_exists() -> Tuple[bool, Optional[str]]:
    """Check if Qdrant data exists"""
    config_dir = Path.home() / ".talkingcode"
    qdrant_path = config_dir / "qdrant"

    if not qdrant_path.exists():
        return False, "Vector store not found. Please run 'talkingcode ingest' first."

    # Check if qdrant directory has content
    if not any(qdrant_path.iterdir()):
        return (
            False,
            "Vector store appears empty. Please run 'talkingcode ingest' first.",
        )

    return True, None


def validate_serve_requirements() -> None:
    """Validate all requirements for serve command"""
    checks = [check_config_exists(), check_database_exists(), check_qdrant_exists()]

    for success, message in checks:
        if not success:
            console.print(f"[red]Error:[/red] {message}")
            raise typer.Exit(1)


def validate_ingest_requirements() -> None:
    """Validate requirements for ingest command"""
    success, message = check_config_exists()
    if not success:
        console.print(f"[red]Error:[/red] {message}")
        raise typer.Exit(1)
