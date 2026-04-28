from querynest.config.config_loader import load_config, save_config, update_api_key, update_llm_config
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
    """Prompts user to update Gemini API key"""
    print("Update Gemini API key")
    new_key = input("Enter new Gemini API key: ").strip()
    update_api_key(new_key)
    print("API key updated successfully")

def set_llm_config():
    """
    Prompts user to select LLM from curated list or enter custom model string.
    Called from 'querynest config set-llm'
    """
    MODELS = [
        {"label": "Gemini 2.5 Flash (default)", "model": "gemini/gemini-2.5-flash", "provider": "gemini"},
        {"label": "OpenAI - GPT-4o",             "model": "openai/gpt-4o",            "provider": "openai"},
        {"label": "OpenAI - GPT-4o Mini",         "model": "openai/gpt-4o-mini",       "provider": "openai"},
        {"label": "Anthropic - Claude Sonnet",    "model": "anthropic/claude-sonnet-4-5", "provider": "anthropic"},
        {"label": "Groq - Llama 3.3 70B",         "model": "groq/llama-3.3-70b-versatile", "provider": "groq"},
        {"label": "Mistral - Large",              "model": "mistral/mistral-large-latest", "provider": "mistral"},
        {"label": "Enter custom model string",    "model": None,                        "provider": None},
    ]

    print("\nSelect LLM model:")
    for i, m in enumerate(MODELS, 1):
        print(f"  {i}. {m['label']}")

    choice = input("\nEnter number: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(MODELS)):
        raise RuntimeError("Invalid choice.")

    selected = MODELS[int(choice) - 1]

    # Custom model string
    if selected["model"] is None:
        model_str = input("Enter model string (e.g. groq/llama-3.1-8b-instant): ").strip()
        if not model_str or "/" not in model_str:
            raise RuntimeError("Invalid model string. Format should be 'provider/model-name'.")
        selected_model = model_str
        provider = model_str.split("/")[0]
    else:
        selected_model = selected["model"]
        provider = selected["provider"]

    # Gemini as LLM → reuse existing gemini_api_key, no need for separate key
    if provider == "gemini":
        update_llm_config(llm_model=selected_model, llm_api_key=None)
        print(f"LLM set to: {selected_model}")
        print("Using existing Gemini API key for LLM.")
        return

    # Non-interactive check
    if not sys.stdin.isatty():
        raise RuntimeError(
            f"API key for {provider} not found.\n"
            f"Set the key interactively or via environment variable."
        )

    api_key = input(f"Enter API key for {provider}: ").strip()
    if not api_key:
        raise RuntimeError("Empty API key is not allowed.")

    update_llm_config(llm_model=selected_model, llm_api_key=api_key)
    print(f"LLM set to: {selected_model}")
    print(f"API key for {provider} saved.")