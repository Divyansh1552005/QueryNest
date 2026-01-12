"""
Is file ka kaam:
- YouTube URL se video ID nikalna
- Transcript API se transcript fetch karna
- LangChain Document object return karna (splitter + FAISS ready)

IMPORTANT:
- Loader ka kaam sirf data lana hai
- No splitting, no embeddings, no FAISS here
"""

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain_core.documents import Document


def extract_video_id(url: str) -> str:
    """
    YouTube ke different URL formats handle karta hai

    Supported:
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/watch?v=VIDEO_ID
    """

    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]

    if "v=" in url:
        return url.split("v=")[1].split("&")[0]

    raise ValueError("Invalid YouTube URL format")


def load_youtube_documents(url: str) -> list[Document]:
    """
    YouTube transcript fetch karta hai aur
    usko LangChain Document me convert karta hai.

    Language preference order:
    1. English
    2. Hindi
    3. Any available language

    Returns:
    - list[Document] (single Document, splitter ke liye consistent)
    """

    video_id = extract_video_id(url)

    try:
        api = YouTubeTranscriptApi()

        # -------------------------------
        # Language fallback strategy
        # -------------------------------
        try:
            transcript = api.fetch(video_id, ["en"])
        except Exception:
            try:
                transcript = api.fetch(video_id, ["hi"])
            except Exception:
                transcript = api.fetch(video_id)

        # Transcript segments → plain text
        full_text = " ".join(segment.text for segment in transcript)

        if not full_text.strip():
            raise RuntimeError("Empty transcript fetched")

        # -------------------------------
        # Convert to LangChain Document
        # -------------------------------
        doc = Document(
            page_content=full_text,
            metadata={
                "source": url,
                "type": "youtube",
                "video_id": video_id,
            },
        )

        # list return kar rahe hain taaki
        # PDF / Web loaders ke saath interface same rahe
        return [doc]

    except TranscriptsDisabled:
        raise RuntimeError("Transcripts are disabled for this video")

    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript: {e}")
