from pydantic import BaseModel, field_validator

from app.schemas.language import LanguageChoice


class TranslateRequest(BaseModel):
    text: str
    target_language: LanguageChoice

    @field_validator("text")
    def validate_query(cls, value):
        if not value.strip():  # Ensures it isn't just whitespace
            raise ValueError("Text must not be empty or whitespace.")
        return value


class LanguageDetectorRequest(BaseModel):
    text: str

    @field_validator("text")
    def validate_query(cls, value):
        if not value.strip():  # Ensures it isn't just whitespace
            raise ValueError("Text must not be empty or whitespace.")
        return value


class TranslateResponse(BaseModel):
    translated_text: str
    language_detected: str
