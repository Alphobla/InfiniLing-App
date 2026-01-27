"""Vocabulary CRUD endpoints."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id

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
