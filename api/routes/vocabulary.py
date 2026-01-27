"""Vocabulary CRUD endpoints."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id
from api.services.openai_service import OpenAIService
from api.services.token_tracker import TokenTracker
from api.config import get_settings

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])


class VocabularyCreate(BaseModel):
    """Schema for creating a vocabulary word."""
    word: str
    translation: str
    language_from: str
    language_to: str


class VocabularyUpdate(BaseModel):
    """Schema for updating a vocabulary word."""
    word: Optional[str] = None
    lemma: Optional[str] = None
    translation: Optional[str] = None
    secondary_translation: Optional[str] = None
    example_sentence_original: Optional[str] = None
    example_sentence_translation: Optional[str] = None


class VocabularyResponse(BaseModel):
    """Schema for vocabulary response."""
    id: UUID
    word: str
    lemma: Optional[str]
    translation: Optional[str]
    language_from: str
    language_to: str
    frequency_rank: Optional[int]
    frequency_level: Optional[str]
    example_sentence_original: Optional[str]
    example_sentence_translation: Optional[str]
    secondary_translation: Optional[str]
    next_review_date: Optional[str]
    review_interval_days: Optional[int]
    easiness_factor: Optional[float]
    created_at: datetime


@router.get("", response_model=List[VocabularyResponse])
def list_vocabulary(
    language_from: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """List user's vocabulary words with optional filtering."""
    query = db.table("vocabulary").select("*").eq("user_id", user_id)

    if language_from:
        query = query.eq("language_from", language_from)

    if search:
        query = query.or_(f"word.ilike.%{search}%,translation.ilike.%{search}%")

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()
    return result.data


@router.post("", response_model=VocabularyResponse)
def create_vocabulary(
    vocab: VocabularyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Add a new vocabulary word."""
    data = vocab.model_dump()
    data["user_id"] = user_id
    data["lemma"] = vocab.word  # Default lemma to word, enhance later

    result = db.table("vocabulary").insert(data).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create vocabulary")

    return result.data[0]


@router.get("/{vocab_id}", response_model=VocabularyResponse)
def get_vocabulary(
    vocab_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get a single vocabulary word by ID."""
    result = db.table("vocabulary").select("*").eq("id", str(vocab_id)).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

    return result.data[0]


@router.put("/{vocab_id}", response_model=VocabularyResponse)
def update_vocabulary(
    vocab_id: UUID,
    vocab: VocabularyUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Update a vocabulary word."""
    update_data = vocab.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = db.table("vocabulary").update(update_data).eq("id", str(vocab_id)).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

    return result.data[0]


@router.delete("/{vocab_id}")
def delete_vocabulary(
    vocab_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Delete a vocabulary word."""
    result = db.table("vocabulary").delete().eq("id", str(vocab_id)).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

    return {"message": "Deleted successfully"}

class EnhanceRequest(BaseModel):
    """Schema for word enhancement request."""
    word: str
    language_from: str
    language_to: str
    existing_translation: Optional[str] = None


class EnhanceResponse(BaseModel):
    """Schema for word enhancement response."""
    lemma: str
    translation: str
    secondary_translation: Optional[str]
    frequency_rank: Optional[int]
    frequency_level: str
    enhancement_failed: bool = False


@router.post("/enhance", response_model=EnhanceResponse)
def enhance_word(
    request: EnhanceRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Enhance a word with lemmatization, translation, and frequency."""
    settings = get_settings()

    # Check token limit
    tracker = TokenTracker(db, user_id)
    tracker.check_limit()

    # Get user's API key or use default
    user_settings = tracker.get_user_settings()
    api_key = settings.openai_api_key
    if user_settings and user_settings.get("openai_api_key_encrypted"):
        # TODO: Decrypt user's key
        pass

    # Enhance word
    service = OpenAIService(
        api_key,
        settings.enhance_max_tokens,
        settings.enhance_temperature
    )
    result = service.enhance_word(
        request.word,
        request.language_from,
        request.language_to,
        request.existing_translation
    )

    # Track tokens
    tracker.add_tokens(result.get("tokens_used", 0))

    # Handle enhancement failure
    if result.get("enhancement_failed"):
        return EnhanceResponse(
            lemma=request.word,
            translation="Unknown",
            secondary_translation=None,
            frequency_rank=None,
            frequency_level="Unknown",
            enhancement_failed=True
        )

    return EnhanceResponse(
        lemma=result["lemma"],
        translation=result["translation"],
        secondary_translation=result.get("secondary_translation"),
        frequency_rank=result.get("frequency_rank"),
        frequency_level=result.get("frequency_level", "Unknown"),
    )
