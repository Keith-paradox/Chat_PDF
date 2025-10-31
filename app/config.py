import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_model: str = "google/gemini-2.5-flash-lite"
    redis_url: str = "redis://redis:6379/0"
    chroma_dir: str = "./data/chroma_db"
    searchapi_api_key: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
