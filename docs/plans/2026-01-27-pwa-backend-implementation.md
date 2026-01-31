# PWA Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the FastAPI backend for InfiniLing PWA with Supabase integration, reusing existing spaced repetition and translation logic.

**Architecture:** FastAPI serverless functions on Vercel, connected to Supabase PostgreSQL. Auth handled by Supabase. Token tracking for OpenAI usage limits.

**Tech Stack:** FastAPI, Supabase (PostgreSQL + Auth), OpenAI API, Python 3.10+

---

## Progress Summary

| Task | Status |
|------|--------|
| Task 1: Project Structure Setup | ✅ DONE |
| Task 2: Supabase Auth Middleware | ✅ DONE |
| Task 3: Database Models (SQL) | ✅ DONE |
| Task 4: Vocabulary CRUD Endpoints | ✅ DONE |
| Task 5: Word Enhancement Service | ✅ DONE |
| Task 6: Spaced Repetition Endpoints | ✅ DONE |
| Task 7: User Settings Endpoints | ✅ DONE |
| Task 8: Story Generation Endpoints | ❌ TODO |
| Task 9: Import/Export Endpoints | ❌ TODO |
| Task 10: Starter Words Endpoint | ❌ TODO |
| Task 11: Environment Setup | ❌ TODO |

---

## Task 1: Project Structure Setup ✅ DONE

**Files:**
- Create: `api/__init__.py`
- Create: `api/main.py`
- Create: `api/config.py`
- Create: `api/requirements.txt`
- Create: `vercel.json`

**Step 1: Create the api directory structure**

```bash
mkdir -p api/routes api/services
touch api/__init__.py api/routes/__init__.py api/services/__init__.py
```

**Step 2: Create api/config.py**

```python
"""Configuration management for the API."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str

    # OpenAI
    openai_api_key: str

    # Word enhancement settings
    enhance_max_tokens: int = 200
    enhance_temperature: float = 0.3

    # Token limits
    default_token_limit: int = 100000

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Step 3: Create api/main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 4: Create api/requirements.txt**

```
fastapi>=0.109.0
pydantic-settings>=2.0.0
supabase>=2.0.0
python-jose[cryptography]>=3.3.0
openai>=1.0.0
wordfreq>=3.0.0
httpx>=0.25.0
python-multipart>=0.0.6
```

**Step 5: Create vercel.json**

```json
{
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/main.py"
    }
  ]
}
```

**Step 6: Commit**

```bash
git add api/ vercel.json
git commit -m "feat: add FastAPI project structure for PWA backend"
```

---

## Task 2: Supabase Auth Middleware ✅ DONE

**Files:**
- Create: `api/auth.py`
- Create: `api/dependencies.py`

**Step 1: Create api/auth.py**

```python
"""Supabase authentication utilities."""

from fastapi import HTTPException, Request
from jose import jwt, JWTError
from api.config import get_settings


def get_user_id_from_token(request: Request) -> str:
    """
    Extract and validate user ID from Supabase JWT token.

    Args:
        request: FastAPI request object

    Returns:
        User ID (UUID string)

    Raises:
        HTTPException: If token is missing or invalid
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ")[1]
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
```

**Step 2: Create api/dependencies.py**

```python
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
```

**Step 3: Commit**

```bash
git add api/auth.py api/dependencies.py
git commit -m "feat: add Supabase auth middleware and dependencies"
```

---

## Task 3: Database Models (Supabase SQL) ✅ DONE

**Files:**
- Create: `api/schema.sql`

This file is for reference and manual execution in Supabase dashboard.

**Step 1: Create api/schema.sql**

```sql
-- Vocabulary table
CREATE TABLE vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    lemma TEXT,
    translation TEXT,
    language_from TEXT NOT NULL,
    language_to TEXT NOT NULL,
    frequency_rank INTEGER,
    frequency_level TEXT,
    example_sentence_original TEXT,
    example_sentence_translation TEXT,
    secondary_translation TEXT,
    next_review_date DATE,
    review_interval_days INTEGER DEFAULT 1,
    easiness_factor FLOAT DEFAULT 2.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, lemma, language_from, language_to)
);

-- Index for fast user queries
CREATE INDEX idx_vocabulary_user_id ON vocabulary(user_id);
CREATE INDEX idx_vocabulary_language ON vocabulary(user_id, language_from);
CREATE INDEX idx_vocabulary_review ON vocabulary(user_id, next_review_date);

-- Vocabulary occurrence (review history)
CREATE TABLE vocabulary_occurrence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vocabulary_id UUID NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    review_date TIMESTAMPTZ DEFAULT NOW(),
    score INTEGER CHECK (score >= 0 AND score <= 5),
    easiness_factor FLOAT,
    interval_days INTEGER,
    repetitions INTEGER
);

CREATE INDEX idx_occurrence_vocabulary ON vocabulary_occurrence(vocabulary_id);

-- User settings
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    openai_api_key_encrypted TEXT,
    tokens_used_this_month INTEGER DEFAULT 0,
    token_limit INTEGER DEFAULT 100000,
    mother_tongue TEXT NOT NULL,
    last_language TEXT,
    reset_date DATE DEFAULT (date_trunc('month', NOW()) + INTERVAL '1 month')::DATE,
    has_seen_intro BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security policies
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary_occurrence ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own vocabulary" ON vocabulary
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own vocabulary" ON vocabulary
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vocabulary" ON vocabulary
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own vocabulary" ON vocabulary
    FOR DELETE USING (auth.uid() = user_id);

-- Same for occurrences (via vocabulary ownership)
CREATE POLICY "Users can view own occurrences" ON vocabulary_occurrence
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM vocabulary WHERE vocabulary.id = vocabulary_id AND vocabulary.user_id = auth.uid())
    );

CREATE POLICY "Users can insert own occurrences" ON vocabulary_occurrence
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM vocabulary WHERE vocabulary.id = vocabulary_id AND vocabulary.user_id = auth.uid())
    );

-- User settings
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);
```

**Step 2: Commit**

```bash
git add api/schema.sql
git commit -m "docs: add Supabase database schema with RLS policies"
```

---

## Task 4: Vocabulary CRUD Endpoints ✅ DONE

**Files:**
- Create: `api/routes/vocabulary.py`
- Modify: `api/main.py` (add router)

**Step 1: Create api/routes/vocabulary.py**

```python
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
```

**Step 2: Update api/main.py to include router**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 3: Commit**

```bash
git add api/routes/vocabulary.py api/main.py
git commit -m "feat: add vocabulary CRUD endpoints"
```

---

## Task 5: Word Enhancement Service ✅ DONE

**Files:**
- Create: `api/services/openai_service.py`
- Create: `api/services/token_tracker.py`
- Modify: `api/routes/vocabulary.py` (add enhance endpoint)

**Step 1: Create api/services/openai_service.py**

```python
"""OpenAI service for word enhancement and generation."""

import json
from typing import Optional, Dict
from openai import OpenAI
from wordfreq import zipf_frequency


def get_frequency_info(word: str, language: str) -> Dict:
    """Get word frequency information using wordfreq."""
    zipf_freq = zipf_frequency(word.lower(), language)

    if zipf_freq <= 0:
        return {"rank": None, "level": "Unknown"}

    rank = int(10 ** (8 - zipf_freq))

    if rank <= 1000:
        level = "Top 1,000"
    elif rank <= 5000:
        level = "Top 5,000"
    elif rank <= 10000:
        level = "Top 10,000"
    elif rank <= 20000:
        level = "Top 20,000"
    else:
        level = "Rare"

    return {"rank": rank, "level": level}


class OpenAIService:
    """Service for OpenAI API calls."""

    def __init__(self, api_key: str, max_tokens: int, temperature: float):
        self.client = OpenAI(api_key=api_key)
        self.max_tokens = max_tokens
        self.temperature = temperature

    def enhance_word(
        self,
        word: str,
        language_from: str,
        language_to: str,
        existing_translation: Optional[str] = None
    ) -> Dict:
        """
        Enhance a word with lemmatization, translation, and frequency.

        Returns dict with: lemma, translation, secondary_translation,
        frequency_rank, frequency_level, tokens_used

        If enhancement fails, returns dict with "enhancement_failed": True
        """
        prompt = f"""You are a professional lexicographer normalizing vocabulary entries.

INPUT: {language_from} word "{word}"
{f'CONTEXT: Existing translation "{existing_translation}" may help disambiguate meaning.' if existing_translation else ''}

TASK: Convert to standard dictionary headword form (lemma), then translate to {language_to}.

LEMMATIZATION STANDARDS:
- Verbs: infinitive form (e.g., "played" -> "play", "ging" -> "gehen")
- Nouns: singular form with definite article ONLY if the language uses gendered articles to convey grammatical gender (e.g., "der Hund" for German, "le chien" for French). For languages without grammatical gender like English, use bare noun without article.
- Adjectives: citation form (typically masculine singular, e.g., "belle" -> "beau")
- Reflexive/pronominal verbs: retain reflexive marker (e.g., "sich freuen", "se lever")
- Fixed expressions/idioms: preserve complete phrase (e.g., "ins Gras beissen", "casser les pieds")

OUTPUT: JSON only, no markdown formatting.
{{
  "lemma": "<dictionary headword in {language_from}>",
  "translation": "<{language_to} equivalent>",
  "secondary_translation": "<alternative meaning if common, otherwise null>"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        content = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1])

        result = json.loads(content)

        # Validate that lemma was identified
        lemma = result.get("lemma")
        if not lemma or lemma.lower() in ["none", "null", ""]:
            return {
                "enhancement_failed": True,
                "tokens_used": response.usage.total_tokens
            }

        # Add frequency info
        # Strip articles for frequency lookup
        core_word = lemma.split()[-1] if " " in lemma else lemma
        freq_info = get_frequency_info(core_word, language_from)

        result["frequency_rank"] = freq_info["rank"]
        result["frequency_level"] = freq_info["level"]

        # Return token count for tracking
        result["tokens_used"] = response.usage.total_tokens

        return result
```

**Step 2: Create api/services/token_tracker.py**

```python
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
```

**Step 3: Add enhance endpoint to api/routes/vocabulary.py**

Add this import at the top:

```python
from api.services.openai_service import OpenAIService
from api.services.token_tracker import TokenTracker
from api.config import get_settings
```

Add this endpoint:

```python
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
```

**Step 4: Commit**

```bash
git add api/services/openai_service.py api/services/token_tracker.py api/routes/vocabulary.py
git commit -m "feat: add word enhancement with token tracking"
```

---

## Task 6: Spaced Repetition Endpoints

**Files:**
- Create: `api/routes/review.py`
- Modify: `api/main.py` (add router)

**Step 1: Create api/routes/review.py**

```python
"""Spaced repetition review endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id

router = APIRouter(prefix="/api/review", tags=["review"])


# SM-2 Algorithm parameters
INITIAL_INTERVAL = 1
SECOND_INTERVAL = 6
MIN_EASINESS = 1.3
INITIAL_EASINESS = 2.5


def calculate_easiness_factor(current_ef: float, score: int) -> float:
    """Calculate new easiness factor based on SM-2 algorithm."""
    new_ef = current_ef + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
    return max(new_ef, MIN_EASINESS)


def calculate_next_interval(repetitions: int, easiness_factor: float, current_interval: int) -> int:
    """Calculate next review interval in days."""
    if repetitions == 0:
        return INITIAL_INTERVAL
    elif repetitions == 1:
        return SECOND_INTERVAL
    else:
        return int(current_interval * easiness_factor)


class ReviewResult(BaseModel):
    """Schema for recording review result."""
    score: int = Field(ge=0, le=5)


class ReviewStats(BaseModel):
    """Schema for review statistics."""
    total_words: int
    due_words: int
    new_words: int
    reviewed_today: int


class DueWord(BaseModel):
    """Schema for a word due for review."""
    id: UUID
    word: str
    lemma: Optional[str]
    translation: Optional[str]
    primary_translation: Optional[str]
    language_from: str
    language_to: str
    is_new: bool


@router.get("/due", response_model=List[DueWord])
def get_due_words(
    language_from: Optional[str] = None,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get words due for review today."""
    today = datetime.utcnow().date().isoformat()

    query = db.table("vocabulary").select("*").eq("user_id", user_id)

    if language_from:
        query = query.eq("language_from", language_from)

    # Get words where next_review_date <= today OR next_review_date is null (new words)
    query = query.or_(f"next_review_date.lte.{today},next_review_date.is.null")
    query = query.order("next_review_date", nullsfirst=True).limit(limit)

    result = query.execute()

    return [
        DueWord(
            id=w["id"],
            word=w["word"],
            lemma=w.get("lemma"),
            translation=w.get("translation"),
            primary_translation=w.get("primary_translation"),
            language_from=w["language_from"],
            language_to=w["language_to"],
            is_new=w.get("next_review_date") is None
        )
        for w in result.data
    ]


@router.get("/session", response_model=List[DueWord])
def get_review_session(
    language_from: Optional[str] = None,
    target_count: int = 20,
    new_word_ratio: float = 0.2,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get a review session mixing due words and new words."""
    today = datetime.utcnow().date().isoformat()
    new_count = int(target_count * new_word_ratio)
    due_count = target_count - new_count

    query = db.table("vocabulary").select("*").eq("user_id", user_id)
    if language_from:
        query = query.eq("language_from", language_from)

    # Get due words (not null and <= today)
    due_query = query.lte("next_review_date", today).order("next_review_date").limit(due_count)
    due_result = due_query.execute()
    due_words = due_result.data

    # Get new words (null next_review_date)
    new_query = db.table("vocabulary").select("*").eq("user_id", user_id)
    if language_from:
        new_query = new_query.eq("language_from", language_from)
    new_query = new_query.is_("next_review_date", "null").limit(new_count)
    new_result = new_query.execute()
    new_words = new_result.data

    # Combine
    all_words = due_words + new_words

    return [
        DueWord(
            id=w["id"],
            word=w["word"],
            lemma=w.get("lemma"),
            translation=w.get("translation"),
            primary_translation=w.get("primary_translation"),
            language_from=w["language_from"],
            language_to=w["language_to"],
            is_new=w.get("next_review_date") is None
        )
        for w in all_words
    ]


@router.post("/{vocab_id}/result")
def record_review_result(
    vocab_id: UUID,
    result: ReviewResult,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Record review result and update spaced repetition parameters."""
    # Get current word
    word_result = db.table("vocabulary").select("*").eq("id", str(vocab_id)).eq("user_id", user_id).execute()

    if not word_result.data:
        raise HTTPException(status_code=404, detail="Word not found")

    word = word_result.data[0]

    # Get current SRS state
    current_ef = word.get("easiness_factor") or INITIAL_EASINESS
    current_interval = word.get("review_interval_days") or 1

    # Count repetitions from occurrences
    occ_result = db.table("vocabulary_occurrence").select("id").eq("vocabulary_id", str(vocab_id)).execute()
    repetitions = len(occ_result.data) if occ_result.data else 0

    # Calculate new parameters
    new_ef = calculate_easiness_factor(current_ef, result.score)
    success = result.score >= 3
    new_reps = repetitions + 1 if success else 0
    new_interval = calculate_next_interval(new_reps, new_ef, current_interval)
    next_review = (datetime.utcnow() + timedelta(days=new_interval)).date().isoformat()

    # Update vocabulary
    db.table("vocabulary").update({
        "easiness_factor": new_ef,
        "review_interval_days": new_interval,
        "next_review_date": next_review,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", str(vocab_id)).execute()

    # Add occurrence
    db.table("vocabulary_occurrence").insert({
        "vocabulary_id": str(vocab_id),
        "score": result.score,
        "easiness_factor": new_ef,
        "interval_days": new_interval,
        "repetitions": new_reps
    }).execute()

    return {
        "message": "Review recorded",
        "next_review_date": next_review,
        "new_interval_days": new_interval
    }


@router.get("/stats", response_model=ReviewStats)
def get_review_stats(
    language_from: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Get review statistics."""
    today = datetime.utcnow().date().isoformat()

    query = db.table("vocabulary").select("id, next_review_date").eq("user_id", user_id)
    if language_from:
        query = query.eq("language_from", language_from)

    result = query.execute()
    words = result.data

    total = len(words)
    new_words = sum(1 for w in words if w.get("next_review_date") is None)
    due_words = sum(1 for w in words if w.get("next_review_date") and w["next_review_date"] <= today)

    # Count today's reviews
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    occ_result = db.table("vocabulary_occurrence").select("id").gte("review_date", today_start).execute()
    reviewed_today = len(occ_result.data) if occ_result.data else 0

    return ReviewStats(
        total_words=total,
        due_words=due_words,
        new_words=new_words,
        reviewed_today=reviewed_today
    )
```

**Step 2: Update api/main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, review

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router)
app.include_router(review.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 3: Commit**

```bash
git add api/routes/review.py api/main.py
git commit -m "feat: add spaced repetition review endpoints"
```

---

## Task 7: User Settings Endpoints

**Files:**
- Create: `api/routes/user.py`
- Modify: `api/main.py` (add router)

**Step 1: Create api/routes/user.py**

```python
"""User settings and account endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id
from api.config import get_settings

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

    data = {
        "user_id": user_id,
        "mother_tongue": request.mother_tongue,
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
    api_key: str,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Set user's own OpenAI API key."""
    # TODO: Encrypt the key before storing
    # For now, store as-is (not production-ready)

    result = db.table("user_settings").update({
        "openai_api_key_encrypted": api_key,  # Should be encrypted
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
```

**Step 2: Update api/main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, review, user

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router)
app.include_router(review.router)
app.include_router(user.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 3: Commit**

```bash
git add api/routes/user.py api/main.py
git commit -m "feat: add user settings and token usage endpoints"
```

---

## Task 8: Story Generation Endpoints

**Files:**
- Create: `api/routes/generate.py`
- Modify: `api/main.py` (add router)
- Modify: `api/services/openai_service.py` (add generation methods)

**Step 1: Add generation methods to api/services/openai_service.py**

Add these methods to the OpenAIService class:

```python
def generate_story(
    self,
    words: List[str],
    language: str,
    difficulty: str = "intermediate"
) -> Dict:
    """
    Generate a story using the provided vocabulary words.

    Returns dict with: story, words_used, tokens_used
    """
    words_str = ", ".join(words)

    prompt = f"""Write a short story (150-250 words) in {language} that naturally incorporates these vocabulary words: {words_str}

Requirements:
- Use simple, clear sentences appropriate for {difficulty} learners
- Incorporate all the words naturally (don't force them)
- Make it engaging and memorable
- The story should make sense and flow well

Write only the story, no explanations."""

    response = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )

    story = response.choices[0].message.content.strip()

    return {
        "story": story,
        "words_used": words,
        "tokens_used": response.usage.total_tokens
    }

def generate_audio(self, text: str, voice: str = "alloy") -> bytes:
    """
    Generate TTS audio for text.

    Returns audio bytes (mp3 format).
    """
    response = self.client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    return response.content
```

**Step 2: Create api/routes/generate.py**

```python
"""Story and audio generation endpoints."""

from typing import List
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
    word_ids: List[str]
    language: str
    difficulty: str = "intermediate"


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

    # Generate story
    service = OpenAIService(settings.openai_api_key)
    result = service.generate_story(words, request.language, request.difficulty)

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
    service = OpenAIService(settings.openai_api_key)
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
```

**Step 3: Update api/main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, review, user, generate

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router)
app.include_router(review.router)
app.include_router(user.router)
app.include_router(generate.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 4: Commit**

```bash
git add api/services/openai_service.py api/routes/generate.py api/main.py
git commit -m "feat: add story and audio generation endpoints"
```

---

## Task 9: Import/Export Endpoints

**Files:**
- Create: `api/routes/import_export.py`
- Modify: `api/main.py` (add router)

**Step 1: Create api/routes/import_export.py**

```python
"""Import and export vocabulary endpoints."""

import csv
import json
from io import StringIO
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client
from api.dependencies import get_supabase, get_current_user_id

router = APIRouter(prefix="/api", tags=["import_export"])


class ImportResult(BaseModel):
    """Schema for import result."""
    total_rows: int
    imported: int
    skipped: int
    errors: List[str]


@router.get("/export")
def export_vocabulary(
    format: str = Query(default="csv", regex="^(csv|json)$"),
    language_from: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """Export vocabulary as CSV or JSON."""
    query = db.table("vocabulary").select("*").eq("user_id", user_id)

    if language_from:
        query = query.eq("language_from", language_from)

    result = query.order("created_at", desc=True).execute()
    words = result.data

    if format == "json":
        # Return JSON
        content = json.dumps(words, indent=2, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=vocabulary.json"}
        )
    else:
        # Return CSV
        output = StringIO()
        if words:
            fieldnames = ["word", "lemma", "translation", "primary_translation",
                         "language_from", "language_to", "frequency_rank",
                         "frequency_level", "example_sentence_original",
                         "example_sentence_translation", "created_at"]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(words)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vocabulary.csv"}
        )


class ImportRequest(BaseModel):
    """Schema for import with conflict resolution."""
    conflict_resolution: str = "skip"  # skip, merge, replace


@router.post("/import", response_model=ImportResult)
async def import_vocabulary(
    file: UploadFile = File(...),
    language_from: str = Query(...),
    language_to: str = Query(...),
    conflict_resolution: str = Query(default="skip", regex="^(skip|merge|replace)$"),
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_supabase)
):
    """
    Import vocabulary from CSV or JSON file.

    Conflict resolution:
    - skip: Skip words that already exist
    - merge: Update existing words with new data
    - replace: Delete existing and add new
    """
    content = await file.read()
    content_str = content.decode("utf-8")

    # Detect format
    filename = file.filename or ""
    if filename.endswith(".json") or content_str.strip().startswith("["):
        words = json.loads(content_str)
    else:
        # Assume CSV
        reader = csv.DictReader(StringIO(content_str))
        words = list(reader)

    result = ImportResult(total_rows=len(words), imported=0, skipped=0, errors=[])

    for i, word_data in enumerate(words):
        try:
            # Get word and translation from various possible column names
            word = word_data.get("word") or word_data.get("source") or word_data.get("term")
            translation = word_data.get("translation") or word_data.get("target") or word_data.get("meaning")

            if not word or not translation:
                result.errors.append(f"Row {i+1}: Missing word or translation")
                result.skipped += 1
                continue

            # Check if exists
            existing = db.table("vocabulary").select("id").eq("user_id", user_id).eq("word", word).eq("language_from", language_from).execute()

            if existing.data:
                if conflict_resolution == "skip":
                    result.skipped += 1
                    continue
                elif conflict_resolution == "merge":
                    # Update existing
                    update_data = {
                        "translation": translation,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    # Add optional fields if present
                    for field in ["lemma", "primary_translation", "frequency_rank"]:
                        if word_data.get(field):
                            update_data[field] = word_data[field]

                    db.table("vocabulary").update(update_data).eq("id", existing.data[0]["id"]).execute()
                    result.imported += 1
                    continue
                elif conflict_resolution == "replace":
                    # Delete existing
                    db.table("vocabulary").delete().eq("id", existing.data[0]["id"]).execute()

            # Insert new
            new_word = {
                "user_id": user_id,
                "word": word,
                "lemma": word_data.get("lemma") or word,
                "translation": translation,
                "language_from": language_from,
                "language_to": language_to,
                "primary_translation": word_data.get("primary_translation"),
                "frequency_rank": word_data.get("frequency_rank"),
                "frequency_level": word_data.get("frequency_level"),
                "example_sentence_original": word_data.get("example_sentence_original"),
                "example_sentence_translation": word_data.get("example_sentence_translation")
            }

            db.table("vocabulary").insert(new_word).execute()
            result.imported += 1

        except Exception as e:
            result.errors.append(f"Row {i+1}: {str(e)}")
            result.skipped += 1

    return result
```

**Step 2: Update api/main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, review, user, generate, import_export

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router)
app.include_router(review.router)
app.include_router(user.router)
app.include_router(generate.router)
app.include_router(import_export.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 3: Commit**

```bash
git add api/routes/import_export.py api/main.py
git commit -m "feat: add vocabulary import/export endpoints"
```

---

## Task 10: Starter Words Endpoint

**Files:**
- Create: `api/services/starter_words.py`
- Create: `api/routes/starter_words.py`
- Modify: `api/main.py` (add router)

**Step 1: Create api/services/starter_words.py**

```python
"""Starter word lists for onboarding."""

# Pre-defined starter words per language (most common, sorted by frequency)
STARTER_WORDS = {
    "es": [  # Spanish
        {"word": "hola", "translation": "hello"},
        {"word": "gracias", "translation": "thank you"},
        {"word": "sí", "translation": "yes"},
        {"word": "no", "translation": "no"},
        {"word": "por favor", "translation": "please"},
        {"word": "el agua", "translation": "water"},
        {"word": "la comida", "translation": "food"},
        {"word": "bueno", "translation": "good"},
        {"word": "malo", "translation": "bad"},
        {"word": "grande", "translation": "big"},
        {"word": "pequeño", "translation": "small"},
        {"word": "la casa", "translation": "house"},
        {"word": "el tiempo", "translation": "time/weather"},
        {"word": "el día", "translation": "day"},
        {"word": "la noche", "translation": "night"},
        {"word": "comer", "translation": "to eat"},
        {"word": "beber", "translation": "to drink"},
        {"word": "hablar", "translation": "to speak"},
        {"word": "trabajar", "translation": "to work"},
        {"word": "vivir", "translation": "to live"},
    ],
    "fr": [  # French
        {"word": "bonjour", "translation": "hello"},
        {"word": "merci", "translation": "thank you"},
        {"word": "oui", "translation": "yes"},
        {"word": "non", "translation": "no"},
        {"word": "s'il vous plaît", "translation": "please"},
        {"word": "l'eau", "translation": "water"},
        {"word": "la nourriture", "translation": "food"},
        {"word": "bon", "translation": "good"},
        {"word": "mauvais", "translation": "bad"},
        {"word": "grand", "translation": "big"},
        {"word": "petit", "translation": "small"},
        {"word": "la maison", "translation": "house"},
        {"word": "le temps", "translation": "time/weather"},
        {"word": "le jour", "translation": "day"},
        {"word": "la nuit", "translation": "night"},
        {"word": "manger", "translation": "to eat"},
        {"word": "boire", "translation": "to drink"},
        {"word": "parler", "translation": "to speak"},
        {"word": "travailler", "translation": "to work"},
        {"word": "vivre", "translation": "to live"},
    ],
    "de": [  # German
        {"word": "hallo", "translation": "hello"},
        {"word": "danke", "translation": "thank you"},
        {"word": "ja", "translation": "yes"},
        {"word": "nein", "translation": "no"},
        {"word": "bitte", "translation": "please"},
        {"word": "das Wasser", "translation": "water"},
        {"word": "das Essen", "translation": "food"},
        {"word": "gut", "translation": "good"},
        {"word": "schlecht", "translation": "bad"},
        {"word": "groß", "translation": "big"},
        {"word": "klein", "translation": "small"},
        {"word": "das Haus", "translation": "house"},
        {"word": "die Zeit", "translation": "time"},
        {"word": "der Tag", "translation": "day"},
        {"word": "die Nacht", "translation": "night"},
        {"word": "essen", "translation": "to eat"},
        {"word": "trinken", "translation": "to drink"},
        {"word": "sprechen", "translation": "to speak"},
        {"word": "arbeiten", "translation": "to work"},
        {"word": "leben", "translation": "to live"},
    ],
}


def get_starter_words(language: str) -> list:
    """Get starter words for a language."""
    return STARTER_WORDS.get(language, [])


def get_supported_languages() -> list:
    """Get list of languages with starter words."""
    return list(STARTER_WORDS.keys())
```

**Step 2: Create api/routes/starter_words.py**

```python
"""Starter words endpoints for onboarding."""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.starter_words import get_starter_words, get_supported_languages

router = APIRouter(prefix="/api/starter-words", tags=["starter_words"])


class StarterWord(BaseModel):
    """Schema for a starter word."""
    word: str
    translation: str


class StarterWordsResponse(BaseModel):
    """Schema for starter words response."""
    language: str
    words: List[StarterWord]


@router.get("/languages")
def list_languages():
    """Get list of languages with starter words available."""
    return {"languages": get_supported_languages()}


@router.get("/{language}", response_model=StarterWordsResponse)
def get_language_starter_words(language: str):
    """Get starter words for a specific language."""
    words = get_starter_words(language)

    if not words:
        raise HTTPException(
            status_code=404,
            detail=f"No starter words available for language: {language}"
        )

    return StarterWordsResponse(
        language=language,
        words=[StarterWord(**w) for w in words]
    )
```

**Step 3: Update api/main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import vocabulary, review, user, generate, import_export, starter_words

app = FastAPI(
    title="InfiniLing API",
    description="Language learning API with spaced repetition",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary.router)
app.include_router(review.router)
app.include_router(user.router)
app.include_router(generate.router)
app.include_router(import_export.router)
app.include_router(starter_words.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

**Step 4: Commit**

```bash
git add api/services/starter_words.py api/routes/starter_words.py api/main.py
git commit -m "feat: add starter words endpoint for onboarding"
```

---

## Task 11: Environment Setup and Local Testing

**Files:**
- Create: `api/.env.example`
- Update: `.gitignore`

**Step 1: Create api/.env.example**

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Optional
DEFAULT_TOKEN_LIMIT=100000
```

**Step 2: Update .gitignore (add api/.env)**

Add this line to .gitignore:

```
api/.env
```

**Step 3: Create local .env from example**

```bash
cp api/.env.example api/.env
# Edit api/.env with your actual keys
```

**Step 4: Test locally**

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then visit http://localhost:8000/api/health

**Step 5: Commit**

```bash
git add api/.env.example .gitignore
git commit -m "chore: add environment setup for API"
```

---

## Summary

This plan creates a complete FastAPI backend with:

1. **Project structure** - FastAPI app with Vercel deployment config
2. **Auth middleware** - Supabase JWT validation
3. **Database schema** - PostgreSQL tables with RLS policies
4. **Vocabulary CRUD** - List, create, read, update, delete
5. **Word enhancement** - GPT lemmatization + translation + frequency
6. **Spaced repetition** - SM-2 algorithm, due words, review sessions
7. **User settings** - Mother tongue, API key, token usage
8. **Story generation** - GPT stories + TTS audio
9. **Import/export** - CSV/JSON with conflict resolution
10. **Starter words** - Pre-defined word lists for onboarding

**Next steps after backend:**
- Set up Supabase project and run schema.sql
- Deploy to Vercel
- Test all endpoints with Postman
- Then proceed to React frontend implementation
