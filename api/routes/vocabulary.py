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
from api.services.srs_service import SRSService
from api.services.tatoeba_service import get_example_sentence
from api.config import get_settings

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class VocabularyCreate(BaseModel):
    """Schema for creating a vocabulary word."""
    word: str
    translation: str
    language_from: str
    language_to: str
    # Enhanced fields (optional, populated after enhance call)
    lemma: Optional[str] = None
    secondary_translation: Optional[str] = None
    frequency_rank: Optional[int] = None
    frequency_level: Optional[str] = None
    example_sentence_original: Optional[str] = None
    example_sentence_translation: Optional[str] = None


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
    example_sentence_original: Optional[str] = None
    example_sentence_translation: Optional[str] = None
    enhancement_failed: bool = False


class ReviewRequest(BaseModel):
    """Schema for submitting a review."""
    score: int  # 0-5 performance score


class ReviewResponse(BaseModel):
    """Schema for review result."""
    vocabulary_id: UUID
    score: int
    easiness_factor: float
    interval_days: int
    repetitions: int
    next_review_date: str


class DueWordResponse(BaseModel):
    """Schema for a word due for review."""
    id: UUID
    word: str
    lemma: Optional[str]
    translation: Optional[str]
    language_from: str
    language_to: str
    example_sentence_original: Optional[str]
    example_sentence_translation: Optional[str]
    secondary_translation: Optional[str]
    next_review_date: Optional[str]
    easiness_factor: Optional[float]
    review_interval_days: Optional[int]


class ReviewStatistics(BaseModel):
    """Schema for review statistics."""
    total_words: int
    new_words: int
    due_words: int
    future_words: int


# ============================================================================
# List and Create Endpoints
# ============================================================================

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
    data = vocab.model_dump(exclude_none=True)
    data["user_id"] = user_id
    if "lemma" not in data:
        data["lemma"] = vocab.word  # Default lemma to word if not provided

    result = db.table("vocabulary").insert(data).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create vocabulary")

    return result.data[0]


# ============================================================================
# Static Path Endpoints (must come before /{vocab_id})
# ============================================================================

@router.get("/due", response_model=List[DueWordResponse])
def get_due_words(
    language_from: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    include_new: bool = True,
    new_word_ratio: float = Query(default=0.2, ge=0, le=1),
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """
    Get words due for review.

    Returns words where next_review_date <= today, sorted by urgency.
    Optionally includes new words (never reviewed) based on new_word_ratio.
    """
    today = datetime.utcnow().date().isoformat()

    # Calculate how many due vs new words to fetch
    if include_new:
        new_count = int(limit * new_word_ratio)
        due_count = limit - new_count
    else:
        due_count = limit
        new_count = 0

    # Get due words (have been reviewed before and are due)
    due_query = db.table("vocabulary").select("*").eq("user_id", user_id).not_.is_("next_review_date", "null").lte("next_review_date", today)

    if language_from:
        due_query = due_query.eq("language_from", language_from)

    due_query = due_query.order("next_review_date").limit(due_count)
    due_result = due_query.execute()
    due_words = due_result.data

    # Get new words (never reviewed - no next_review_date)
    new_words = []
    if new_count > 0:
        new_query = db.table("vocabulary").select("*").eq("user_id", user_id).is_("next_review_date", "null")

        if language_from:
            new_query = new_query.eq("language_from", language_from)

        new_query = new_query.order("created_at").limit(new_count)
        new_result = new_query.execute()
        new_words = new_result.data

    # Combine results
    return due_words + new_words


@router.get("/statistics", response_model=ReviewStatistics)
def get_review_statistics(
    language_from: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get statistics about review state."""
    today = datetime.utcnow().date().isoformat()

    base_query = db.table("vocabulary").select("id, next_review_date").eq("user_id", user_id)

    if language_from:
        base_query = base_query.eq("language_from", language_from)

    result = base_query.execute()
    words = result.data

    total_words = len(words)
    new_words = 0
    due_words = 0
    future_words = 0

    for word in words:
        next_review = word.get("next_review_date")
        if next_review is None:
            new_words += 1
        elif next_review <= today:
            due_words += 1
        else:
            future_words += 1

    return ReviewStatistics(
        total_words=total_words,
        new_words=new_words,
        due_words=due_words,
        future_words=future_words
    )


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

    # Fetch example sentence from Tatoeba
    example_original = None
    example_translation = None
    try:
        example = get_example_sentence(
            result["lemma"],
            request.language_from,
            request.language_to
        )
        if example:
            example_original = example.get("original")
            example_translation = example.get("translation")
    except Exception:
        pass  # Don't fail the request if Tatoeba fails

    return EnhanceResponse(
        lemma=result["lemma"],
        translation=result["translation"],
        secondary_translation=result.get("secondary_translation"),
        frequency_rank=result.get("frequency_rank"),
        frequency_level=result.get("frequency_level", "Unknown"),
        example_sentence_original=example_original,
        example_sentence_translation=example_translation,
    )


# ============================================================================
# Dynamic Path Endpoints (/{vocab_id})
# ============================================================================

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


@router.post("/{vocab_id}/review", response_model=ReviewResponse)
def submit_review(
    vocab_id: UUID,
    review: ReviewRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """
    Submit a review for a vocabulary word.

    Score meanings:
    - 0: Complete blackout
    - 1: Incorrect, but recognized after seeing answer
    - 2: Incorrect, but answer seemed easy to recall
    - 3: Correct with serious difficulty
    - 4: Correct with some hesitation
    - 5: Perfect response
    """
    if not (0 <= review.score <= 5):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 5")

    # Get current word state
    result = db.table("vocabulary").select("*").eq("id", str(vocab_id)).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vocabulary not found")

    word = result.data[0]

    # Get latest occurrence for current repetitions count
    occ_result = db.table("vocabulary_occurrence").select("repetitions").eq(
        "vocabulary_id", str(vocab_id)
    ).order("review_date", desc=True).limit(1).execute()

    current_reps = occ_result.data[0]["repetitions"] if occ_result.data else 0

    # Calculate new SRS parameters
    new_ef, new_reps, new_interval, next_review = SRSService.process_review(
        score=review.score,
        current_ef=word.get("easiness_factor"),
        current_repetitions=current_reps,
        current_interval=word.get("review_interval_days")
    )

    # Create occurrence record
    occurrence_data = {
        "vocabulary_id": str(vocab_id),
        "score": review.score,
        "easiness_factor": new_ef,
        "interval_days": new_interval,
        "repetitions": new_reps
    }
    db.table("vocabulary_occurrence").insert(occurrence_data).execute()

    # Update vocabulary with new SRS state
    update_data = {
        "easiness_factor": new_ef,
        "review_interval_days": new_interval,
        "next_review_date": next_review.date().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    db.table("vocabulary").update(update_data).eq("id", str(vocab_id)).eq("user_id", user_id).execute()

    return ReviewResponse(
        vocabulary_id=vocab_id,
        score=review.score,
        easiness_factor=new_ef,
        interval_days=new_interval,
        repetitions=new_reps,
        next_review_date=next_review.date().isoformat()
    )
