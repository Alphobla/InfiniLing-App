"""Token usage tracking service."""

from datetime import datetime, date, timedelta
from supabase import Client
from fastapi import HTTPException


class TokenTracker:
    """Track and enforce token usage limits."""

    def __init__(self, db: Client, user_id: str):
        self.db = db
        self.user_id = user_id

    def get_user_settings(self) -> dict:
        """Get user settings, creating if not exists."""
        result = self.db.table("user_settings").select("*").eq("user_id", self.user_id).execute()

        if result.data:
            return result.data[0]

        return None

    def check_limit(self) -> bool:
        """
        Check if user is within token limit.

        Returns True if OK, raises HTTPException if limit exceeded.
        """
        settings = self.get_user_settings()

        if not settings:
            # No settings = new user, they're fine
            return True

        # Check if we need to reset (new month)
        reset_date = datetime.strptime(settings["reset_date"], "%Y-%m-%d").date()
        if date.today() >= reset_date:
            # Reset tokens and update reset date
            new_reset = (date.today().replace(day=1) + timedelta(days=32)).replace(day=1)
            self.db.table("user_settings").update({
                "tokens_used_this_month": 0,
                "reset_date": new_reset.isoformat()
            }).eq("user_id", self.user_id).execute()
            return True

        # Check if user has their own key (unlimited)
        if settings.get("openai_api_key_encrypted"):
            return True

        # Check limit - require these fields to exist
        used = settings.get("tokens_used_this_month")
        limit = settings.get("token_limit")

        if used is None:
            raise HTTPException(
                status_code=500,
                detail="User settings missing 'tokens_used_this_month' field"
            )

        if limit is None:
            raise HTTPException(
                status_code=500,
                detail="User settings missing 'token_limit' field"
            )

        if used >= limit:
            raise HTTPException(
                status_code=403,
                detail="Token limit reached. Add your own OpenAI API key in settings to continue."
            )

        return True

    def add_tokens(self, count: int) -> None:
        """Add tokens to user's monthly usage."""
        settings = self.get_user_settings()

        if not settings:
            return  # No settings to update

        # Don't track if user has own key
        if settings.get("openai_api_key_encrypted"):
            return

        current = settings.get("tokens_used_this_month")
        if current is None:
            raise HTTPException(
                status_code=500,
                detail="User settings missing 'tokens_used_this_month' field"
            )

        self.db.table("user_settings").update({
            "tokens_used_this_month": current + count
        }).eq("user_id", self.user_id).execute()
