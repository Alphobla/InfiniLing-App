"""Story and audio generation endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client
from io import BytesIO
from api.dependencies import get_supabase, get_current_user_id
from api.services.openai_service import OpenAIService
from api.services.token_tracker import TokenTracker
from api.config import get_settings

router = APIRouter(prefix="/api/generate", tags=["generate"])


class StoryRequest(BaseModel):
    """Schema for story generation request."""
    language: str
    word_count: int = 10
    new_word_count: int = 2
    target_length: int = 150
    topic: Optional[str] = None
    style: Optional[str] = None
    format: Optional[str] = None


class StoryResponse(BaseModel):
    """Schema for story generation response."""
    title: str
    story: str


class AudioRequest(BaseModel):
    """Schema for audio generation request."""
    text: str
    voice: str = "alloy"


@router.post("/story", response_model=StoryResponse)
def generate_story(
    request: StoryRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Generate a text using the most overdue vocabulary words."""
    settings = get_settings()

    # Check token limit
    tracker = TokenTracker(db, user_id)
    tracker.check_limit()

    today = datetime.utcnow().date().isoformat()
    due_count = request.word_count - request.new_word_count

    # Fetch most overdue words for this language
    words = []
    if due_count > 0:
        due_query = (
            db.table("vocabulary")
            .select("word, lemma")
            .eq("user_id", user_id)
            .eq("language_from", request.language)
            .not_.is_("next_review_date", "null")
            .lte("next_review_date", today)
            .order("next_review_date")
            .limit(due_count)
        )
        due_result = due_query.execute()
        words = [row.get("lemma") or row["word"] for row in due_result.data]

    # Fetch new words (never reviewed)
    if request.new_word_count > 0:
        new_query = (
            db.table("vocabulary")
            .select("word, lemma")
            .eq("user_id", user_id)
            .eq("language_from", request.language)
            .is_("next_review_date", "null")
            .order("created_at")
            .limit(request.new_word_count)
        )
        new_result = new_query.execute()
        words.extend(row.get("lemma") or row["word"] for row in new_result.data)

    # If not enough due words, fill with more new words (and vice versa)
    if len(words) < request.word_count:
        existing_words = set(w.lower() for w in words)
        remaining = request.word_count - len(words)
        fill_query = (
            db.table("vocabulary")
            .select("word, lemma")
            .eq("user_id", user_id)
            .eq("language_from", request.language)
            .order("created_at")
            .limit(remaining + len(words))
        )
        fill_result = fill_query.execute()
        for row in fill_result.data:
            if len(words) >= request.word_count:
                break
            w = row.get("lemma") or row["word"]
            if w.lower() not in existing_words:
                words.append(w)
                existing_words.add(w.lower())

    if not words:
        raise HTTPException(status_code=400, detail="No vocabulary words found for this language")

    # Generate text
    service = OpenAIService(
        settings.openai_api_key,
        settings.story_max_tokens,
        settings.story_temperature
    )
    result = service.generate_text(
        words=words,
        language=request.language,
        target_length=request.target_length,
        topic=request.topic,
        style=request.style,
        format=request.format,
    )

    # Track tokens
    tracker.add_tokens(result.get("tokens_used", 0))

    return StoryResponse(title=result.get("title", ""), story=result["story"])


@router.post("/audio")
def generate_audio(
    request: AudioRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Generate TTS audio for text."""
    settings = get_settings()

    # Check token limit (TTS costs ~15 chars = 1 token equivalent)
    tracker = TokenTracker(db, user_id)
    tracker.check_limit()

    # Generate audio
    service = OpenAIService(
        settings.openai_api_key,
        settings.enhance_max_tokens,
        settings.enhance_temperature
    )
    audio_bytes = service.generate_audio(request.text, request.voice)

    # Track approximate token cost (rough estimate for TTS)
    estimated_tokens = len(request.text) // 4
    tracker.add_tokens(estimated_tokens)

    # Return as streaming response
    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"}
    )
