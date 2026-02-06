"""User settings and account endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id
from api.config import get_settings
from api.services.languages import get_code, is_valid_code

router = APIRouter(prefix="/api/user", tags=["user"])


class UserSettingsResponse(BaseModel):
    """Schema for user settings response."""
    mother_tongue: str
    last_language: Optional[str]
    has_seen_intro: bool
    has_own_api_key: bool
    tokens_used_this_month: int
    token_limit: int


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    mother_tongue: Optional[str] = None
    last_language: Optional[str] = None
    has_seen_intro: Optional[bool] = None


class TokenUsageResponse(BaseModel):
    """Schema for token usage response."""
    tokens_used: int
    token_limit: int
    percentage_used: float
    has_own_key: bool


class CreateSettingsRequest(BaseModel):
    """Schema for creating user settings on signup."""
    mother_tongue: str


class ApiKeyRequest(BaseModel):
    """Schema for setting API key."""
    api_key: str


@router.get("/settings", response_model=UserSettingsResponse)
def get_user_settings(
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get current user's settings."""
    result = db.table("user_settings").select("*").eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User settings not found")

    settings = result.data[0]

    return UserSettingsResponse(
        mother_tongue=settings["mother_tongue"],
        last_language=settings.get("last_language"),
        has_seen_intro=settings.get("has_seen_intro", False),
        has_own_api_key=bool(settings.get("openai_api_key_encrypted")),
        tokens_used_this_month=settings.get("tokens_used_this_month", 0),
        token_limit=settings.get("token_limit", 100000)
    )


@router.post("/settings", response_model=UserSettingsResponse)
def create_user_settings(
    request: CreateSettingsRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Create user settings (called on signup)."""
    # Check if already exists
    existing = db.table("user_settings").select("user_id").eq("user_id", user_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Settings already exist")

    settings = get_settings()

    # Convert language name to code if needed
    from src.shared.languages import get_code, is_valid_code
    mother_tongue = request.mother_tongue
    
    # If it's a full language name, convert to code
    if not is_valid_code(mother_tongue):
        code = get_code(mother_tongue)
        if code:
            mother_tongue = code
        else:
            raise HTTPException(status_code=400, detail=f"Invalid language: {request.mother_tongue}")

    data = {
        "user_id": user_id,
        "mother_tongue": mother_tongue,
        "token_limit": settings.default_token_limit
    }

    result = db.table("user_settings").insert(data).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create settings")

    s = result.data[0]
    return UserSettingsResponse(
        mother_tongue=s["mother_tongue"],
        last_language=s.get("last_language"),
        has_seen_intro=s.get("has_seen_intro", False),
        has_own_api_key=False,
        tokens_used_this_month=0,
        token_limit=s.get("token_limit", 100000)
    )


@router.put("/settings", response_model=UserSettingsResponse)
def update_user_settings(
    settings_update: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Update user settings."""
    update_data = settings_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = db.table("user_settings").update(update_data).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User settings not found")

    s = result.data[0]
    return UserSettingsResponse(
        mother_tongue=s["mother_tongue"],
        last_language=s.get("last_language"),
        has_seen_intro=s.get("has_seen_intro", False),
        has_own_api_key=bool(s.get("openai_api_key_encrypted")),
        tokens_used_this_month=s.get("tokens_used_this_month", 0),
        token_limit=s.get("token_limit", 100000)
    )


@router.get("/usage", response_model=TokenUsageResponse)
def get_token_usage(
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get current month's token usage."""
    result = db.table("user_settings").select(
        "tokens_used_this_month, token_limit, openai_api_key_encrypted"
    ).eq("user_id", user_id).execute()

    if not result.data:
        # No settings = new user with no usage
        return TokenUsageResponse(
            tokens_used=0,
            token_limit=100000,
            percentage_used=0.0,
            has_own_key=False
        )

    s = result.data[0]
    used = s.get("tokens_used_this_month", 0)
    limit = s.get("token_limit", 100000)

    return TokenUsageResponse(
        tokens_used=used,
        token_limit=limit,
        percentage_used=round((used / limit) * 100, 1) if limit > 0 else 0,
        has_own_key=bool(s.get("openai_api_key_encrypted"))
    )


@router.put("/api-key")
def set_api_key(
    request: ApiKeyRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Set user's own OpenAI API key."""
    # TODO: Encrypt the key before storing
    # For now, store as-is (not production-ready)

    result = db.table("user_settings").update({
        "openai_api_key_encrypted": request.api_key,  # Should be encrypted
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User settings not found")

    return {"message": "API key saved"}


@router.delete("/api-key")
def remove_api_key(
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Remove user's OpenAI API key."""
    result = db.table("user_settings").update({
        "openai_api_key_encrypted": None,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User settings not found")

    return {"message": "API key removed"}
