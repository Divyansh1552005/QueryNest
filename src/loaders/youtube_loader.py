"""
Is file ka kaam:
- YouTube URL se video ID nikalna
- Transcript API se transcript fetch karna
- LangChain Document object return karna (splitter + FAISS ready)

IMPORTANT:
- Loader ka kaam sirf data lana hai
- No splitting, no embeddings, no FAISS here
"""

from langchain_core.documents import Document
from youtube_transcript_api import TranscriptsDisabled, YouTubeTranscriptApi


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
        # -------------------------------
        # Language fallback strategy
        # -------------------------------
        transcript = None
        try:
            # Try English first
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        except Exception:
            try:
                # Try Hindi
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["hi"]
                )
            except Exception:
                # Get any available transcript
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # Try to get first available transcript (manually created or generated)
                try:
                    transcript = transcript_list.find_transcript(
                        transcript_list._manually_created_transcripts.keys()
                        if transcript_list._manually_created_transcripts
                        else transcript_list._generated_transcripts.keys()
                    ).fetch()
                except Exception:
                    # If all else fails, get the first available one
                    for t in transcript_list:
                        transcript = t.fetch()
                        break

        if not transcript:
            raise RuntimeError("No transcript available for this video")

        # Transcript segments → plain text
        full_text = " ".join(segment["text"] for segment in transcript)

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
