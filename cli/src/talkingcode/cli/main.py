import typer

from talkingcode.cli.commands import ingest_command, serve_command, setup_command

app = typer.Typer(
    help="TalkingCode - A GitHub code RAG system",
    add_completion=True,
)

app.command(name="setup")(setup_command)
app.command(name="ingest")(ingest_command)
app.command(name="serve")(serve_command)

if __name__ == "__main__":
    app()
