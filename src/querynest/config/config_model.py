from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    # min length aala faltu mein laga diya , bas itna rok sake ki 123 ya awein kuch bhi na daal de user
    gemini_api_key: str = Field(..., min_length=10)

