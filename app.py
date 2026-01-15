"""
QueryNest – Terminal-based RAG application
End-to-end wiring:
Source → Loader → Splitter → FAISS → RAG → Chat Memory

ARCHITECTURE:
1. Collect source metadata (NO FETCHING)
2. Check if session exists (FAISS index check)
3. IF session exists → resume (NO LOADERS)
4. IF new session → fetch, split, embed, save
"""

import sys


# 1. Bootstrap (API key setup)
from querynest.config.bootstrap import bootstrap

bootstrap()

# 2. Imports (safe after bootstrap)
from querynest.config.gemini import get_llm
from querynest.loaders.pdf_loader import load_pdfs_lazy
from querynest.loaders.web_loader import load_web_pages
from querynest.loaders.youtube_loader import load_youtube_documents
from querynest.memory.chat_memory import ChatMemory
from querynest.processor.text_splitter import split_documents
from querynest.rag.rag_chain import build_rag_chain
from querynest.sessions.session_meta import SessionMeta, load_session_meta, save_session_meta
from querynest.utils.hashing import generate_session_id
from querynest.utils.paths import ensure_base_dirs, get_session_dir
from querynest.vector_store.faiss_store import FaissStore


def collect_source_metadata():
    """
    ONLY collects source information - DOES NOT FETCH ANYTHING`
    Returns: (source_type, source_key, session_name)
    We are doing this so that agr session ho already toh vahi load ho jaaye
    """
    source_type = input("Choose source (yt / pdf / web): ").strip().lower()

    if source_type == "yt":
        url = input("Enter YouTube URL: ").strip()
        session_key = url
        name = (
            input("Enter session name (optional, press Enter to skip): ").strip()
            or url[:50]
        )
        return source_type, session_key, name

    elif source_type == "pdf":
        path = input(
            "Enter PDF file path or directory path (for multiple PDFs): "
        ).strip()
        session_key = path
        name = (
            input("Enter session name (optional, press Enter to skip): ").strip()
            or path.split("/")[-1]
        )
        return source_type, session_key, name

    elif source_type == "web":
        url_input = input(
            "Enter Website URL(s) (comma-separated for multiple): "
        ).strip()
        session_key = url_input
        name = (
            input("Enter session name (optional, press Enter to skip): ").strip()
            or url_input[:50]
        )
        return source_type, session_key, name

    else:
        print(f"\n❌ Error: '{source_type}' is not supported.")
        print("We only support: yt (YouTube), pdf (PDF files), web (Websites)")
        print("Exiting...\n")
        sys.exit(1)


def fetch_source_documents(source_type: str, source_key: str):
    """
    Fetches documents based on source type
    """
    print(f"Fetching {source_type} content from: {source_key[:60]}...")

    if source_type == "yt":
        return load_youtube_documents(source_key)

    elif source_type == "pdf":
        return load_pdfs_lazy(source_key)

    elif source_type == "web":
        # Split by comma if multiple URLs provided
        urls = [url.strip() for url in source_key.split(",") if url.strip()]
        return load_web_pages(urls)

    else:
        raise ValueError(f"Unknown source type: {source_type}")


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
        from querynest.config.setup import reset_api_key

        reset_api_key()
        print("\n✅ API key updated. Continuing...\n")


def main():
    ensure_base_dirs()

    # Config commands check
    check_for_config_commands()

    # STEP 1: Collect source metadata
    source_type, session_key, session_name = collect_source_metadata()


    # STEP 2: Compute session ID and check existence of session
    session_id = generate_session_id(session_key)
    session_dir = get_session_dir(session_id)

    print(f"\nSession ID: {session_id[:8]}...")


    # STEP 3: Check if FAISS index exists
    store = FaissStore()
    session_exists = store.load(session_id)


    # BRANCHING: Resume vs New Session
    if session_exists:
        # SESSION RESUME PATH
        print("Session resumed from disk")

        # Load existing metadata
        existing_meta = load_session_meta(session_dir)

        if existing_meta:
            # Update last_used_at timestamp
            existing_meta.last_used_at = SessionMeta.now()
            save_session_meta(session_dir, existing_meta)
            print(f"Session: {existing_meta.name}")
            print(f"Source: {existing_meta.source_type.upper()}")
        else:
            print("Session metadata not found (corrupted session?)")

    else:
        # new session is made
        print("New session – fetching and building vector store...")

        # STEP 4: Fetch documents
        documents = fetch_source_documents(source_type, session_key)

        # STEP 5: Split documents into chunks
        print("Splitting documents into chunks...")
        chunks = split_documents(documents)
        print(f"Created {len(chunks)} chunks")

        # STEP 6: Build FAISS index with embeddings
        print("Building FAISS vector store (this may take a moment)...")
        store.build(chunks, session_id)
        print("Vector store built successfully")

        # STEP 7: Create and save session metadata
        meta = SessionMeta(
            id=session_id,
            name=session_name,
            source=session_key,
            source_type=source_type,
            created_at=SessionMeta.now(),
            last_used_at=SessionMeta.now(),
        )
        save_session_meta(session_dir, meta)
        print(f"Session saved: {session_name}")


    # Chat memory (both paths)
    memory = ChatMemory(session_id)

    # LLM + RAG chain (both paths)
    llm = get_llm()
    retriever = store.get_retriever(k=6)
    rag_chain = build_rag_chain(llm, retriever)

    print("\n Chat started! Ask questions (type 'exit' to quit)\n")


    # Chatting loop
    while True:
        query = input("You: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Bye!!!")
            break

        if not query:
            continue

        memory.add_user_message(query)

        # Inject chat history into query
        chat_context = memory.get_context()
        final_query = f"{chat_context}\nUser: {query}"

        answer = rag_chain.invoke(final_query)

        print(f"\nAssistant: {answer}\n")

        memory.add_assistant_message(answer)


if __name__ == "__main__":
    main()
