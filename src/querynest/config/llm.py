from langchain_litellm import ChatLiteLLM
from querynest.config.config_loader import load_config

def get_llm():
    config = load_config()
    if not config:
        raise RuntimeError("Config not found. Run 'querynest config set-api-key' first.")
        
    
    return ChatLiteLLM(
        model=config.llm_model,
        temperature=0,
        max_tokens=4096,
    )
    
