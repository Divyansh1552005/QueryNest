import typer
import json
from typing import Optional

from querynest.utils.hashing import generate_session_id
from querynest.utils.paths import get_chat_path

app = typer.Typer()


@app.command()
def show(
    # Optional[str] means it can be optional or a string (optional coz ek devega ne user teeno mein te)
    session_id: Optional[str] = typer.Option(
        None,
        "--session-id",
        help="Session ID"
    ),
    web: Optional[str] = typer.Option(
        None,
        "--web",
        help="Web page URL"
    ),
    
    pdf: Optional[str] = typer.Option(
        None,
        "--pdf",
        help="PDF path"
    ),
):
    """Show chat history using session ID or source"""

    # exactly one source of truth must be provided
    provided = [session_id, web, pdf]
    if sum(x is not None for x in provided) != 1:
        typer.secho(
            "Provide exactly one of --session-id, --web, or --pdf",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if session_id:
        sid = session_id
    else:
        source = web if web else pdf
        sid = generate_session_id(source)

    chat_path = get_chat_path(sid)

    if not chat_path.exists():
        typer.secho("No chat history found", fg=typer.colors.RED)
        raise typer.Exit(1)

    with open(chat_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    for msg in history:
        role = msg["role"].upper()
        color = typer.colors.CYAN if role == "USER" else typer.colors.WHITE
        typer.secho(f"{role}: {msg['content']}", fg=color)
