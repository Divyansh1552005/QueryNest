"""
This file :
- LangChain Community FAISS vector store manage karna
- Session-based save / load support dena
- Retriever provide karna (RAG ke liye)
"""

from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from querynest.embeddings.embedder import get_embeddings
from querynest.utils.paths import get_session_dir


class FaissStore:
    def __init__(self):
        self.embeddings = get_embeddings()

        # Actual FAISS store (initially None)
        self.store: FAISS | None = None

    # Load existing session if it exists ofc
    def load(self, session_id: str) -> bool:
        """
        Agar is session ke liye FAISS index already exist karta hai,
        toh usko disk se load karta hai, no need to create it again and again.

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

    # Build new index

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

    # Save the current faiss session to didsk
    def save(self, session_id: str):
        if not self.store:
            raise RuntimeError("FAISS store not initialized")

        session_dir = get_session_dir(session_id)
        self.store.save_local(str(session_dir))

    # Retriever is returned by this
    def get_retriever(self, k: int = 4):
        if not self.store:
            raise RuntimeError("FAISS store not initialized")

        return self.store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )
