from langchain_google_genai import GoogleGenerativeAIEmbeddings

# isme jarurat nahi hai api key dene ki ye apne aap nikaal lene os environment se

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004"
    )
