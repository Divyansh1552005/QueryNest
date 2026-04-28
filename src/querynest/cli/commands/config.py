import typer
from querynest.config.config_loader import update_api_key
from querynest.config.setup import set_llm_config
from querynest.config.config_loader import load_config, update_llm_config


app = typer.Typer()

@app.command()
def set_gemini_key():
    """Update Gemini API key"""
    new_key = typer.prompt("Enter new Gemini API key", hide_input=True)
    update_api_key(new_key)
    typer.secho("API key updated successfully", fg=typer.colors.GREEN)

@app.command()
def set_llm():
    """Select LLM model (OpenAI, Anthropic, Groq, Mistral, or custom)"""
    try:
        set_llm_config()
    except RuntimeError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def show_models():
    """Show current LLM and embedding model being used"""
    config = load_config()
    if not config:
        typer.secho("Config not found. Run 'querynest config set-api-key' first.", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    typer.secho("\nCurrent Configuration:", fg=typer.colors.YELLOW, bold=True)
    typer.secho("  Embeddings : Google Gemini (text-embedding-004)", fg=typer.colors.MAGENTA)
    typer.secho(f"  LLM        : {config.llm_model}", fg=typer.colors.MAGENTA)
    typer.echo()


@app.command()
def set_llm_key():
    """Update API key for current LLM provider"""
    config = load_config()
    if not config:
        typer.secho("Config not found. Run 'querynest config set-gemini-key' first.", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    if config.llm_model.startswith("gemini/"):
        typer.secho("Current LLM is Gemini — use 'set-gemini-key' instead.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)
    
    provider = config.llm_model.split("/")[0]
    new_key = typer.prompt(f"Enter new API key for {provider}", hide_input=True)
    update_llm_config(llm_model=config.llm_model, llm_api_key=new_key)
    typer.secho(f"API key for {provider} updated successfully", fg=typer.colors.GREEN)