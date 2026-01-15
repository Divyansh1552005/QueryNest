"""
This file: 
- kisi bhi source (URL / file path / text) se
- ek deterministic session id banana jisse aage agr same web, pdf de toh session continue ho sake and we dont need to do ingestion, indexing steps again

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

