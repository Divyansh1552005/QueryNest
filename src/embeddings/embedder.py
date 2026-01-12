"""
Is file ka kaam:
- Gemini embeddings create karna using LangChain wrapper
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings

# isme jarurat nahi hai api key dene ki ye apne aap nikaal lene os environment se

def get_embeddings():
    """
    Returns a LangChain embeddings object
    (actual embedding computation FAISS ke andar karenge ham iss objecct model ko use krke hi)
    """
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004"
    )
