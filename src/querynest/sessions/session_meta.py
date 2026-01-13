"""
Is file ka kaam:
- Session metadata ka structure define karna
- meta.json read/write handle karna
"""

from datetime import datetime
from pydantic import BaseModel
from pathlib import Path
import json


class SessionMeta(BaseModel):
    id: str
    name: str
    source: str
    source_type: str
    created_at: str
    last_used_at: str

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat()


def save_session_meta(session_dir: Path, meta: SessionMeta):
    meta_path = session_dir / "meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta.model_dump(), f, indent=2)


def load_session_meta(session_dir: Path) -> SessionMeta | None:
    meta_path = session_dir / "meta.json"
    if not meta_path.exists():
        return None

    with open(meta_path, "r") as f:
        return SessionMeta(**json.load(f))
