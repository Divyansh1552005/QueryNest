"""
Is file ka kaam:
- Session-based chat history store karna
- JSON file me persist karna
- Sliding window maintain karna for context awareness

Ye memory RAG ke context ke liye use krunga
"""

import json
from typing import Dict, List

from querynest.utils.paths import get_chat_path


class ChatMemory:
    def __init__(self, session_id: str, window_size: int = 4):
        """
        session_id: current session ka id
        window_size: kitne recent messages yaad rakhne hain
        """
        self.session_id = session_id
        self.window_size = window_size
        self.chat_path = get_chat_path(session_id)

        # Load existing history (agar hai)
        self.history: List[Dict[str, str]] = self._load()

    def _load(self) -> List[Dict[str, str]]:
        """
        chat.json se purani history load karta hai
        """
        if not self.chat_path.exists():
            return []

        with open(self.chat_path, "r") as f:
            return json.load(f)

    def add_user_message(self, message: str):
        self.history.append(
            {
                "role": "user",
                "content": message,
            }
        )
        self._save()

    def add_assistant_message(self, message: str):
        self.history.append(
            {
                "role": "assistant",
                "content": message,
            }
        )
        self._save()

    def _save(self):
        """
        Sliding window apply karke save karta hai
        """
        trimmed = self.history[-self.window_size * 2 :]

        with open(self.chat_path, "w") as f:
            json.dump(trimmed, f, indent=2)

        self.history = trimmed

    def get_context(self) -> str:
        """
        Chat history ko ek string me convert karta hai
        (prompt me inject karne ke liye)
        """
        lines = []
        for msg in self.history:
            role = msg["role"].capitalize()
            lines.append(f"{role}: {msg['content']}")

        return "\n".join(lines)
