"""
Is file ka kaam:
- Gemini LLM ka LangChain object create karna

IMPORTANT:
- API key yahan set nahi hoti
- Ye assume karta hai ki bootstrap() pehle call ho chuka hai
"""

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm():
    """
    Returns a configured Gemini LLM instance
    """

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=4096,
    )
