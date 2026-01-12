"""
QueryNest – Terminal-based RAG application
End-to-end wiring:
Source → Loader → Splitter → FAISS → RAG → Chat Memory
"""

import sys

# -----------------------------
# 1. Bootstrap (API key setup)
# -----------------------------
from src.config.bootstrap import bootstrap

bootstrap()

# -----------------------------
# 2. Imports (safe after bootstrap)
# -----------------------------
from src.config.gemini import get_llm
from src.loaders.pdf_loader import load_pdfs_lazy
from src.loaders.web_loader import load_web_pages
from src.loaders.youtube_loader import load_youtube_documents
from src.memory.chat_memory import ChatMemory
from src.processor.text_splitter import split_documents
from src.rag.rag_chain import build_rag_chain
from src.sessions.session_meta import SessionMeta, load_session_meta, save_session_meta
from src.utils.hashing import generate_session_id
from src.utils.paths import ensure_base_dirs, get_session_dir
from src.vector_store.faiss_store import FaissStore


def select_source():
    """
    User se source type aur input leta hai
    Returns: (documents, session_key, source_type)
    """
    source_type = input("Choose source (yt / pdf / web): ").strip().lower()

    if source_type == "yt":
        url = input("Enter YouTube URL: ").strip()
        docs = load_youtube_documents(url)
        session_key = url
        name = (
            input("Enter session name (optional, press Enter to skip): ").strip()
            or url[:50]
        )

    elif source_type == "pdf":
        path = input("Enter PDF file or directory path: ").strip()
        docs = load_pdfs_lazy(path)
        session_key = path
        name = (
            input("Enter session name (optional, press Enter to skip): ").strip()
            or path.split("/")[-1]
        )

    elif source_type == "web":
        url = input("Enter Website URL: ").strip()
        docs = load_web_pages(url)
        session_key = url
        name = (
            input("Enter session name (optional, press Enter to skip): ").strip()
            or url[:50]
        )

    else:
        print(f"\n❌ Error: '{source_type}' is not supported.")
        print("We only support: yt (YouTube), pdf (PDF files), web (Websites)")
        print("Exiting...\n")
        sys.exit(1)

    return docs, session_key, source_type, name


def check_for_config_commands():
    """
    Allows user to update API key before app starts
    """
    cmd = (
        input("Type 'reset-key' to update API key or press Enter to continue: ")
        .strip()
        .lower()
    )

    if cmd == "reset-key":
        from src.config.setup import reset_api_key

        reset_api_key()
        print("\n✅ API key updated. Continuing...\n")


def main():
    ensure_base_dirs()

    # -----------------------------
    # Config commands check
    # -----------------------------
    check_for_config_commands()

    # -----------------------------
    # Source selection
    # -----------------------------
    documents, session_key, source_type, session_name = select_source()
    session_id = generate_session_id(session_key)
    session_dir = get_session_dir(session_id)

    print(f"Session ID: {session_id[:8]}...")

    # -----------------------------
    # FAISS Store
    # -----------------------------
    store = FaissStore()
    resumed = store.load(session_id)

    # -----------------------------
    # Session Metadata
    # -----------------------------
    existing_meta = load_session_meta(session_dir)

    if not resumed:
        print("🆕 New session – building vector store...")

        chunks = split_documents(documents)
        store.build(chunks, session_id)

        # Create new session metadata
        meta = SessionMeta(
            id=session_id,
            name=session_name,
            source=session_key,
            source_type=source_type,
            created_at=SessionMeta.now(),
            last_used_at=SessionMeta.now(),
        )
        save_session_meta(session_dir, meta)
        print(f"📝 Session saved: {session_name}")

    else:
        print("✅ Session resumed")

        # Update last_used_at for existing session
        if existing_meta:
            existing_meta.last_used_at = SessionMeta.now()
            save_session_meta(session_dir, existing_meta)
            print(f"📝 Session: {existing_meta.name}")

    # -----------------------------
    # Chat memory
    # -----------------------------
    memory = ChatMemory(session_id)

    # -----------------------------
    # LLM + RAG chain
    # -----------------------------
    llm = get_llm()
    retriever = store.get_retriever(k=6)
    rag_chain = build_rag_chain(llm, retriever)

    print("\nAsk questions (type 'exit' to quit)\n")

    # -----------------------------
    # Chat loop
    # -----------------------------
    while True:
        query = input("You: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("👋 Bye")
            break

        memory.add_user_message(query)

        # Inject chat history into query
        chat_context = memory.get_context()
        final_query = f"{chat_context}\nUser: {query}"

        answer = rag_chain.invoke(final_query)

        print(f"\nAssistant: {answer}\n")

        memory.add_assistant_message(answer)


if __name__ == "__main__":
    main()
