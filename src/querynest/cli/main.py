import typer
import warnings

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
)


from querynest.cli.commands import chat, config, history
from querynest.config.bootstrap import bootstrap
from querynest.cli.commands import sessions

app = typer.Typer(help="QueryNest CLI – Chat with PDFs & Web using RAG")



@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context):
    """
    Show help when no command is provided.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
        
        
        
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
