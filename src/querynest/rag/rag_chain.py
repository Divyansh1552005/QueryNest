from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from querynest.prompts.prompt_template import get_chat_prompt_template


def _format_docs(docs):
    """
    Retriever se aaye Documents ko
    ek string context me convert karta hai
    """
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(llm, retriever):
    # Prompt template
    prompt = get_chat_prompt_template()

    # Retrieval + formatting
    retrieval_chain = RunnableParallel(
        {
            "context": retriever | RunnableLambda(_format_docs),
            "question": RunnablePassthrough(),
        }
    )

    # Final RAG chain
    rag_chain = retrieval_chain | prompt | llm | StrOutputParser()

    return rag_chain
