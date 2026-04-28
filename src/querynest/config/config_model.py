from pydantic import BaseModel, Field
from typing import Optional

class AppConfig(BaseModel):
    gemini_api_key: str = Field(..., min_length=10)
    
    llm_model: str = Field(default="gemini/gemini-2.5-flash")
    llm_api_key: Optional[str] = Field(default=None, min_length=10)