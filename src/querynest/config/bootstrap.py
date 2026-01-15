"""
Why this file : 
- App start hote hi ensure karna ki Gemini API key available ho
- First run pe user se API key lena
- GOOGLE_API_KEY environment variable set karna
Ye file sirf ek baar call hoti hai (app startup pe)
"""

import os
from querynest.config.setup import setup_if_needed


def bootstrap():
    """
    1. Check karta hai ki config.json exist karta hai ya nahi
    2. Agar nahi karta → user se API key input leta hai
    3. API key ko environment variable me set karta hai

    Iske baad - chatmodel, embedding model sb api key use kr skte hai environment se
    """

    config = setup_if_needed()

    # LangChain internally GOOGLE_API_KEY env var read karta hai
    os.environ["GOOGLE_API_KEY"] = config.gemini_api_key
