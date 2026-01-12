import os

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.setup import setup_if_needed


def get_llm():
    # ensure config + api key exists (auto setup if needed)
    config = setup_if_needed()

    # set env var once (LangChain reads from here)
    os.environ["GOOGLE_API_KEY"] = config.gemini_api_key

    # create LangChain Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=4096,
    )

    return llm
