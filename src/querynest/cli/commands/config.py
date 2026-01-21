
import typer
from querynest.config.config_loader import update_api_key

app = typer.Typer()


@app.command()
def set_api_key():
    """Update Gemini API key"""
    new_key = typer.prompt("Enter new Gemini API key", hide_input=True)
    update_api_key(new_key)
    typer.secho("API key updated successfully", fg=typer.colors.GREEN)


