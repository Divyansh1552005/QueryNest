from src.utils.hashing import generate_session_id
from src.utils.paths import ensure_base_dirs
from src.vector_store.faiss_store import FaissStore
from src.config.gemini import get_llm


def main():
    ensure_base_dirs()

    source = input("Enter source (URL / PDF path): ")
    query = input("Ask your question: ")

    session_id = generate_session_id(source)

    # LLM (LangChain Gemini)
    llm = get_llm()

    # Vector store
    store = FaissStore()

    # Try resuming session
    resumed = store.load(session_id)

    if not resumed:
        print("🆕 New session, building vectors...")

        # yahan actual loaders aayenge (PDF / Web / YT)
        texts = [
            "This is a sample document",
            "QueryNest is a terminal based RAG app"
        ]

        store.build(texts, session_id)
    else:
        print("✅ Session resumed")

    # Retrieve context
    context_chunks = store.search(query)

    # Prompt (simple for now)
    context = "\n".join(context_chunks)
    prompt = f"""
Answer only from the context below.
If not found, say "I don't know".

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)
    print(response.content)


if __name__ == "__main__":
    main()
