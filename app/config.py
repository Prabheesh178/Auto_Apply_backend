import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Auto-Apply Backend"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./auto_apply.db" # Default local async SQLite, or postgresql+asyncpg://...
    GEMINI_API_KEY: Optional[str] = None
    GMAIL_CREDENTIALS_FILE: Optional[str] = "credentials.json"
    GMAIL_TOKEN_FILE: Optional[str] = "token.json"
    STORAGE_DIR: str = "./storage"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "resumes"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "screenshots"), exist_ok=True)
