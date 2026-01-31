"""Story and audio generation endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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
    word_ids: List[str]
    language: str
    difficulty: str = "intermediate"
    word_multiplier: Optional[int] = None  # Override default if provided


class StoryResponse(BaseModel):
    """Schema for story generation response."""
    story: str
    words_used: List[str]


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
    """Generate a story using vocabulary words."""
    settings = get_settings()

    # Check token limit
    tracker = TokenTracker(db, user_id)
    tracker.check_limit()

    # Get words from database
    words = []
    for word_id in request.word_ids:
        result = db.table("vocabulary").select("word, lemma").eq("id", word_id).eq("user_id", user_id).execute()
        if result.data:
            # Use lemma if available, otherwise word
            w = result.data[0]
            words.append(w.get("lemma") or w["word"])

    if not words:
        raise HTTPException(status_code=400, detail="No valid words found")

    # Use request multiplier or fall back to settings default
    word_multiplier = request.word_multiplier or settings.story_word_multiplier

    # Generate story
    service = OpenAIService(
        settings.openai_api_key,
        settings.story_max_tokens,
        settings.story_temperature
    )
    result = service.generate_story(
        words,
        request.language,
        request.difficulty,
        word_multiplier=word_multiplier,
        max_tokens=settings.story_max_tokens,
        temperature=settings.story_temperature
    )

    # Track tokens
    tracker.add_tokens(result.get("tokens_used", 0))

    return StoryResponse(
        story=result["story"],
        words_used=result["words_used"]
    )


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
