from src.config.config_loader import load_config, save_config
from src.config.config_model import AppConfig

def setup_if_needed() -> AppConfig:
    config = load_config()
    if config:
        return config

    print("🔐 Gemini API key not found.")
    api_key = input("Enter your Gemini API key: ").strip()

    config = AppConfig(gemini_api_key=api_key)
    save_config(config)

    print("✅ API key saved at ~/.querynest/config.json")
    return config
