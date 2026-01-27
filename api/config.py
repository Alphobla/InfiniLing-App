"""Configuration management for the API."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str

    # OpenAI
    openai_api_key: str

    # Token limits
    default_token_limit: int = 100000

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
