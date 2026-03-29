"""Onboarding word list endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id
from api.services.onboarding_words import load_word_list, get_words_by_indices

router = APIRouter(prefix="/api/onboarding-words", tags=["onboarding"])


class OnboardingWord(BaseModel):
    """Schema for a single onboarding word."""
    word: str
    example_sentence: str
    frequency_level: str


class OnboardingWordsResponse(BaseModel):
    """Schema for the word list response."""
    language: str
    words: List[OnboardingWord]


class BulkAddRequest(BaseModel):
    """Schema for bulk-adding onboarding words to vocabulary."""
    indices: List[int]
    language_from: str
    language_to: str


class BulkAddResponse(BaseModel):
    """Schema for bulk-add result."""
    added: int


@router.get("/{language_code}", response_model=OnboardingWordsResponse)
def get_onboarding_words(language_code: str):
    """
    Get the 200-word onboarding list for a language.
    No auth required — word lists are public/static data.
    """
    words = load_word_list(language_code)
    if not words:
        raise HTTPException(
            status_code=404,
            detail=f"No onboarding words available for language: {language_code}"
        )
    return OnboardingWordsResponse(
        language=language_code,
        words=[OnboardingWord(**w) for w in words]
    )


@router.post("/add", response_model=BulkAddResponse)
def bulk_add_onboarding_words(
    request: BulkAddRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """
    Bulk-add selected onboarding words to user's vocabulary.

    Takes word indices (positions in the parallel lists), looks up each index
    in both the target (language_from) and native (language_to) files to build
    complete vocabulary entries with translations.
    """
    # Load both language lists
    target_words = load_word_list(request.language_from)
    native_words = load_word_list(request.language_to)

    if not target_words:
        raise HTTPException(status_code=404, detail=f"No word list for: {request.language_from}")
    if not native_words:
        raise HTTPException(status_code=404, detail=f"No word list for: {request.language_to}")

    # Build vocabulary entries from the parallel lists
    entries = []
    for idx in request.indices:
        if idx < 0 or idx >= len(target_words) or idx >= len(native_words):
            continue

        target = target_words[idx]
        native = native_words[idx]

        entries.append({
            "user_id": user_id,
            "word": target["word"],
            "lemma": target["word"],
            "translation": native["word"],
            "language_from": request.language_from,
            "language_to": request.language_to,
            "frequency_level": target["frequency_level"],
            "example_sentence_original": target["example_sentence"],
            "example_sentence_translation": native["example_sentence"],
        })

    if not entries:
        raise HTTPException(status_code=400, detail="No valid word indices provided")

    # Insert all entries at once
    result = db.table("vocabulary").insert(entries).execute()

    return BulkAddResponse(added=len(result.data))
