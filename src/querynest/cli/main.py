import typer
from querynest.cli.commands import chat, config, history
from querynest.config.bootstrap import bootstrap
from querynest.cli.commands import sessions

app = typer.Typer(help="QueryNest CLI – Chat with PDFs & Web using RAG")

# register subcommands
app.add_typer(chat.app, name="chat", help="Chat with a PDF or Web page")
app.add_typer(config.app, name="config", help="Manage configuration")
app.add_typer(history.app, name="history", help="View chat history")
app.add_typer(sessions.app, name="sessions", help="Manage sessions")


def main():
    # ensure API key + base dirs
    bootstrap()
    app()


if __name__ == "__main__":
    main()
