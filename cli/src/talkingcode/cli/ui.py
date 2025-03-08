import webbrowser
from typing import List

import typer
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

HELP_TEXTS = {
    "github_pat": """
# Creating a GitHub Personal Access Token (PAT)

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Click "Generate new token"
3. Set a name like "TalkingCode"
4. Set expiration as needed
5. Select repositories you want to analyze
6. Under "Repository permissions", grant:
   - Contents: Read-only
   - Metadata: Read-only

Need to open the GitHub tokens page?
    """,
    "openai_key": """
# Getting your OpenAI API Key

1. Go to OpenAI API Settings
2. Click "Create new secret key"
3. Give it a name like "TalkingCode"
4. Copy the key (you won't see it again!)

Need help accessing your OpenAI dashboard?
    """,
    "database": """
# Choosing a Database

- **SQLite**: Perfect for local development or personal use
  - No setup required
  - Data stored in your home directory
  - Great for trying out TalkingCode

- **PostgreSQL**: Recommended for production use
  - Better performance with large codebases
  - Supports concurrent access
  - Required format: postgresql://user:pass@host:port/dbname
    """,
    "qdrant": """
# Configuring Qdrant Vector Store

- **Local Mode**: 
  - No setup required
  - Data stored in your home directory
  - Perfect for personal use

- **Server Mode**:
  - Better for team usage
  - Supports larger datasets
  - Required format: http://host:port
    """,
}


def show_help(topic: str) -> bool:
    """Show help text and optionally open relevant webpage"""
    console.print(Markdown(HELP_TEXTS[topic]))

    if topic == "github_pat":
        if typer.confirm("Open GitHub tokens page in your browser?"):
            webbrowser.open("https://github.com/settings/tokens?type=beta")
            return True
    elif topic == "openai_key":
        if typer.confirm("Open OpenAI API settings in your browser?"):
            webbrowser.open("https://platform.openai.com/api-keys")
            return True
    return False


def show_options(options: List[str], title: str = "") -> int:
    """Display numbered options and return selected index"""
    if title:
        console.print(f"\n[bold]{title}[/bold]")

    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("Option", style="cyan")

    for i, opt in enumerate(options, 1):
        table.add_row(f"{i}. {opt}")

    console.print(table)
    choice = Prompt.ask(
        "Select an option",
        choices=[str(i) for i in range(1, len(options) + 1)],
        show_choices=False,
    )
    return int(choice) - 1


def show_summary(db_type: str, qdrant_mode: str) -> None:
    """Display configuration summary"""
    summary = Table(title="Configuration Summary", box=box.ROUNDED)
    summary.add_column("Setting", style="cyan")
    summary.add_column("Value", style="green")

    summary.add_row("Database", db_type)
    summary.add_row("Vector Store", qdrant_mode)

    console.print("\n")
    console.print(summary)

    console.print(
        Panel.fit(
            "[green]Setup Complete![/green]\n\n"
            "Next steps:\n"
            "1. Run [bold cyan]talkingcode ingest[/bold cyan] to download and process your repositories\n"
            "2. Run [bold cyan]talkingcode serve[/bold cyan] to start the server\n\n"
            "Need help? Run [bold cyan]talkingcode --help[/bold cyan] for more information",
            title="✨ Success",
            border_style="green",
        )
    )
