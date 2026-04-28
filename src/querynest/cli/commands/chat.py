from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

# from querynest.config.gemini import get_llm
from querynest.config.llm import get_llm  
from querynest.loaders.pdf_loader import load_pdfs
from querynest.loaders.web_loader import load_web_page
from querynest.memory.chat_memory import ChatMemory
from querynest.processor.text_splitter import split_documents
from querynest.rag.rag_chain import build_rag_chain
from querynest.config.config_loader import load_config
from querynest.sessions.session_meta import (
    SessionMeta,
    load_session_meta,
    save_session_meta,
)
from querynest.utils.paths import get_session_dir, get_chat_path
from querynest.utils.hashing import generate_session_id
from querynest.utils.paths import get_session_dir
from querynest.vector_store.faiss_store import FaissStore

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    web: Optional[str] = typer.Option(None, "--web", help="Web page URL"),
    pdf: Optional[str] = typer.Option(None, "--pdf", help="PDF file or directory path"),
    force: bool = typer.Option(False, "--force", help="Force re-index even if session exists"),
):
    """
    Start a chat session with a web page or PDF.
    """

    # If a subcommand is invoked, don't run this
    if ctx.invoked_subcommand is not None:
        return

    if not web and not pdf:
        typer.secho("Error: Please provide --web or --pdf", fg=typer.colors.RED)
        typer.echo("\nExamples:")
        typer.echo('querynest chat --web "https://example.com"')
        typer.echo('querynest chat --pdf "/path/to/file.pdf"')
        raise typer.Exit(1)

    if web and pdf:
        typer.secho("Error: Use only one source at a time", fg=typer.colors.RED)
        raise typer.Exit(1)

    source_type = "web" if web else "pdf"
    source_key = web if web else pdf

    typer.secho(f"Source: {source_key[:80]}...", fg=typer.colors.BLUE)

    session_id = generate_session_id(source_key)
    session_dir = get_session_dir(session_id)
    
    typer.secho("Using Embeddings: Google Gemini (text-embedding-004)", fg=typer.colors.MAGENTA)
    store = FaissStore()
    resumed = store.load(session_id)
    
    # force flag - suppose if the same web page has been updated etc so user can force it
    if resumed and force:
        typer.secho("Force flag detected — rebuilding index...", fg=typer.colors.YELLOW)
        resumed = False
        # Chat history bhi clear karo
        chat_path = get_chat_path(session_id)
        if chat_path.exists():
                chat_path.unlink()
        resumed = False

    if not resumed:
        # NEW SESSION - Ask for name
        typer.echo()
        session_name = typer.prompt(
            "Enter a name for this session (optional, press Enter to use default)",
            default="",
            show_default=False,
        ).strip()

        # Use default name if user didn't provide one
        if not session_name:
            if source_type == "pdf":
                # Use filename or directory name
                session_name = source_key.rstrip("/").split("/")[-1]
            else:
                # Use first 50 chars of URL
                session_name = source_key[:50]

        typer.secho(f"\nSession name: {session_name}", fg=typer.colors.BLUE)
        typer.secho("Loading documents...", fg=typer.colors.CYAN)

        if source_type == "web":
            documents = [load_web_page(source_key)]
        else:
            documents = load_pdfs(source_key)

        typer.secho("Splitting into chunks...", fg=typer.colors.CYAN)
        chunks = split_documents(documents)

        typer.secho(
            f"Building vector index ({len(chunks)} chunks)...", fg=typer.colors.CYAN
        )
        store.build(chunks, session_id)

        meta = SessionMeta(
            id=session_id,
            name=session_name,
            source=source_key,
            source_type=source_type,
            created_at=SessionMeta.now(),
            last_used_at=SessionMeta.now(),
        )
        save_session_meta(session_dir, meta)
        typer.secho("New session created", fg=typer.colors.GREEN)
    else:
        # resumed session case - Load and display existing name
        existing_meta = load_session_meta(session_dir)

        if existing_meta:
            # Update last_used_at timestamp
            existing_meta.last_used_at = SessionMeta.now()
            save_session_meta(session_dir, existing_meta)

            typer.secho("Resuming existing session", fg=typer.colors.GREEN)
            typer.secho(f"Session name: {existing_meta.name}", fg=typer.colors.BLUE)
            typer.secho(
                f"Source type: {existing_meta.source_type.upper()}",
                fg=typer.colors.BLUE,
            )
        else:
            typer.secho(
                "Resuming existing session (metadata not found)", fg=typer.colors.YELLOW
            )

    memory = ChatMemory(session_id)
    retriever = store.get_retriever()
    llm = get_llm()
    config = load_config()
    typer.secho(f"Using LLM: {config.llm_model}", fg=typer.colors.MAGENTA)
    rag_chain = build_rag_chain(llm, retriever)

    typer.secho(
        "\nChat started! (type 'exit' or 'quit' to end)\n",
        fg=typer.colors.YELLOW,
        bold=True,
    )

    try:
        while True:
            question = typer.prompt("You")

            if question.lower().strip() in {"exit", "quit"}:
                typer.echo("\nGoodbye!")
                break

            if not question.strip():
                continue

            memory.add_user_message(question)
            context = memory.get_context()

            final_query = f"{context}\nUser: {question}"

            # Done without streaming (older implementation )
            # typer.secho("Thinking...", fg=typer.colors.CYAN)

            # answer = rag_chain.invoke(final_query)

            # console.print("\n[bold green]Assistant[/bold green]")
            # console.print(Markdown(answer))
            # console.print()  # spacing
            
            typer.secho("Thinking...", fg=typer.colors.CYAN)
            
            console.print("\n[bold green]Assistant[/bold green]")
            answer = ""
            for chunk in rag_chain.stream(final_query):
                print(chunk, end="", flush=True)
                answer += chunk
            console.print("\n")  # newline at end
            
            
            
            memory.add_assistant_message(answer)
    except (KeyboardInterrupt, EOFError):
        typer.echo("\n\nSession saved. Goodbye!")
