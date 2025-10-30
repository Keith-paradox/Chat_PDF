import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4o-mini"
    redis_url: str = "redis://redis:6379/0"
    web_search_provider: str = "duckduckgo"
    chroma_dir: str = "./data/chroma_db"

    class Config:
        env_file = ".env"

settings = Settings()
