import json
from querynest.config.config_model import AppConfig
from querynest.utils.paths import CONFIG_PATH, ensure_base_dirs

def load_config() -> AppConfig | None:
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    return AppConfig(**data)

def save_config(config: AppConfig):
    ensure_base_dirs()
    with open(CONFIG_PATH, "w") as f:
        json.dump(config.model_dump(), f, indent=2)

def update_api_key(new_key: str):
    # Preserves existing llm config, only overwrites gemini_api_key
    existing = load_config()
    if existing:
        config = existing.model_copy(update={"gemini_api_key": new_key})
    else:
        config = AppConfig(gemini_api_key=new_key)
    save_config(config)

def update_llm_config(llm_model: str, llm_api_key: str | None):
    existing = load_config()
    if existing:
        config = existing.model_copy(update={"llm_model": llm_model, "llm_api_key": llm_api_key})
    else:
        # Edge case: shouldn't happen since bootstrap ensures gemini key exists first
        raise RuntimeError("Config not found. Run 'querynest config set-api-key' first.")
    save_config(config)