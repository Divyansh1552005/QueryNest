"""
Is file ka kaam:
- LangChain Documents ko chunks me todna
- sbhi loaders k liye same way mein split karange
- Chunking token-aware + overlap ke saath karna

IMPORTANT:
- Loader sirf Document deta hai
- Splitter sirf Document → Document karta hai
"""

from typing import Iterable, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_text_splitter(
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
) -> RecursiveCharacterTextSplitter:
    """
    Ye function ek configured text splitter return karta hai

    chunk_size:
    - ek chunk me approx kitna text (characters)

    chunk_overlap:
    - consecutive chunks ke beech overlap
    - context continuity ke liye important
    """

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def split_documents(
    documents: Iterable[Document],
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
) -> List[Document]:
    """
    documents:
    - Iterable[Document] (lazy loader se aaya ho sakta hai)

    Returns:
    - List[Document] (small chunks)
    """

    splitter = get_text_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # LangChain internally generator ko bhi handle kar leta hai
    chunks = splitter.split_documents(documents)

    return chunks
