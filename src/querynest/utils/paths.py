"""
this file will : 
- ~/.querynest ke andar saare paths manage karna
- directories automatically create karna on start
"""

from pathlib import Path

# Base directory for QueryNest ie we will save it in user's home directory as a hidden folder .querynest
BASE_DIR = Path.home() / ".querynest"

# Config file path ie config file that will save the api keys
CONFIG_PATH = BASE_DIR / "config.json"

# Sessions parent directory ie it will store each sessions meta data, chat data in json files as well as faiss index so we can resume sessions.
# iska ye fayda hoga ki baar baar index nahi banana pdega ya page load nahi krna pdega 
SESSIONS_DIR = BASE_DIR / "sessions"


def ensure_base_dirs():
    """
    Agar ~/.querynest ya sessions folder exist nahi karta
    toh automatically create kar de
    """
    BASE_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)


def get_session_dir(session_id: str) -> Path:
    """
    Har session ke liye alag folder jisme chats store karke rakhenge , unka meta data, faiss index etc
    ~/.querynest/sessions/<session_id>/
    """
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_faiss_path(session_id: str) -> Path:
    """
    FAISS index file ka path
    """
    return get_session_dir(session_id) / "vectors.faiss"


def get_chat_path(session_id: str) -> Path:
    """
    Chat history ka path
    """
    return get_session_dir(session_id) / "chat.json"


