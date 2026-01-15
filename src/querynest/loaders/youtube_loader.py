"""
DEPRECATED: YouTube loader is no longer functional

YouTube has implemented stricter rate limiting and blocking mechanisms that prevent
reliable transcript fetching. The YouTube Transcript API now frequently blocks requests,
making this loader unusable in practice.

This file is kept for reference but should not be used.

---

Original functionality:
- YouTube URL se video ID nikalna
- Transcript API se transcript fetch karna
- LangChain Document object return karna
"""

# import time
#
# from langchain_core.documents import Document
# from youtube_transcript_api import (
#     TranscriptsDisabled,
#     YouTubeRequestFailed,
#     YouTubeTranscriptApi,
# )
#
#
# """
# This func handles different formats of yt links
# Supported:
# - https://youtu.be/VIDEO_ID
# - https://www.youtube.com/watch?v=VIDEO_ID
# """
#
# def extract_video_id(url: str) -> str:
#
#     if "youtu.be/" in url:
#         return url.split("youtu.be/")[1].split("?")[0]
#
#     if "v=" in url:
#         return url.split("v=")[1].split("&")[0]
#
#     raise ValueError("Invalid YouTube URL format")
#
# """
# Transcript fetch karta hai with retry logic and exponential backoff
#
# Args:
#     video_id: YouTube video ID
#     max_retries: Maximum number of retry attempts
#
# Returns:
#     Transcript as list of segments
# """
# def fetch_transcript_with_retry(video_id: str, max_retries: int = 3) -> list:
#
#
#     for attempt in range(max_retries):
#         try:
#             # Add delay between requests to avoid rate limiting
#             if attempt > 0:
#                 wait_time = 2**attempt  # Exponential backoff: 2, 4, 8 seconds
#                 print(
#                     f"⏳ Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}..."
#                 )
#                 time.sleep(wait_time)
#
#             # Try to get transcript with language preference
#             transcript = None
#
#             # Method 1: Try English first
#             try:
#                 print(
#                     f"🔍 Fetching English transcript (attempt {attempt + 1}/{max_retries})..."
#                 )
#                 transcript = YouTubeTranscriptApi.get_transcript(
#                     video_id, languages=["en"]
#                 )
#                 print("✅ English transcript fetched successfully")
#                 return transcript
#             except Exception as e:
#                 error_msg = str(e)
#
#                 # Check if it's a rate limit or empty response
#                 if "no element found" in error_msg or "ParseError" in error_msg:
#                     if attempt < max_retries - 1:
#                         print(f"Empty response (possible rate limit). Retrying...")
#                         continue
#                     else:
#                         raise RuntimeError(
#                             "YouTube is blocking requests (rate limit). "
#                             "Please wait 5-10 minutes and try again."
#                         )
#
#                 # If English not available, try Hindi
#                 pass
#
#             # Method 2: Try Hindi
#             try:
#                 print(f"Trying Hindi transcript...")
#                 transcript = YouTubeTranscriptApi.get_transcript(
#                     video_id, languages=["hi"]
#                 )
#                 print("Hindi transcript fetched successfully")
#                 return transcript
#             except Exception as e:
#                 error_msg = str(e)
#
#                 if "no element found" in error_msg or "ParseError" in error_msg:
#                     if attempt < max_retries - 1:
#                         print(f"Empty response (possible rate limit). Retrying...")
#                         continue
#                     else:
#                         raise RuntimeError(
#                             "YouTube is blocking requests (rate limit). "
#                             "Please wait 5-10 minutes and try again."
#                         )
#
#                 # If Hindi not available, try any language
#                 pass
#
#             # Method 3: Get any available transcript
#             try:
#                 print(f"Fetching any available transcript...")
#
#                 # First, list available transcripts
#                 transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
#
#                 # Try to get the first available transcript
#                 for transcript_obj in transcript_list:
#                     try:
#                         transcript = transcript_obj.fetch()
#                         print(f"✅ Transcript fetched in {transcript_obj.language}")
#                         return transcript
#                     except:
#                         continue
#
#                 # If we reach here, no transcript worked
#                 raise RuntimeError("No transcript could be fetched")
#
#             except Exception as e:
#                 error_msg = str(e)
#
#                 if "no element found" in error_msg or "ParseError" in error_msg:
#                     if attempt < max_retries - 1:
#                         print(f"Empty response (possible rate limit). Retrying...")
#                         continue
#                     else:
#                         raise RuntimeError(
#                             "YouTube is blocking requests (rate limit). "
#                             "Please wait 5-10 minutes and try again."
#                         )
#                 else:
#                     raise e
#
#         except RuntimeError:
#             # Re-raise RuntimeError without wrapping
#             raise
#         except TranscriptsDisabled:
#             raise RuntimeError("Transcripts are disabled for this video")
#         except YouTubeRequestFailed as e:
#             error_msg = str(e)
#             if "429" in error_msg or "Too Many Requests" in error_msg:
#                 if attempt < max_retries - 1:
#                     wait_time = 2**attempt
#                     print(f"⚠️  Rate limit hit. Waiting {wait_time} seconds...")
#                     time.sleep(wait_time)
#                     continue
#                 else:
#                     raise RuntimeError(
#                         "YouTube rate limit reached. Please wait 5-10 minutes and try again."
#                     )
#             else:
#                 raise RuntimeError(f"YouTube request failed: {error_msg}")
#         except Exception as e:
#             error_msg = str(e)
#             if "no element found" in error_msg or "ParseError" in error_msg:
#                 if attempt < max_retries - 1:
#                     continue
#                 else:
#                     raise RuntimeError(
#                         "YouTube is blocking requests (rate limit). "
#                         "Please wait 5-10 minutes and try again, or try using a VPN."
#                     )
#             else:
#                 raise RuntimeError(f"Failed to fetch transcript: {e}")
#
#     # If all retries failed
#     raise RuntimeError(
#         "Failed to fetch transcript after multiple attempts. "
#         "YouTube may be rate limiting. Please wait 5-10 minutes and try again."
#     )
#
#
# def load_youtube_documents(url: str) -> list[Document]:
#     """
#     YouTube transcript fetch karta hai aur
#     usko LangChain Document me convert karta hai.
#
#     Language preference order:
#     1. English
#     2. Hindi
#     3. Any available language
#
#     Returns:
#     - list[Document] (single Document, splitter ke liye consistent)
#     """
#
#     video_id = extract_video_id(url)
#
#     print(f"📺 Video ID: {video_id}")
#
#     # Add small initial delay to avoid immediate rate limiting
#     print("Adding 2 second delay to avoid rate limiting...")
#     time.sleep(2)
#
#     try:
#         # Fetch transcript with retry logic
#         transcript = fetch_transcript_with_retry(video_id, max_retries=3)
#
#         if not transcript:
#             raise RuntimeError("No transcript found")
#
#         # Transcript segments → plain text
#         full_text = " ".join(segment["text"] for segment in transcript)
#
#         if not full_text.strip():
#             raise RuntimeError("Empty transcript fetched")
#
#         print(f"Transcript length: {len(full_text)} characters")
#
#         # Convert to LangChain Document
#         doc = Document(
#             page_content=full_text,
#             metadata={
#                 "source": url,
#                 "type": "youtube",
#                 "video_id": video_id,
#             },
#         )
#
#         # list return kar rahe hain taaki
#         # PDF / Web loaders ke saath interface same rahe
#         return [doc]
#
#     except TranscriptsDisabled:
#         raise RuntimeError("Transcripts are disabled for this video")
#
#     except RuntimeError:
#         # Re-raise RuntimeError as is
#         raise
#
#     except Exception as e:
#         raise RuntimeError(f"Failed to fetch transcript: {e}")
