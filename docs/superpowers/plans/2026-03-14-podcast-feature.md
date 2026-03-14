# Podcast Feature Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Podcast tab where users can browse, transcribe, and study foreign-language podcasts with synchronized transcript display and word-click-to-translate.

**Architecture:** Two new backend files (service + routes) following existing FastAPI patterns, two new Supabase tables, one new React page with three internal views, and a shared `useWordPopover` hook extracted from StoryGenerator. Audio streams from original podcast URLs; transcription via OpenAI Whisper.

**Tech Stack:** FastAPI, feedparser (new dep), OpenAI Whisper API, React, Supabase, Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-03-14-podcast-feature-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `api/services/podcast_service.py` | Create | RSS parsing, Whisper transcription, starter podcast config |
| `api/routes/podcast.py` | Create | REST endpoints for podcasts and episodes |
| `api/main.py` | Modify (line ~5, ~15) | Register podcast router |
| `api/schema.sql` | Modify (append) | Add podcasts + podcast_episodes tables + RLS |
| `web/src/services/api.js` | Modify (append) | Add podcastApi namespace |
| `web/src/pages/Podcast.jsx` | Create | Podcast page with 3 views |
| `web/src/hooks/useWordPopover.js` | Create | Extracted word popover hook (shared state + outside-click) |
| `web/src/components/WordPopover.jsx` | Create | Extracted word popover component (shared UI) |
| `web/src/pages/StoryGenerator.jsx` | Modify | Refactor to use shared useWordPopover + WordPopover |
| `web/src/components/Layout.jsx` | Modify (lines 6-9, 100-135) | Add Podcast to nav + mobile nav |
| `web/src/App.jsx` | Modify (lines 8-14, 36) | Add Podcast route |
| `pyproject.toml` | Modify | Add feedparser dependency |
| `tests/test_podcast_service.py` | Create | Tests for RSS parsing + transcription |
| `tests/test_podcast_routes.py` | Create | Tests for podcast endpoints |

---

## Chunk 1: Backend — Database + Podcast Service

### Task 1: Database schema — podcasts + podcast_episodes tables

**Files:**
- Modify: `api/schema.sql` (append at end)

- [ ] **Step 1: Add podcast tables to schema.sql**

Append to `api/schema.sql`:

```sql
-- Podcasts
CREATE TABLE IF NOT EXISTS podcasts (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title text NOT NULL,
    description text,
    rss_url text NOT NULL,
    image_url text,
    language text NOT NULL,
    is_starter boolean DEFAULT false,
    created_at timestamptz DEFAULT now(),
    UNIQUE(user_id, rss_url)
);

ALTER TABLE podcasts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own podcasts"
    ON podcasts FOR ALL
    USING (user_id = auth.uid());

-- Podcast Episodes (only transcribed ones are stored)
CREATE TABLE IF NOT EXISTS podcast_episodes (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    podcast_id uuid REFERENCES podcasts(id) ON DELETE CASCADE NOT NULL,
    guid text NOT NULL,
    title text NOT NULL,
    description text,
    audio_url text NOT NULL,
    duration integer,
    published_at timestamptz,
    transcript jsonb,
    is_transcribed boolean DEFAULT false,
    created_at timestamptz DEFAULT now(),
    UNIQUE(podcast_id, guid)
);

ALTER TABLE podcast_episodes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their podcast episodes"
    ON podcast_episodes FOR ALL
    USING (EXISTS (
        SELECT 1 FROM podcasts
        WHERE podcasts.id = podcast_episodes.podcast_id
        AND podcasts.user_id = auth.uid()
    ));
```

- [ ] **Step 2: Run this SQL in your Supabase dashboard**

Go to Supabase → SQL Editor → paste and run the SQL above. Verify both tables appear in the Table Editor.

- [ ] **Step 3: Commit**

```bash
git add api/schema.sql
git commit -m "db: add podcasts and podcast_episodes tables with RLS"
```

---

### Task 2: Install feedparser dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add feedparser to dependencies**

In `pyproject.toml`, add `"feedparser>=6.0.0"` to the `dependencies` array.

- [ ] **Step 2: Install**

Run: `uv sync`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add feedparser for RSS parsing"
```

---

### Task 3: Podcast service — starter config + RSS parsing

**Files:**
- Create: `api/services/podcast_service.py`
- Create: `tests/test_podcast_service.py`

- [ ] **Step 1: Write failing tests for RSS parsing and starter config**

Create `tests/test_podcast_service.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from api.services.podcast_service import (
    STARTER_PODCASTS,
    parse_rss_feed,
    parse_episodes_from_feed,
)


def test_starter_podcasts_has_all_languages():
    """Each supported language should have starter podcasts."""
    for lang in ["fr", "es", "it", "ru", "zh"]:
        assert lang in STARTER_PODCASTS
        assert len(STARTER_PODCASTS[lang]) >= 1
        for pod in STARTER_PODCASTS[lang]:
            assert "title" in pod
            assert "rss_url" in pod


def test_parse_rss_feed_extracts_metadata():
    """parse_rss_feed should return podcast title, description, image_url."""
    mock_feed = MagicMock()
    mock_feed.feed.title = "My Podcast"
    mock_feed.feed.get.side_effect = lambda k, d="": {
        "subtitle": "A great podcast",
    }.get(k, d)
    mock_feed.feed.get.return_value = "A great podcast"
    # itunes image
    mock_feed.feed.image = MagicMock()
    mock_feed.feed.image.href = "https://example.com/cover.jpg"

    with patch("api.services.podcast_service.feedparser.parse", return_value=mock_feed):
        result = parse_rss_feed("https://example.com/feed.xml")

    assert result["title"] == "My Podcast"
    assert "cover.jpg" in result["image_url"]


def test_parse_episodes_from_feed():
    """parse_episodes_from_feed should extract episode metadata."""
    mock_entry = MagicMock()
    mock_entry.title = "Episode 1"
    mock_entry.get.side_effect = lambda k, d=None: {
        "id": "ep-guid-1",
        "summary": "Ep description",
        "published_parsed": None,
    }.get(k, d)
    mock_entry.links = [
        {"rel": "enclosure", "href": "https://example.com/ep1.mp3", "type": "audio/mpeg"}
    ]
    mock_entry.get.return_value = "ep-guid-1"

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("api.services.podcast_service.feedparser.parse", return_value=mock_feed):
        episodes = parse_episodes_from_feed("https://example.com/feed.xml")

    assert len(episodes) >= 1
    assert episodes[0]["title"] == "Episode 1"
    assert episodes[0]["audio_url"] == "https://example.com/ep1.mp3"
    assert episodes[0]["guid"] == "ep-guid-1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_podcast_service.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement podcast_service.py — starter config + RSS parsing**

Create `api/services/podcast_service.py`:

```python
"""Podcast service: RSS parsing, Whisper transcription, starter podcast config."""

import tempfile
import os
from datetime import datetime
from calendar import timegm
from time import mktime

import feedparser
import requests
from openai import OpenAI


# Starter podcasts per language — seeded on first visit
STARTER_PODCASTS = {
    "fr": [
        {
            "title": "Tout un monde",
            "rss_url": "https://feeds.rts.ch/info-tout-un-monde.xml",
            "image_url": "https://www.rts.ch/2024/06/28/17/31/14928029.image/16x9",
            "description": "RTS — Actualité internationale",
        },
        {
            "title": "Journal en français facile",
            "rss_url": "https://savoirs.rfi.fr/fr/apprendre-enseigner/langue-francaise/journal-en-francais-facile/podcast",
            "image_url": "",
            "description": "RFI — Actualité simplifiée",
        },
        {
            "title": "InnerFrench",
            "rss_url": "https://feeds.soundcloud.com/users/soundcloud:users:304682547/sounds.rss",
            "image_url": "",
            "description": "Hugo Cotton — Intermediate French",
        },
    ],
    "es": [
        {
            "title": "News in Slow Spanish",
            "rss_url": "https://www.newsinslowspanish.com/latino/podcast/feed",
            "image_url": "",
            "description": "Current events in slow Spanish",
        },
    ],
    "it": [
        {
            "title": "News in Slow Italian",
            "rss_url": "https://www.newsinslowitalian.com/podcast/feed",
            "image_url": "",
            "description": "Current events in slow Italian",
        },
    ],
    "ru": [
        {
            "title": "Russian Podcast",
            "rss_url": "https://russianpodcast.eu/feed/podcast",
            "image_url": "",
            "description": "Slow Russian for learners",
        },
    ],
    "zh": [
        {
            "title": "ChinesePod",
            "rss_url": "https://chinesepod.com/feed",
            "image_url": "",
            "description": "Learn Mandarin Chinese",
        },
    ],
}


def parse_rss_feed(rss_url: str) -> dict:
    """Parse an RSS feed URL and return podcast metadata.

    Returns dict with keys: title, description, image_url
    """
    feed = feedparser.parse(rss_url)
    title = feed.feed.get("title", "Unknown Podcast")
    description = feed.feed.get("subtitle", "") or feed.feed.get("summary", "")

    # Try itunes:image first, then standard image
    image_url = ""
    itunes_image = feed.feed.get("image")
    if itunes_image and hasattr(itunes_image, "href"):
        image_url = itunes_image.href
    elif hasattr(feed.feed, "itunes_image"):
        image_url = feed.feed.itunes_image.get("href", "")

    return {"title": title, "description": description, "image_url": image_url}


def parse_episodes_from_feed(rss_url: str, limit: int = 50) -> list[dict]:
    """Parse RSS feed and return list of episode dicts.

    Each episode has: guid, title, description, audio_url, duration, published_at
    """
    feed = feedparser.parse(rss_url)
    episodes = []

    for entry in feed.entries[:limit]:
        # Find audio enclosure
        audio_url = ""
        for link in getattr(entry, "links", []):
            if link.get("rel") == "enclosure" and "audio" in link.get("type", ""):
                audio_url = link.get("href", "")
                break

        if not audio_url:
            continue  # Skip episodes without audio

        # Parse duration (itunes:duration can be seconds or HH:MM:SS)
        duration = None
        raw_duration = entry.get("itunes_duration")
        if raw_duration:
            try:
                if ":" in str(raw_duration):
                    parts = str(raw_duration).split(":")
                    if len(parts) == 3:
                        duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration = int(parts[0]) * 60 + int(parts[1])
                else:
                    duration = int(raw_duration)
            except (ValueError, TypeError):
                pass

        # Parse publish date
        published_at = None
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            try:
                published_at = datetime.utcfromtimestamp(timegm(published_parsed)).isoformat()
            except (ValueError, TypeError, OverflowError):
                pass

        episodes.append({
            "guid": entry.get("id", entry.get("link", "")),
            "title": entry.get("title", "Untitled"),
            "description": entry.get("summary", ""),
            "audio_url": audio_url,
            "duration": duration,
            "published_at": published_at,
        })

    return episodes


def transcribe_audio(audio_url: str, api_key: str) -> list[dict]:
    """Download audio from URL and transcribe with OpenAI Whisper.

    Returns list of segment dicts: [{start, end, text}, ...]
    Raises ValueError if file too large (>25MB).
    """
    # Check file size before downloading
    head = requests.head(audio_url, allow_redirects=True, timeout=10)
    content_length = int(head.headers.get("content-length", 0))
    if content_length > 25 * 1024 * 1024:
        raise ValueError(f"Audio file too large ({content_length // (1024*1024)}MB). Whisper API limit is 25MB.")

    # Download to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    try:
        response = requests.get(audio_url, stream=True, timeout=300)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()

        # Transcribe with Whisper
        client = OpenAI(api_key=api_key)
        with open(tmp.name, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        # Extract segments (OpenAI SDK returns objects with attribute access)
        segments = []
        for seg in result.segments:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })

        return segments

    finally:
        os.unlink(tmp.name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_podcast_service.py -v`
Expected: PASS

- [ ] **Step 5: Write test for transcribe_audio**

Add to `tests/test_podcast_service.py`:

```python
def test_transcribe_audio_rejects_large_files():
    """Should raise ValueError if audio file exceeds 25MB."""
    mock_response = MagicMock()
    mock_response.headers = {"content-length": str(30 * 1024 * 1024)}

    with patch("api.services.podcast_service.requests.head", return_value=mock_response):
        with pytest.raises(ValueError, match="too large"):
            from api.services.podcast_service import transcribe_audio
            transcribe_audio("https://example.com/huge.mp3", "fake-key")
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_podcast_service.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add api/services/podcast_service.py tests/test_podcast_service.py
git commit -m "feat: add podcast service with RSS parsing and Whisper transcription"
```

---

### Task 4: Podcast routes — CRUD + transcribe endpoints

**Files:**
- Create: `api/routes/podcast.py`
- Modify: `api/main.py` (lines ~5, ~15)

- [ ] **Step 1: Create podcast routes**

Create `api/routes/podcast.py`:

```python
"""Podcast routes: browse, add, delete podcasts; list episodes; transcribe."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.dependencies import get_current_user_id, get_supabase
from api.services.podcast_service import (
    STARTER_PODCASTS,
    parse_rss_feed,
    parse_episodes_from_feed,
    transcribe_audio,
)

router = APIRouter(prefix="/api/podcasts", tags=["podcasts"])


class AddPodcastRequest(BaseModel):
    rss_url: str
    language: str


class TranscribeRequest(BaseModel):
    guid: str
    title: str
    audio_url: str
    duration: Optional[int] = None
    published_at: Optional[str] = None


@router.get("")
def list_podcasts(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """List user's podcasts. Auto-seeds starters if none exist for language."""
    # Get user's language setting
    settings = db.table("user_settings").select("last_language").eq("user_id", user_id).maybe_single().execute()
    language = settings.data.get("last_language", "") if settings.data else ""

    # Check if user has any podcasts
    existing = db.table("podcasts").select("id").eq("user_id", user_id).execute()

    # Seed starters if none exist
    if not existing.data and language in STARTER_PODCASTS:
        for starter in STARTER_PODCASTS[language]:
            db.table("podcasts").insert({
                "user_id": user_id,
                "title": starter["title"],
                "description": starter.get("description", ""),
                "rss_url": starter["rss_url"],
                "image_url": starter.get("image_url", ""),
                "language": language,
                "is_starter": True,
            }).execute()

    # Return all podcasts
    result = db.table("podcasts").select("*").eq("user_id", user_id).order("created_at").execute()
    return {"podcasts": result.data}


@router.post("")
def add_podcast(
    body: AddPodcastRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Add a podcast from RSS URL."""
    try:
        metadata = parse_rss_feed(body.rss_url)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse RSS feed")

    result = db.table("podcasts").insert({
        "user_id": user_id,
        "title": metadata["title"],
        "description": metadata["description"],
        "rss_url": body.rss_url,
        "image_url": metadata["image_url"],
        "language": body.language,
        "is_starter": False,
    }).execute()

    return result.data[0]


@router.delete("/{podcast_id}")
def delete_podcast(
    podcast_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Delete a podcast and its episodes (cascade)."""
    result = db.table("podcasts").delete().eq("id", podcast_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return {"ok": True}


@router.get("/{podcast_id}/episodes")
def list_episodes(
    podcast_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """List episodes from RSS feed, merging transcription status from DB."""
    # Verify ownership
    podcast = db.table("podcasts").select("rss_url").eq("id", podcast_id).eq("user_id", user_id).maybe_single().execute()
    if not podcast.data:
        raise HTTPException(status_code=404, detail="Podcast not found")

    # Fetch episodes from RSS
    try:
        episodes = parse_episodes_from_feed(podcast.data["rss_url"])
    except Exception:
        raise HTTPException(status_code=400, detail="Could not fetch podcast feed")

    # Get transcribed episodes from DB
    transcribed = db.table("podcast_episodes").select("guid, id").eq("podcast_id", podcast_id).eq("is_transcribed", True).execute()
    transcribed_map = {row["guid"]: row["id"] for row in (transcribed.data or [])}

    # Merge transcription status
    for ep in episodes:
        ep["is_transcribed"] = ep["guid"] in transcribed_map
        ep["episode_id"] = transcribed_map.get(ep["guid"])

    return {"episodes": episodes}


@router.post("/{podcast_id}/episodes/transcribe")
def transcribe_episode(
    podcast_id: str,
    body: TranscribeRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Transcribe an episode using Whisper API."""
    # Verify ownership
    podcast = db.table("podcasts").select("id").eq("id", podcast_id).eq("user_id", user_id).maybe_single().execute()
    if not podcast.data:
        raise HTTPException(status_code=404, detail="Podcast not found")

    # Get API key — same pattern as generate.py
    from api.config import get_settings
    api_key = get_settings().openai_api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    # Transcribe
    try:
        segments = transcribe_audio(body.audio_url, api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Transcription failed")

    # Store episode with transcript (upsert by podcast_id + guid unique constraint)
    result = db.table("podcast_episodes").upsert({
        "podcast_id": podcast_id,
        "guid": body.guid,
        "title": body.title,
        "audio_url": body.audio_url,
        "duration": body.duration,
        "published_at": body.published_at,
        "transcript": segments,
        "is_transcribed": True,
    }, on_conflict="podcast_id,guid").execute()

    return result.data[0]


@router.get("/{podcast_id}/episodes/{episode_id}")
def get_episode(
    podcast_id: str,
    episode_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_supabase),
):
    """Get a transcribed episode with its transcript."""
    result = (
        db.table("podcast_episodes")
        .select("*, podcasts!inner(user_id)")
        .eq("id", episode_id)
        .eq("podcast_id", podcast_id)
        .eq("podcasts.user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Remove the join data
    episode = {k: v for k, v in result.data.items() if k != "podcasts"}
    return episode
```

- [ ] **Step 2: Register the router in main.py**

In `api/main.py`, add:
- Import: `from api.routes import podcast` (alongside existing imports)
- Registration: `app.include_router(podcast.router)` (alongside existing router includes)

- [ ] **Step 3: Verify the server starts**

Run: `uvicorn api.main:app --reload`
Check: No import errors. Visit `http://localhost:8000/docs` — podcast endpoints should appear.

- [ ] **Step 4: Commit**

```bash
git add api/routes/podcast.py api/main.py
git commit -m "feat: add podcast routes — CRUD, episode listing, transcription"
```

---

## Chunk 2: Frontend — Navigation, API, useWordPopover Hook

### Task 5: Add podcastApi to frontend API service

**Files:**
- Modify: `web/src/services/api.js` (append)

- [ ] **Step 1: Add podcastApi namespace**

Add to end of `web/src/services/api.js` (before the final export if there is one, or just append):

```javascript
export const podcastApi = {
  list: () => api.get('/api/podcasts'),
  add: (data) => api.post('/api/podcasts', data),
  remove: (id) => api.delete(`/api/podcasts/${id}`),
  episodes: (podcastId) => api.get(`/api/podcasts/${podcastId}/episodes`),
  transcribe: (podcastId, data) => api.post(`/api/podcasts/${podcastId}/episodes/transcribe`, data),
  getEpisode: (podcastId, episodeId) => api.get(`/api/podcasts/${podcastId}/episodes/${episodeId}`),
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/services/api.js
git commit -m "feat: add podcastApi to frontend API service"
```

---

### Task 6: Extract useWordPopover hook + WordPopover component from StoryGenerator

**Concept:** A React "hook" is a reusable function that encapsulates state logic. A "component" is a reusable piece of UI. Right now StoryGenerator has both the popover state management and the popover UI embedded directly. We'll extract both into shared files so StoryGenerator and Podcast can reuse them without duplication.

**Files:**
- Create: `web/src/hooks/useWordPopover.js`
- Create: `web/src/components/WordPopover.jsx`
- Modify: `web/src/pages/StoryGenerator.jsx`

- [ ] **Step 1: Read StoryGenerator.jsx fully to identify word popover logic**

Read `web/src/pages/StoryGenerator.jsx` — identify:
- State: `popover` (stores `{word, rect}` or null)
- Handlers: `handleWordDoubleClick`, touch handlers for mobile
- The `WordPopover` component that renders the translation + "Add to Vocabulary" button
- The `enhance` API call and `addToVocabulary` logic inside WordPopover
- Close-on-outside-click/touchstart behavior

Note the exact shape of data: StoryGenerator stores a DOMRect (`rect`) for positioning, not raw `x, y`.

- [ ] **Step 2: Create useWordPopover hook**

Create `web/src/hooks/useWordPopover.js`. This hook manages popover state and outside-click/touch dismissal. It stores `rect` (a DOMRect) for positioning, matching StoryGenerator's existing pattern.

```javascript
import { useState, useEffect, useCallback } from 'react'

/**
 * useWordPopover — shared hook for word-click-to-translate popover.
 *
 * Stores { word, rect } where rect is a DOMRect from getBoundingClientRect().
 * Both StoryGenerator and Podcast use this hook.
 */
export default function useWordPopover() {
  const [popover, setPopover] = useState(null)

  const openPopover = useCallback((word, rect) => {
    setPopover({ word, rect })
  }, [])

  const closePopover = useCallback(() => {
    setPopover(null)
  }, [])

  // Close on outside click/touch
  useEffect(() => {
    if (!popover) return
    const handleDismiss = (e) => {
      if (e.target.closest('.word-popover')) return
      closePopover()
    }
    // Delay attach to avoid immediate trigger from the click that opened it
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleDismiss)
      document.addEventListener('touchstart', handleDismiss)
    }, 100)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('mousedown', handleDismiss)
      document.removeEventListener('touchstart', handleDismiss)
    }
  }, [popover, closePopover])

  return { popover, openPopover, closePopover }
}
```

- [ ] **Step 3: Extract WordPopover component**

Create `web/src/components/WordPopover.jsx`. Move the existing WordPopover rendering logic from StoryGenerator into this shared component. It receives `word`, `rect`, `language`, `motherTongue`, and `onClose` as props.

Read StoryGenerator.jsx carefully and extract the WordPopover component as-is (the enhance API call, save-to-vocabulary flow, positioning logic using `rect`, frequency display, close button). Keep the same structure and styling — just move it to its own file.

The component should:
- Use `rect.left + rect.width / 2` for horizontal centering
- Use `rect.bottom + 8` for vertical position (below the word)
- Clamp horizontal position to stay on screen
- Call `vocabularyApi.enhance()` on mount
- Have "Add to Vocabulary" button calling `vocabularyApi.create()`
- Use Unicode-aware regex for word cleaning: `word.replace(/[^\p{L}\p{M}'-]/gu, '')` (this handles accented chars, Cyrillic, Chinese)

- [ ] **Step 4: Refactor StoryGenerator to use shared hook + component**

In `StoryGenerator.jsx`:
- Import: `import useWordPopover from '../hooks/useWordPopover'`
- Import: `import WordPopover from '../components/WordPopover'`
- Replace `const [popover, setPopover] = useState(null)` with `const { popover, openPopover, closePopover } = useWordPopover()`
- Update word click handlers to call `openPopover(word, rect)` instead of `setPopover({word, rect})`
- Replace inline WordPopover with: `{popover && <WordPopover word={popover.word} rect={popover.rect} language={language} motherTongue={settings?.mother_tongue} onClose={closePopover} />}`
- Remove the old WordPopover function definition and old outside-click effect

- [ ] **Step 5: Verify StoryGenerator still works**

Start the dev server, navigate to Story page, generate a story, double-click/long-press a word — popover should still appear and function correctly. Test on both desktop (double-click) and mobile (long-press).

- [ ] **Step 6: Commit**

```bash
git add web/src/hooks/useWordPopover.js web/src/components/WordPopover.jsx web/src/pages/StoryGenerator.jsx
git commit -m "refactor: extract useWordPopover hook and WordPopover component"
```

---

### Task 7: Add Podcast to navigation + routing

**Files:**
- Modify: `web/src/components/Layout.jsx` (lines 6-9, 100-135)
- Modify: `web/src/App.jsx` (lines 8-14, 36)

- [ ] **Step 1: Add Podcast to navItems in Layout.jsx**

In `Layout.jsx`, add to `navItems` array (line ~9):

```javascript
const navItems = [
  { path: '/vocabulary', label: 'Vocabulary' },
  { path: '/review', label: 'Review' },
  { path: '/story', label: 'Story' },
  { path: '/podcast', label: 'Podcast' },
]
```

- [ ] **Step 2: Add Podcast to mobile bottom nav in Layout.jsx**

Add a new `<Link>` for Podcast in the mobile bottom nav section (after the Story link, around line ~125). Use a headphone icon:

```jsx
<Link
  to="/podcast"
  className={`flex flex-col items-center gap-1 px-6 py-2 transition-colors ${
    location.pathname === '/podcast' ? 'text-accent' : 'text-muted'
  }`}
>
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m-4 0h8m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
  </svg>
  <span className="text-xs font-medium">Podcast</span>
</Link>
```

- [ ] **Step 3: Add Podcast route to App.jsx**

In `App.jsx`:
- Add lazy import: `const Podcast = lazy(() => import('./pages/Podcast'))`
- Add route inside the Layout routes: `<Route path="/podcast" element={<Podcast />} />`

- [ ] **Step 4: Create a placeholder Podcast.jsx**

Create `web/src/pages/Podcast.jsx` with a minimal placeholder so the route works:

```jsx
export default function Podcast() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-text">Podcast</h1>
      <p className="text-muted mt-2">Coming soon...</p>
    </div>
  )
}
```

- [ ] **Step 5: Verify navigation works**

Start the dev server, check that "Podcast" appears in the nav bar and mobile nav. Click it — should show the placeholder page.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/Layout.jsx web/src/App.jsx web/src/pages/Podcast.jsx
git commit -m "feat: add Podcast tab to navigation and routing"
```

---

## Chunk 3: Frontend — Podcast Page (Views 1-3)

### Task 8: Podcast page — View 1 (Podcast List) + View 2 (Episode List)

**Files:**
- Modify: `web/src/pages/Podcast.jsx`

- [ ] **Step 1: Implement Podcast list and Episode list views**

Replace the placeholder `Podcast.jsx` with the full component. Key React concepts:

- **`view` state** — a string (`'list'`, `'episodes'`, `'study'`) that controls which UI is shown. React re-renders when state changes.
- **Conditional rendering** — `{view === 'list' && <ListUI />}` only renders when the condition is true.
- **`useEffect`** — runs side effects (API calls) when dependencies change. `useEffect(() => { fetch... }, [])` runs once on mount.

```jsx
import { useState, useEffect, useRef, useCallback } from 'react'
import { podcastApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import useWordPopover from '../hooks/useWordPopover'
import WordPopover from '../components/WordPopover'

export default function Podcast() {
  const { settings } = useAuthStore()

  // Navigation state — controls which of the 3 views is shown
  const [view, setView] = useState('list') // 'list' | 'episodes' | 'study'
  const [selectedPodcast, setSelectedPodcast] = useState(null)
  const [selectedEpisode, setSelectedEpisode] = useState(null)

  // Podcast list state
  const [podcasts, setPodcasts] = useState([])
  const [loadingPodcasts, setLoadingPodcasts] = useState(true)
  const [rssUrl, setRssUrl] = useState('')
  const [addError, setAddError] = useState('')
  const [adding, setAdding] = useState(false)

  // Episode list state
  const [episodes, setEpisodes] = useState([])
  const [loadingEpisodes, setLoadingEpisodes] = useState(false)
  const [transcribingGuid, setTranscribingGuid] = useState(null)

  // Study mode state
  const [transcript, setTranscript] = useState([])
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(-1)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const audioRef = useRef(null)
  const transcriptRef = useRef(null)

  // Preview audio (episode list play button)
  const [previewAudioUrl, setPreviewAudioUrl] = useState(null)
  const previewAudioRef = useRef(null)

  // Word popover (shared hook)
  const { popover, openPopover, closePopover } = useWordPopover()

  // ── Fetch podcasts on mount ──
  useEffect(() => {
    podcastApi.list()
      .then(({ data }) => setPodcasts(data.podcasts || []))
      .catch(console.error)
      .finally(() => setLoadingPodcasts(false))
  }, [])

  // ── Sync playback rate ──
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = playbackRate
  }, [playbackRate])

  // ── Add podcast from RSS ──
  const handleAddPodcast = async () => {
    if (!rssUrl.trim()) return
    setAdding(true)
    setAddError('')
    try {
      const { data } = await podcastApi.add({
        rss_url: rssUrl.trim(),
        language: settings?.last_language || 'fr',
      })
      setPodcasts(prev => [...prev, data])
      setRssUrl('')
    } catch (err) {
      setAddError(err.response?.data?.detail || 'Could not add podcast')
    } finally {
      setAdding(false)
    }
  }

  // ── Open podcast → load episodes ──
  const openPodcast = async (podcast) => {
    setSelectedPodcast(podcast)
    setView('episodes')
    setLoadingEpisodes(true)
    try {
      const { data } = await podcastApi.episodes(podcast.id)
      setEpisodes(data.episodes || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingEpisodes(false)
    }
  }

  // ── Transcribe episode ──
  const handleTranscribe = async (episode) => {
    setTranscribingGuid(episode.guid)
    try {
      const { data } = await podcastApi.transcribe(selectedPodcast.id, {
        guid: episode.guid,
        title: episode.title,
        audio_url: episode.audio_url,
        duration: episode.duration,
        published_at: episode.published_at,
      })
      // Update episode in list
      setEpisodes(prev => prev.map(ep =>
        ep.guid === episode.guid
          ? { ...ep, is_transcribed: true, episode_id: data.id }
          : ep
      ))
    } catch (err) {
      alert(err.response?.data?.detail || 'Transcription failed')
    } finally {
      setTranscribingGuid(null)
    }
  }

  // ── Open study mode ──
  const openStudy = async (episode) => {
    try {
      const { data } = await podcastApi.getEpisode(selectedPodcast.id, episode.episode_id)
      setSelectedEpisode(data)
      setTranscript(data.transcript || [])
      setCurrentSegmentIndex(-1)
      setCurrentTime(0)
      setIsPlaying(false)
      setView('study')
    } catch (err) {
      console.error(err)
    }
  }

  // ── Audio time update → find current segment ──
  const handleTimeUpdate = useCallback(() => {
    if (!audioRef.current) return
    const t = audioRef.current.currentTime
    setCurrentTime(t)
    const idx = transcript.findIndex(seg => t >= seg.start && t < seg.end)
    if (idx !== currentSegmentIndex) {
      setCurrentSegmentIndex(idx)
      // Auto-scroll to current segment
      const el = document.getElementById(`segment-${idx}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [transcript, currentSegmentIndex])

  // ── Word click handler ──
  const handleWordClick = (word, e) => {
    // Unicode-aware cleaning — works with French accents, Cyrillic, Chinese, etc.
    const clean = word.replace(/[^\p{L}\p{M}'-]/gu, '').trim()
    if (!clean) return
    closePopover()
    const rect = e.target.getBoundingClientRect()
    openPopover(clean, rect)
  }

  // ── Format time ──
  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  // ── Format duration for episode list ──
  const formatDuration = (s) => {
    if (!s) return ''
    if (s >= 3600) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}min`
    return `${Math.floor(s / 60)} min`
  }

  // ═══════════════════════════════════════════
  // VIEW 1: PODCAST LIST
  // ═══════════════════════════════════════════
  if (view === 'list') {
    return (
      <div>
        {/* RSS input */}
        <form onSubmit={(e) => { e.preventDefault(); handleAddPodcast() }} className="mb-6">
          <input
            type="text"
            value={rssUrl}
            onChange={(e) => setRssUrl(e.target.value)}
            placeholder="Add your favourite podcast (RSS link)"
            className="w-full px-4 py-3 bg-surface border border-border rounded-lg text-text placeholder-muted focus:outline-none focus:border-accent"
            disabled={adding}
          />
          {addError && <p className="text-red-400 text-sm mt-2">{addError}</p>}
        </form>

        {/* Podcast grid */}
        {loadingPodcasts ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {podcasts.map((pod) => (
              <button
                key={pod.id}
                onClick={() => openPodcast(pod)}
                className="aspect-square rounded-xl overflow-hidden bg-surface border border-border hover:border-accent transition-colors"
              >
                {pod.image_url ? (
                  <img src={pod.image_url} alt={pod.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl bg-surface">
                    🎙️
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ═══════════════════════════════════════════
  // VIEW 2: EPISODE LIST
  // ═══════════════════════════════════════════
  if (view === 'episodes') {
    return (
      <div>
        {/* Back button */}
        <button
          onClick={() => { setView('list'); setPreviewAudioUrl(null) }}
          className="text-accent text-sm mb-4 hover:underline"
        >
          ← Back to Podcasts
        </button>

        {/* Podcast header */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-xl overflow-hidden bg-surface border border-border flex-shrink-0">
            {selectedPodcast?.image_url ? (
              <img src={selectedPodcast.image_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-2xl">🎙️</div>
            )}
          </div>
          <div>
            <h2 className="text-lg font-bold text-text">{selectedPodcast?.title}</h2>
            <p className="text-sm text-muted">{selectedPodcast?.description}</p>
          </div>
        </div>

        {/* Preview audio player */}
        {previewAudioUrl && (
          <div className="mb-4 p-3 bg-surface border border-border rounded-lg">
            <audio ref={previewAudioRef} src={previewAudioUrl} controls className="w-full" />
          </div>
        )}

        {/* Episode list */}
        {loadingEpisodes ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {episodes.map((ep) => (
              <div
                key={ep.guid}
                className={`p-4 bg-surface rounded-xl border ${ep.is_transcribed ? 'border-accent' : 'border-border'}`}
              >
                <div className="flex justify-between items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-sm text-text">{ep.title}</h3>
                    <p className="text-xs text-muted mt-1">
                      {ep.published_at && new Date(ep.published_at).toLocaleDateString()}
                      {ep.duration && ` · ${formatDuration(ep.duration)}`}
                    </p>
                    {ep.is_transcribed && (
                      <p className="text-xs text-accent mt-1">✓ Transcribed</p>
                    )}
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {ep.is_transcribed ? (
                      <button
                        onClick={() => openStudy(ep)}
                        className="px-3 py-1.5 bg-accent text-white text-xs rounded-md hover:bg-accent/90"
                      >
                        ▶ Study
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={() => setPreviewAudioUrl(ep.audio_url)}
                          className="px-3 py-1.5 bg-surface border border-border text-muted text-xs rounded-md hover:text-text"
                        >
                          ▶ Play
                        </button>
                        <button
                          onClick={() => handleTranscribe(ep)}
                          disabled={transcribingGuid === ep.guid}
                          className="px-3 py-1.5 bg-accent text-white text-xs rounded-md hover:bg-accent/90 disabled:opacity-50"
                        >
                          {transcribingGuid === ep.guid ? 'Transcribing...' : 'Save & Transcribe'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ═══════════════════════════════════════════
  // VIEW 3: STUDY MODE (next task)
  // ═══════════════════════════════════════════
  return <div>Study mode — implemented in next task</div>
}
```

- [ ] **Step 2: Verify Views 1 and 2 work**

Start frontend + backend. Navigate to Podcast tab:
- Starter podcasts should load (cover tiles)
- Click a tile → episode list loads
- "Play" button plays preview audio
- "Save & Transcribe" triggers transcription (test with a short podcast)

- [ ] **Step 3: Commit**

```bash
git add web/src/pages/Podcast.jsx
git commit -m "feat: implement podcast list and episode list views"
```

---

### Task 9: Podcast page — View 3 (Study Mode with transcript sync)

**Files:**
- Modify: `web/src/pages/Podcast.jsx`

- [ ] **Step 1: Replace the study mode placeholder**

Replace the last return statement (the study mode placeholder) with the full study view. Key concepts:

- **`timeupdate` event** — the `<audio>` element fires this event as it plays. We use it to find which transcript segment matches the current time.
- **`useCallback`** — memoizes a function so it doesn't get recreated on every render (performance optimization).
- **Segment highlighting** — we map over transcript segments and apply a CSS class to the one matching `currentSegmentIndex`.
- **Seekable progress bar** — clicking the progress bar calculates the time position and sets `audioRef.current.currentTime`.

Replace the final `return` block with:

```jsx
  // ═══════════════════════════════════════════
  // VIEW 3: STUDY MODE
  // ═══════════════════════════════════════════
  return (
    <div>
      {/* Back button */}
      <button
        onClick={() => { setView('episodes'); setIsPlaying(false); if (audioRef.current) audioRef.current.pause() }}
        className="text-accent text-sm mb-4 hover:underline"
      >
        ← Back to Episodes
      </button>

      {/* Audio player */}
      <div className="bg-surface border border-border rounded-xl p-4 mb-6">
        <audio
          ref={audioRef}
          src={selectedEpisode?.audio_url}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />
        <div className="flex items-center gap-3">
          {/* Play/pause */}
          <button
            onClick={() => {
              if (isPlaying) audioRef.current?.pause()
              else audioRef.current?.play()
            }}
            className="w-10 h-10 rounded-full bg-accent text-white flex items-center justify-center text-lg flex-shrink-0"
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          {/* Progress bar */}
          <div className="flex-1">
            <div
              className="h-1.5 bg-border rounded-full cursor-pointer relative"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const ratio = (e.clientX - rect.left) / rect.width
                if (audioRef.current) audioRef.current.currentTime = ratio * duration
              }}
            >
              <div
                className="h-full bg-accent rounded-full"
                style={{ width: duration ? `${(currentTime / duration) * 100}%` : '0%' }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-muted">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Speed controls */}
          <div className="flex gap-1 flex-shrink-0">
            {[0.75, 1, 1.25].map((rate) => (
              <button
                key={rate}
                onClick={() => setPlaybackRate(rate)}
                className={`px-2 py-1 text-xs rounded ${
                  playbackRate === rate
                    ? 'bg-accent text-white'
                    : 'bg-surface border border-border text-muted hover:text-text'
                }`}
              >
                {rate}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Transcript */}
      <div ref={transcriptRef} className="leading-relaxed text-base">
        {transcript.map((seg, i) => (
          <span
            key={i}
            id={`segment-${i}`}
            className={`inline ${
              i === currentSegmentIndex
                ? 'bg-accent/10 border-l-2 border-accent pl-1.5 rounded-sm'
                : 'text-muted'
            }`}
            style={{ transition: 'all 0.3s ease' }}
          >
            {seg.text.split(/(\s+)/).map((token, j) => {
              const isWord = /\p{L}/u.test(token) // Unicode-aware: matches any letter
              return isWord ? (
                <span
                  key={j}
                  onClick={(e) => handleWordClick(token, e)}
                  className="cursor-pointer hover:underline hover:decoration-dotted hover:text-text"
                >
                  {token}
                </span>
              ) : (
                <span key={j}>{token}</span>
              )
            })}
            {' '}
          </span>
        ))}
      </div>

      {/* Word popover — uses shared component from components/WordPopover.jsx */}
      {popover && (
        <WordPopover
          word={popover.word}
          rect={popover.rect}
          language={settings?.last_language}
          motherTongue={settings?.mother_tongue}
          onClose={closePopover}
        />
      )}
    </div>
  )
```

- [ ] **Step 2: Verify WordPopover import is in place**

`Podcast.jsx` already imports the shared `WordPopover` component (added in Task 8's imports). No need to create a duplicate — the same component extracted in Task 6 is reused here. It receives `word`, `rect`, `language`, `motherTongue`, and `onClose` props.

- [ ] **Step 3: Test the full study flow**

1. Navigate to Podcast tab
2. Click a podcast tile
3. Transcribe an episode (or use one already transcribed)
4. Click "Study" — transcript should display
5. Play audio — current segment should highlight and auto-scroll
6. Click a word — popover should appear with translation
7. Click "Add to Vocabulary" — word should save
8. Test speed controls (0.75x, 1x, 1.25x)

- [ ] **Step 4: Commit**

```bash
git add web/src/pages/Podcast.jsx
git commit -m "feat: implement podcast study mode with transcript sync and word popover"
```

---

## Chunk 4: Polish and Final Integration

### Task 10: Delete podcast functionality + error states

**Files:**
- Modify: `web/src/pages/Podcast.jsx`

- [ ] **Step 1: Add delete button to podcast tiles**

In the podcast grid (View 1), add a small delete (×) button on each tile that appears on hover. Use a `deletingId` state to track which podcast is being deleted:

```jsx
// Add to state declarations:
const [deletingId, setDeletingId] = useState(null)

// Delete handler:
const handleDelete = async (e, podcastId) => {
  e.stopPropagation() // Prevent opening the podcast
  if (!confirm('Remove this podcast?')) return
  setDeletingId(podcastId)
  try {
    await podcastApi.remove(podcastId)
    setPodcasts(prev => prev.filter(p => p.id !== podcastId))
  } catch (err) {
    console.error(err)
  } finally {
    setDeletingId(null)
  }
}
```

Add a delete button overlay on each tile:

```jsx
<button
  key={pod.id}
  onClick={() => openPodcast(pod)}
  className="aspect-square rounded-xl overflow-hidden bg-surface border border-border hover:border-accent transition-colors relative group"
>
  {/* ... existing image/emoji ... */}
  <div
    onClick={(e) => handleDelete(e, pod.id)}
    className="absolute top-1 right-1 w-6 h-6 bg-black/60 rounded-full flex items-center justify-center text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity"
  >
    ✕
  </div>
</button>
```

- [ ] **Step 2: Test delete flow**

Verify: hover over a podcast tile → × appears → click → confirm → podcast is removed from grid.

- [ ] **Step 3: Commit**

```bash
git add web/src/pages/Podcast.jsx
git commit -m "feat: add podcast delete functionality"
```

---

### Task 11: End-to-end manual testing

- [ ] **Step 1: Test full flow with a real podcast**

Run both backend and frontend. Test the complete flow:

1. Open Podcast tab — starter podcasts should load as cover tiles
2. Paste a real RSS feed URL (e.g., `https://feeds.rts.ch/info-tout-un-monde.xml`) → podcast appears in grid
3. Click the podcast → episodes list loads with titles, dates, durations
4. Click "Play" on an episode → audio preview plays
5. Click "Save & Transcribe" on a short episode → loading spinner → transcription completes → "Study" button appears
6. Click "Study" → transcript displays, audio plays, segments highlight
7. Click a word → popover with translation appears
8. Click "Add to Vocabulary" → word saved (check Vocabulary tab)
9. Test speed controls
10. Back navigation works at every level
11. Delete a podcast → removed from grid
12. Mobile nav shows Podcast icon

- [ ] **Step 2: Fix any issues found during testing**

- [ ] **Step 3: Final commit**

```bash
git status  # Review changes before committing
git add web/src/pages/Podcast.jsx
git commit -m "fix: address issues found during end-to-end testing"
```
