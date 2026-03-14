# Podcast Feature — Design Spec

## Overview

Add a "Podcast" tab to InfiniLing (right of "Story") that lets users browse, listen to, and study foreign-language podcasts. Users can preview episodes, transcribe them via OpenAI Whisper, and interact with the transcript the same way they do with stories — clicking unknown words to translate and add to vocabulary.

## Goals

- Let users study real-world spoken content in their target language
- Reuse existing word-interaction patterns from story mode (popover, translate, add to vocabulary)
- Keep infrastructure simple: no file storage, no new external services beyond OpenAI Whisper

## Podcast Sources

- **Curated starter podcasts**: ~3 per language, stored as a seed config (similar to starter words). Each entry has: RSS URL, title, description, image URL, language code.
- **User-added podcasts**: user pastes an RSS feed URL into an input bar. The app parses the feed to extract podcast metadata (title, description, image) and episode list.
- No distinction in the UI between starter and user-added podcasts — they appear as a flat grid of cover tiles.

## Data Model

### `podcasts` table

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK, default gen_random_uuid() |
| user_id | uuid | FK to auth.users |
| title | text | Parsed from RSS feed |
| description | text | Parsed from RSS feed |
| rss_url | text | The feed URL |
| image_url | text | Podcast cover art URL |
| language | text | Language code (e.g., "fr") |
| is_starter | boolean | True for curated podcasts |
| created_at | timestamptz | Default now() |

- Unique constraint on (user_id, rss_url)
- RLS policy: `USING (user_id = auth.uid())` on SELECT/INSERT/UPDATE/DELETE
- Starter podcasts are seeded per user when they first visit the podcast tab (or on onboarding)

### `podcast_episodes` table

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK, default gen_random_uuid() |
| podcast_id | uuid | FK to podcasts |
| guid | text | Episode GUID from RSS (for dedup) |
| title | text | Episode title |
| description | text | Episode description |
| audio_url | text | Direct link to audio file |
| duration | integer | Duration in seconds |
| published_at | timestamptz | Episode publish date |
| transcript | jsonb | Array of {start, end, text} segments, null until transcribed |
| is_transcribed | boolean | Default false |
| created_at | timestamptz | Default now() |

- Unique constraint on (podcast_id, guid)
- RLS policy: `USING (EXISTS (SELECT 1 FROM podcasts WHERE podcasts.id = podcast_episodes.podcast_id AND podcasts.user_id = auth.uid()))` on SELECT/INSERT/UPDATE/DELETE
- Only episodes the user has transcribed get rows in this table. Non-transcribed episodes are fetched live from the RSS feed.

### Transcript JSONB format

```json
[
  {"start": 0.0, "end": 4.8, "text": "Bonjour et bienvenue dans notre émission."},
  {"start": 4.8, "end": 9.2, "text": "Aujourd'hui nous allons parler de la situation au Moyen-Orient."}
]
```

Segment-level timestamps (not word-level) — each segment is typically a sentence or phrase, 3-10 seconds long. This provides calm, line-by-line highlighting during playback.

## Backend

### New files

- **`api/services/podcast_service.py`** — RSS parsing, Whisper transcription, starter podcast config
- **`api/routes/podcast.py`** — REST endpoints

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /podcasts | List user's podcasts (saved + starters for their language) |
| POST | /podcasts | Add podcast from RSS URL. Parses feed, saves metadata. |
| DELETE | /podcasts/{id} | Remove a saved podcast (cascade-deletes its episodes) |
| GET | /podcasts/{id}/episodes | Fetch episodes from RSS feed (live parse). For transcribed episodes, include transcript from DB. Limit to 50 most recent episodes. |
| POST | /podcasts/{id}/episodes/transcribe | Transcribe an episode. Request body contains episode metadata. Returns the transcript. |
| GET | /podcasts/{id}/episodes/{episode_id} | Get a single transcribed episode with transcript (by DB id, for study mode) |

### Request/Response Schemas

**POST /podcasts** — Add podcast
- Request: `{ "rss_url": "https://...", "language": "fr" }`
- Response: `{ "id": "uuid", "title": "...", "description": "...", "image_url": "...", "rss_url": "...", "language": "fr" }`

**GET /podcasts** — List podcasts
- Response: `[{ "id": "uuid", "title": "...", "image_url": "...", "language": "fr", "is_starter": true }]`

**GET /podcasts/{id}/episodes** — List episodes
- Response: `[{ "guid": "...", "title": "...", "description": "...", "audio_url": "...", "duration": 1680, "published_at": "...", "is_transcribed": false, "episode_id": null }]`
- For transcribed episodes, `is_transcribed=true` and `episode_id` contains the DB id (for the study link).

**POST /podcasts/{id}/episodes/transcribe** — Transcribe episode
- Request: `{ "guid": "...", "title": "...", "audio_url": "...", "duration": 1680, "published_at": "..." }`
- Response: `{ "id": "uuid", "transcript": [{"start": 0.0, "end": 4.8, "text": "..."}] }`
- This is a synchronous endpoint. Transcription takes ~30-60 seconds for a 30-min episode. The frontend shows a loading spinner. FastAPI timeout should be set to at least 5 minutes for this endpoint.

**GET /podcasts/{id}/episodes/{episode_id}** — Get transcribed episode
- Response: `{ "id": "uuid", "title": "...", "audio_url": "...", "transcript": [...] }`

### RSS Parsing

Use `feedparser` library (standard Python RSS parser) to parse feeds. Extract:
- Podcast: title, description, image (from `<itunes:image>` or `<image>`), episodes
- Episodes: title, description, audio URL (from `<enclosure>`), duration, published date, GUID

### Whisper Transcription

Use OpenAI Whisper API (`audio/transcriptions` endpoint):
- Before downloading, send a HEAD request to the audio URL to check Content-Length. If > 25 MB, return an error immediately without downloading.
- Download audio from the episode's URL to a temp file
- Send to Whisper with `response_format="verbose_json"` and `timestamp_granularities=["segment"]`
- Extract segments array from response
- Store in podcast_episodes.transcript as JSONB
- Clean up temp file
- Cost: ~$0.006/minute, ~$0.18 for a 30-min episode
- Uses the user's existing OpenAI API key (from user_settings)

New dependency: `feedparser` (add to pyproject.toml)

### Starter Podcast Config

A dict in `podcast_service.py` mapping language codes to starter podcast lists:

```python
STARTER_PODCASTS = {
    "fr": [
        {"title": "Tout un monde", "rss_url": "...", "image_url": "...", "description": "RTS — Actualité internationale"},
        # 2 more
    ],
    "es": [...],
    "it": [...],
    "ru": [...],
    "zh": [...],
}
```

Seeded into the podcasts table (with `is_starter=True`) on the backend: the `GET /podcasts` endpoint checks if the user has any podcasts for their language. If not, it inserts the starters automatically before returning the list.

## Frontend

### Navigation

Add "Podcast" to `navItems` in `Layout.jsx`, right after "Story":
```js
{ path: '/podcast', label: 'Podcast' }
```

Also add to mobile bottom nav with a headphone/podcast icon.

### New page: `web/src/pages/Podcast.jsx`

Single page component with three internal views managed by local state (not routes):

#### View 1: Podcast List
- Input bar at top: placeholder "Add your favourite podcast (RSS link)", on Enter/submit → POST /podcasts
- Grid of square cover-image tiles (3 columns on desktop, 2 on mobile)
- Cover images only — no titles
- Clicking a tile → transitions to episode list view

#### View 2: Episode List
- Back button → podcast list
- Podcast header: cover image + title + description
- List of episodes (fetched from GET /podcasts/{id}/episodes)
- Each episode shows: title, date, duration
- Two buttons per episode:
  - "Play" — plays audio directly (preview mode, no transcript)
  - "Save & Transcribe" — calls POST transcribe endpoint, shows loading state
- Transcribed episodes show "Study" button instead, with a "Transcribed" badge

#### View 3: Player & Transcript (Study Mode)
- Back button → episode list
- Audio player bar: play/pause, progress bar (seekable), current time / total time, speed controls (0.75x, 1x, 1.25x)
- Reuse playback rate logic from StoryGenerator (audioRef, playbackRate state, useEffect sync)
- Transcript displayed as flowing text (like story mode)
- Current segment highlighted with subtle style: faint purple background + left border
- Highlight updates via `timeupdate` event on audio element — find the segment where `currentTime` falls between `start` and `end`
- All words are clickable — on click, show the same word popover as story mode (translate via enhance_word, option to add to vocabulary)
- Auto-scroll to keep the current segment visible

### Shared components with Story mode

Extract a `useWordPopover` hook from StoryGenerator's word-click/popover logic (click handler, popover state, positioning, enhance API call, add-to-vocabulary flow, close-on-outside-click). Both StoryGenerator and Podcast use this hook.

Playback rate controls and audio element management can also be reused — extract if the duplication is more than a few lines, otherwise just replicate the pattern.

## Error Handling

- **Invalid RSS URL**: show inline error below input bar
- **RSS parse failure**: show error message, don't save podcast
- **Transcription failure**: show error on the episode, allow retry
- **Audio playback failure**: browser handles natively (show error if audio URL is broken)
- **Whisper API timeout**: for very long episodes (60+ min), consider a loading indicator with estimated time. The Whisper API has a 25 MB file size limit — if an episode exceeds this, show an error explaining the episode is too long.

## Scope Boundaries

**In scope:**
- Podcast browsing via RSS feeds
- Audio playback (streamed from original URL)
- Transcription via Whisper with segment timestamps
- Synchronized transcript display with segment highlighting
- Word click → translate → add to vocabulary (reuse story mode patterns)
- Starter podcasts per language
- Playback speed control

**Out of scope (future):**
- Downloading/caching audio files
- Offline playback
- Podcast search/discovery (beyond RSS)
- Episode progress tracking / bookmarks
- Sharing podcasts between users
- Automatic transcription of all episodes
