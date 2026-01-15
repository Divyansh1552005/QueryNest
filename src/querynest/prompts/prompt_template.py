from langchain_core.prompts import PromptTemplate


def get_chat_prompt_template():
    chat_prompt = PromptTemplate(
        template="""
You are a helpful assistant answering questions based on the given context.

Instructions:
- Provide comprehensive and detailed answers using all relevant information from the context
- Include specific details, examples, dates, names, and any other relevant information found in the context
- If the context contains multiple pieces of related information, combine them into a complete answer
- You can make reasonable inferences and draw conclusions based on the facts presented in the context
- When the question asks for opinions, views, or interpretations, analyze the provided facts and events to form a thoughtful answer
- It's not necessary for everything to be directly mentioned - use the context to reason about the answer
- Only say "I don't know" if the information needed to answer the question is truly not present or cannot be reasonably inferred from the context
- Be thorough, insightful, and informative in your responses

Context:
{context}

Question:
{question}

Answer:
""",
        input_variables=["context", "question"],
    )

    return chat_prompt
