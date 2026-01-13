"""
Is file ka kaam:
- LangChain Community FAISS vector store manage karna
- Session-based save / load support dena
- Retriever provide karna (RAG ke liye)

IMPORTANT:
- Direct faiss import NAHI use kar rahe
- Embeddings LangChain ke through aate hain
"""

from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from querynest.embeddings.embedder import get_embeddings
from querynest.utils.paths import get_session_dir


class FaissStore:
    """
    QueryNest ka FAISS abstraction
    """

    def __init__(self):
        # Gemini embeddings (LangChain wrapper)
        self.embeddings = get_embeddings()

        # Actual FAISS store (initially None)
        self.store: FAISS | None = None

    # -----------------------------
    # Load existing session
    # -----------------------------
    def load(self, session_id: str) -> bool:
        """
        Agar is session ke liye FAISS index already exist karta hai,
        toh usko disk se load karta hai.

        Returns:
        - True  -> session resumed
        - False -> new session
        """

        session_dir = get_session_dir(session_id)

        if not session_dir.exists():
            return False

        try:
            self.store = FAISS.load_local(
                folder_path=str(session_dir),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
            )
            return True

        except Exception:
            return False

    # -----------------------------
    # Build new index
    # -----------------------------
    def build(self, documents: List[Document], session_id: str):
        """
        Naya FAISS index banata hai using LangChain Documents
        aur disk par save karta hai.
        """

        if not documents:
            raise ValueError("No documents provided to build FAISS index")

        self.store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings,
        )

        self.save(session_id)

    # -----------------------------
    # Save to disk
    # -----------------------------
    def save(self, session_id: str):
        """
        Current FAISS store ko disk par save karta hai
        """

        if not self.store:
            raise RuntimeError("FAISS store not initialized")

        session_dir = get_session_dir(session_id)
        self.store.save_local(str(session_dir))

    # -----------------------------
    # Retriever
    # -----------------------------
    def get_retriever(self, k: int = 4):
        """
        Retriever return karta hai jo similarity search karega
        """

        if not self.store:
            raise RuntimeError("FAISS store not initialized")

        return self.store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )
