"""
This file :
- Session metadata ka structure define karna
- meta.json read/write handle karna
"""

from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel
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
        # timezone-aware UTC datetime
        return datetime.now(timezone.utc).isoformat()


def save_session_meta(session_dir: Path, meta: SessionMeta):
    meta_path = session_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, indent=2)


def load_session_meta(session_dir: Path) -> SessionMeta | None:
    meta_path = session_dir / "meta.json"
    if not meta_path.exists():
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        return SessionMeta(**json.load(f))
