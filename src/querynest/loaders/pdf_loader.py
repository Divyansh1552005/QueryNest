"""
Is file ka kaam:
- PDF files ko LangChain ke through load karna
- Lazy loading use karna taaki RAM par kam load pade
- Single PDF ya poore directory dono support karna

Ye loader sirf DOCUMENTS deta hai,
text splitting baad me hoga.
"""

from pathlib import Path
from typing import Iterable

from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
)
from langchain_core.documents import Document


def load_pdfs_lazy(path: str) -> Iterable[Document]:
    """
    path:
    - ek single PDF file ka path
    - ya ek directory jisme multiple PDFs ho

    Returns:
    - Iterable[Document] (lazy generator)

    NOTE:
    - Is function me koi heavy RAM load nahi hota
    - Documents ek-ek karke milte hain
    """

    input_path = Path(path)

    if not input_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    # -------------------------------
    # Case 1: Single PDF file
    # -------------------------------
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            raise ValueError("Provided file is not a PDF")

        loader = PyPDFLoader(str(input_path))
        return loader.lazy_load()

    # -------------------------------
    # Case 2: Directory of PDFs
    # -------------------------------
    if input_path.is_dir():
        loader = DirectoryLoader(
            path=str(input_path),
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True,  # terminal UX better
        )

        return loader.lazy_load()

    raise RuntimeError("Unsupported path type")
