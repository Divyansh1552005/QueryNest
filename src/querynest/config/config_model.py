from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    gemini_api_key: str = Field(..., min_length=10)

