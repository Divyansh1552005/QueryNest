"""
Is file ka kaam:
- ~/.querynest ke andar saare paths manage karna
- directories automatically create karna
"""

from pathlib import Path

# Base directory for QueryNest
BASE_DIR = Path.home() / ".querynest"

# Config file path
CONFIG_PATH = BASE_DIR / "config.json"

# Sessions parent directory
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
    Har session ke liye alag folder

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
    Chat history ka path (v1.5+)
    """
    return get_session_dir(session_id) / "chat.json"


