from querynest.config.config_loader import load_config, save_config, update_api_key
from querynest.config.config_model import AppConfig
import os
import sys

def setup_if_needed() -> AppConfig:
    # Try existing config file
    config = load_config()
    if config and config.gemini_api_key:
        return config

    # Try environment variable (BEST for Docker)
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        config = AppConfig(gemini_api_key=env_key)
        save_config(config)
        return config

    # Non-interactive environment → fail cleanly
    if not sys.stdin.isatty():
        raise RuntimeError(
            "Gemini API key not found.\n"
            "Set GEMINI_API_KEY environment variable or run interactively."
        )

    # Interactive prompt
    print("Gemini API key not found.")
    api_key = input("Enter your Gemini API key: ").strip()

    if not api_key:
        raise RuntimeError("Empty API key is not allowed.")

    config = AppConfig(gemini_api_key=api_key)
    save_config(config)

    print("API key saved at ~/.querynest/config.json")
    return config

def reset_api_key():
    """
    Prompts user to update Gemini API key
    """
    print("Update Gemini API key")
    new_key = input("Enter new Gemini API key: ").strip()

    update_api_key(new_key)

    print("API key updated successfully")
