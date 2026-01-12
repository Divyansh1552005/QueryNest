"""
Is file ka kaam:
- kisi bhi source (URL / file path / text) se
- ek deterministic session id banana

Same source → same session id
"""

import hashlib


def generate_session_id(source: str) -> str:
    """
    source: YouTube URL / PDF path / website URL

    Returns:
    - sha256 hash (hex string)
    """

    normalized = source.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()
