import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "Shoi (সই) - Health Assistant"
    DEBUG: bool = True
    SECRET_KEY: str = "shoi-secret-key-change-in-production-random-uuid-64738291"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 90

    # Database
    DATABASE_URL: str = "sqlite:///./shoi.db"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # gemini, openai, or mock
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Voice / Audio Settings
    TTS_ENGINE: str = "edge-tts"  # edge-tts, gtts, or web
    BANGLA_VOICE: str = "bn-BD-NabanitaNeural"  # Natural Bangla voice
    WHISPER_MODEL: str = "base"

    # RAG Settings
    KB_CONFIDENCE_THRESHOLD: float = 0.45

settings = Settings()
