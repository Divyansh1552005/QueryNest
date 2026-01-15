import json
from querynest.config.config_model import AppConfig
from querynest.utils.paths import CONFIG_PATH, ensure_base_dirs


# will return appConfig object or none
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
    # It overwrites the existing Gemini API key
    config = AppConfig(gemini_api_key=new_key)
    save_config(config)
