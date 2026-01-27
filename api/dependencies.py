"""FastAPI dependencies for injection."""

from fastapi import Depends, Request
from supabase import create_client, Client
from api.config import get_settings, Settings
from api.auth import get_user_id_from_token


def get_supabase() -> Client:
    """Get Supabase client instance."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_current_user_id(request: Request) -> str:
    """Dependency to get current authenticated user ID."""
    return get_user_id_from_token(request)
