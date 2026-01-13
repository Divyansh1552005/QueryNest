from querynest.config.config_loader import load_config, save_config, update_api_key
from querynest.config.config_model import AppConfig


def setup_if_needed() -> AppConfig:
    config = load_config()
    if config:
        return config

    print("Gemini API key not found.")
    api_key = input("Enter your Gemini API key: ").strip()

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
