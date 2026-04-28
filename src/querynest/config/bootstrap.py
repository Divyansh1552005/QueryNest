"""
Why this file : 
- App start hote hi ensure karna ki Gemini API key available ho
- First run pe user se API key lena
- GOOGLE_API_KEY environment variable set karna
Ye file sirf ek baar call hoti hai (app startup pe)
"""
import os
import sys
from querynest.config.setup import setup_if_needed

def _is_help_or_empty_command() -> bool:
    argv = sys.argv[1:]
    if not argv:
        return True
    if "--help" in argv or "-h" in argv:
        return True
    return False

def bootstrap():
    """
    1. Check karta hai ki config.json exist karta hai ya nahi
    2. Agar nahi karta → user se API key input leta hai
    3. Gemini API key ko environment variable me set karta hai
    4. Agar non-Gemini LLM configured hai → uski API key bhi env me set karta hai
    """
    if _is_help_or_empty_command():
        return

    config = setup_if_needed()

    # Embeddings ke liye — hamesha chahiye
    os.environ["GOOGLE_API_KEY"] = config.gemini_api_key

    # LLM ke liye — sirf tab set karo jab non-Gemini model ho aur key available ho
    if not config.llm_model.startswith("gemini/") and config.llm_api_key:
        provider = config.llm_model.split("/")[0].upper()
        env_key = f"{provider}_API_KEY"  # e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY
        os.environ[env_key] = config.llm_api_key