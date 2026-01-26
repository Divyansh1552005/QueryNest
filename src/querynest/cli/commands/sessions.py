import json
import shutil

from querynest.utils.hashing import generate_session_id
import typer
from rich.console import Console
from rich.table import Table

from querynest.utils.paths import SESSIONS_DIR

console = Console()

app = typer.Typer()


@app.command("list")
def list_sessions(
    all: bool = typer.Option(False, "--all", help="Show full metadata"),
    recent: bool = typer.Option(False, "--recent", help="Sort by last used (newest first)"),
    oldest: bool = typer.Option(False, "--oldest", help="Sort by created time (oldest first)"),
    name: bool = typer.Option(False, "--name", help="Sort alphabetically by name"),
):
    """List all QueryNest sessions"""

    sort_flags = [recent, oldest, name]
    if sum(sort_flags) > 1:
        typer.secho(
            "Please use only one sorting flag at a time",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if not SESSIONS_DIR.exists():
        typer.secho("No sessions found", fg=typer.colors.YELLOW)
        return

    sessions = []
    for session_dir in SESSIONS_DIR.iterdir():
        meta_path = session_dir / "meta.json"
        if not meta_path.exists():
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            sessions.append(json.load(f))

    if not sessions:
        typer.secho("No sessions found", fg=typer.colors.YELLOW)
        return

    if recent:
        sessions.sort(key=lambda m: m.get("last_used_at", ""), reverse=True)
    elif oldest:
        sessions.sort(key=lambda m: m.get("created_at", ""))
    elif name:
        sessions.sort(key=lambda m: m.get("name", "").lower())

    table = Table(title="QueryNest Sessions")

    table.add_column("Session ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")

    if all:
        table.add_column("Source", style="white")
        table.add_column("Created At", style="magenta")
        table.add_column("Last Used", style="blue")

    for meta in sessions:
        row = [
            meta.get("id", ""),
            meta.get("name", ""),
            meta.get("source_type", "").upper(),
        ]

        if all:
            row.extend([
                meta.get("source", ""),
                meta.get("created_at", ""),
                meta.get("last_used_at", ""),
            ])

        table.add_row(*row)

    console.print(table)


@app.command("delete")
def delete_session(session_id: str = typer.Argument(..., help="Session ID to delete")):
    """Delete a session by session ID"""

    session_path = SESSIONS_DIR / session_id

    if not session_path.exists():
        typer.secho("Session not found", fg=typer.colors.RED)
        raise typer.Exit(1)

    confirm = typer.confirm(f"Are you sure you want to delete session {session_id}?")
    if not confirm:
        typer.secho("Aborted", fg=typer.colors.YELLOW)
        raise typer.Exit()

    shutil.rmtree(session_path)
    typer.secho("Session deleted", fg=typer.colors.GREEN)

@app.command("info")
def session_info(
    session_id: str = typer.Argument(
        None,
        help="Session ID",
    ),
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help="Source used to create the session (web URL or PDF path)",
    ),
):
    
    """
    Show info for a session using either its session ID or the source.
    """
    if not session_id and not source:
        typer.secho(
            "Either SESSION_ID or --source must be provided",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if session_id and source:
        typer.secho(
            "Provide only one of SESSION_ID or --source",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if source:
        session_id = generate_session_id(source)
        if not session_id:
            typer.secho(
                "No session found for given source",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

    session_dir = SESSIONS_DIR / session_id
    meta_path = session_dir / "meta.json"

    if not session_dir.exists():
        typer.secho("Session not found", fg=typer.colors.RED)
        raise typer.Exit(1)

    if not meta_path.exists():
        typer.secho(
            "Metadata not found for this session",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    typer.secho("Session Information", fg=typer.colors.BLUE, bold=True)
    typer.secho("─" * 40, fg=typer.colors.BLUE)

    for key, value in meta.items():
        typer.secho(f"{key}: {value}", fg=typer.colors.WHITE)


@app.command("rename")
def rename_session(
    session_id: str = typer.Argument(..., help="Session ID to rename"),
    new_name: str = typer.Argument(..., help="New name for the session"),
):
    """
    Rename a session.
    """

    session_dir = SESSIONS_DIR / session_id
    meta_path = session_dir / "meta.json"

    if not session_dir.exists():
        typer.secho("Session not found", fg=typer.colors.RED)
        raise typer.Exit(1)

    if not meta_path.exists():
        typer.secho("Metadata not found for this session", fg=typer.colors.RED)
        raise typer.Exit(1)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    old_name = meta.get("name", "Unknown")
    meta["name"] = new_name

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    typer.secho("Session renamed successfully", fg=typer.colors.GREEN)
    typer.secho(f"Old name: {old_name}", fg=typer.colors.WHITE)
    typer.secho(f"New name: {new_name}", fg=typer.colors.WHITE)


@app.command("search")
def search_sessions(
    query: str = typer.Argument(..., help="Search query"),
    source: bool = typer.Option(False, "--source", help="Search in source"),
    type_: bool = typer.Option(False, "--type", help="Search in source type"),
    all_: bool = typer.Option(False, "--all", help="Search everywhere"),
):
    """
    Search sessions by name, source, or type.
    """

    if not SESSIONS_DIR.exists():
        typer.secho("No sessions found", fg=typer.colors.YELLOW)
        return

    matches = []

    for session_dir in SESSIONS_DIR.iterdir():
        meta_path = session_dir / "meta.json"
        if not meta_path.exists():
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        q = query.lower()

        fields = []
        if all_:
            fields = [
                meta.get("name", ""),
                meta.get("source", ""),
                meta.get("source_type", ""),
            ]
        elif source:
            fields = [meta.get("source", "")]
        elif type_:
            fields = [meta.get("source_type", "")]
        else:
            fields = [meta.get("name", "")]

        if any(q in (field or "").lower() for field in fields):
            matches.append(meta)

    if not matches:
        typer.secho("No matching sessions found", fg=typer.colors.YELLOW)
        return

    # Show results in a table
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Session ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")

    for meta in matches:
        table.add_row(
            meta.get("id", ""),
            meta.get("name", ""),
            meta.get("source_type", "").upper(),
        )

    console.print(table)
