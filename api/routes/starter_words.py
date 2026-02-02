"""Starter words endpoints for onboarding."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from api.services.starter_words import (
    get_starter_words,
    get_supported_languages,
    get_difficulty_levels
)

router = APIRouter(prefix="/api/starter-words", tags=["starter_words"])


class StarterWord(BaseModel):
    """Schema for a starter word."""
    word: str
    translation: str


class StarterWordsResponse(BaseModel):
    """Schema for starter words response."""
    language: str
    difficulty: Optional[str]
    words: List[StarterWord]


@router.get("/languages")
def list_languages():
    """Get list of languages with starter words available."""
    return {
        "languages": get_supported_languages(),
        "difficulty_levels": get_difficulty_levels()
    }


@router.get("/{language}", response_model=StarterWordsResponse)
def get_language_starter_words(
    language: str,
    difficulty: Optional[str] = Query(None, pattern="^(A1|A2|B1|B2|C1|C2)$")
):
    """
    Get starter words for a specific language.

    Args:
        language: Language code (es, fr, en, de)
        difficulty: Optional CEFR level (A1, A2, B1, B2, C1, C2)
    """
    words = get_starter_words(language, difficulty)

    if not words:
        raise HTTPException(
            status_code=404,
            detail=f"No starter words available for language: {language}" +
                   (f" at level {difficulty}" if difficulty else "")
        )

    return StarterWordsResponse(
        language=language,
        difficulty=difficulty,
        words=[StarterWord(**w) for w in words]
    )
