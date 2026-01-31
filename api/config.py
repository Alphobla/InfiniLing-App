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

    # Word enhancement settings
    enhance_max_tokens: int = 200
    enhance_temperature: float = 0.3

    # Story generation settings
    story_max_tokens: int = 800
    story_temperature: float = 0.7
    story_word_multiplier: int = 20  # Story words per vocabulary word

    # Token limits
    default_token_limit: int = 100000

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
