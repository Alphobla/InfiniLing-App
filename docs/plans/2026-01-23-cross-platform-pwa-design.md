# Cross-Platform PWA Design

## Overview

Migrate InfiniLing from a desktop-only Tkinter app to a cross-platform web app that works on both computer and phone with shared cloud data. **Online-only for MVP** (no offline support initially).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   FastAPI       │────▶│   Supabase      │────▶│   Supabase      │
│ (Reflex/NiceGUI)│◀────│   Backend       │◀────│   PostgreSQL    │     │   Storage       │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
     Phone/PC              Railway              Free hosted DB         Audio files (1GB free)
```

### Tech Stack (All Free Tier)

| Component | Technology | Hosting |
|-----------|------------|---------|
| Frontend | **Reflex or NiceGUI** (Python) | Railway or Vercel |
| Backend | Python FastAPI | Railway (free $5/month) |
| Database | PostgreSQL | Supabase (free 500MB) |
| File Storage | Audio/Transcripts | Supabase Storage (1GB free) |
| Auth | Email/password | Supabase Auth (free) |
| Code | Git | GitHub |

---

## 🔑 API Key Strategy

### Shared Backend Key (Default)
- New users get **free tokens** from your OpenAI key
- Track token usage per user in database
- **Monthly limit**: e.g., 50,000 tokens/user/month (≈ 200 translations + 50 TTS)

### User's Own Key (Optional/Required)
- Users can add their own OpenAI key in settings
- **Required** if they exceed monthly free limit
- Stored encrypted in Supabase

```
UserSettings (new table)
├── user_id (FK)
├── openai_api_key_encrypted (nullable)
├── tokens_used_this_month (int)
├── token_limit (default: 50000)
├── mother_tongue
├── last_language_from
└── reset_date (1st of each month)
```

---

## 📁 Audio & Transcript Storage Strategy

### Option A: Supabase Storage (Recommended for MVP)
Store audio files in Supabase Storage buckets (1GB free):

```
Bucket: audio/
├── {user_id}/
│   ├── tts/
│   │   ├── {word_id}.mp3          (TTS for vocabulary words)
│   │   └── {review_session_id}.mp3 (Generated review text audio)
│   └── transcriptions/
│       ├── {transcript_id}.srt
│       └── {transcript_id}.mp3     (Original uploaded audio)
```

**Pros**: Simple, free, integrated with Supabase auth
**Cons**: 1GB limit, egress costs after free tier

### Option B: Generate Audio On-Demand (No Storage)
- Don't store TTS audio at all
- Generate fresh each time user plays
- Cache in browser session only

**Pros**: Zero storage, always fresh
**Cons**: Higher API costs, slower playback, no offline

### Option C: Cloudflare R2 (If you outgrow Supabase)
- 10GB free storage, zero egress fees
- More complex setup

### 📌 Recommendation: Start with Option A
- Store TTS audio for vocabulary words (small, reusable)
- Don't store generated review session audio (regenerate each time)
- Store user-uploaded transcription files

### Database Tables for Storage

```
AudioFile (new table)
├── id
├── user_id (FK)
├── vocabulary_id (FK, nullable) - for word TTS
├── transcript_id (FK, nullable) - for transcriptions
├── storage_path (e.g., "audio/{user_id}/tts/{word_id}.mp3")
├── file_size_bytes
├── created_at

Transcript (new table)
├── id
├── user_id (FK)
├── title
├── language
├── audio_path (nullable - if user uploaded audio)
├── srt_content (TEXT - store SRT directly in DB, small)
├── created_at
```

### Capacity

- Current data: 400 words = 170KB
- Target: 50-100 users with similar databases
- Estimated total: ~50-200MB (well within free tier)

## Database Schema Changes

Add user ownership to support multiple users:

```
User (use Supabase auth.users)
├── id (UUID)
├── email
└── created_at

Vocabulary (add user_id)
├── id
├── user_id (FK) ← NEW
├── word
├── translation
├── language_from/to
├── ... (existing fields)
└── UNIQUE(user_id, word, translation, language_from, language_to)

VocabularyOccurrence (unchanged)
├── id
├── vocabulary_id (FK)
├── date
└── repeat_flag
```

## API Endpoints

### Authentication (Supabase handles)
```
POST /auth/signup     → Create account
POST /auth/login      → Get access token
POST /auth/logout     → Invalidate token
```

### Vocabulary CRUD
```
GET    /api/vocabulary           → List user's words (paginated, filterable)
POST   /api/vocabulary           → Add new word (basic)
GET    /api/vocabulary/{id}      → Get single word with details
PUT    /api/vocabulary/{id}      → Update word
DELETE /api/vocabulary/{id}      → Delete word
```

### Word Enhancement (GPT)
```
POST /api/vocabulary/enhance     → Lemmatize + translate + frequency (uses GPT)
POST /api/translate              → Simple translation only
GET  /api/frequency/{word}       → Get word frequency (no GPT, uses wordfreq)
```

### Spaced Repetition
```
GET  /api/review/due             → Get words due for review
GET  /api/review/session         → Get review session (mix of new + due words)
POST /api/review/{id}/result     → Record review result (score 0-5)
GET  /api/review/stats           → User's progress statistics
```

### Text Generation (Gentexter mode)
```
POST /api/generate/text          → Generate story with vocabulary words
POST /api/generate/audio         → Generate TTS audio for text
```

### Audio & TTS
```
GET  /api/audio/word/{id}        → Get/generate TTS for a vocabulary word
GET  /api/audio/text             → Stream TTS for arbitrary text
POST /api/audio/upload           → Upload audio file (for transcription)
```

### Transcripts
```
GET    /api/transcripts          → List user's transcripts
POST   /api/transcripts          → Create new transcript (upload SRT + optional audio)
GET    /api/transcripts/{id}     → Get transcript with content
DELETE /api/transcripts/{id}     → Delete transcript
```

### User Settings & Token Usage
```
GET  /api/user/settings          → Get user settings (mother tongue, etc.)
PUT  /api/user/settings          → Update settings
GET  /api/user/usage             → Get token usage this month
PUT  /api/user/api-key           → Set user's own OpenAI key
```

### Import/Export
```
GET  /api/export                 → Download vocabulary as CSV/JSON
POST /api/import                 → Upload vocabulary file
```

## Backend Structure

```
src/
├── api/
│   ├── main.py           (FastAPI app entry point)
│   ├── auth.py           (auth middleware)
│   ├── routes/
│   │   ├── vocabulary.py (CRUD endpoints)
│   │   ├── review.py     (spaced repetition endpoints)
│   │   └── translate.py  (GPT translation endpoint)
│   └── dependencies.py   (DB session, current user helpers)
├── shared/               (existing - reusable)
│   ├── database_models.py
│   └── spaced_repetition_selector.py
```

## Frontend Pages

```
/login          → Email/password form
/signup         → Registration form
/dashboard      → Word count, streak, stats
/vocabulary     → List all words, search, add new
/review         → Flashcard study session
/settings       → Language pair, account settings
```

### PWA Requirements
1. `manifest.json` - App name, icon, colors
2. Service Worker - Caches files for offline use
3. HTTPS - Provided by Vercel

## Implementation Order

### Phase 1: Backend API
1. Set up Supabase project, create tables with `user_id`
2. Create FastAPI project with auth middleware
3. Build vocabulary CRUD endpoints
4. Build review endpoints (reuse spaced repetition logic)
5. Add translation endpoint (reuse GPT code)
6. Deploy to Railway
7. Test with Postman/curl

### Phase 2: Reflex Web App
1. Create Reflex app with routing
2. Build login/signup pages (connect to Supabase Auth)
3. Build vocabulary list page
4. Build review/flashcard page
5. Build settings page (API key, mother tongue)
6. Deploy to Railway or Reflex Cloud

### Phase 3: Polish
1. Add import/export for existing users
2. Mobile-friendly responsive design
3. Audio player for vocabulary words
4. Transcription mode (optional)
5. Invite friends to test

## Code Reuse

| Keep (reuse) | Rebuild |
|--------------|---------|
| SQLAlchemy models | Tkinter UI → Reflex UI |
| Spaced repetition logic | Local DB → Cloud DB |
| Frequency analysis | Add user accounts |
| GPT translation calls | Add REST API layer |

### Estimated Scope
- Backend: ~800-1200 lines of new Python
- Frontend: ~1000-1500 lines of Reflex Python
- Existing logic reused: ~2000 lines

## Migration Notes

- Current Tkinter app continues to work during development
- Import/export feature allows migrating existing vocabulary
- Could add "sync to cloud" button in Tkinter as bridge

---

## 🎨 Frontend Framework: Reflex vs NiceGUI

### Reflex
**What it is**: Full-stack Python framework that compiles to React + FastAPI

| Aspect | Details |
|--------|---------|
| **Look & Feel** | ⭐⭐⭐⭐⭐ Modern, polished, uses Radix UI components |
| **Mobile** | ⭐⭐⭐⭐ Responsive by default, feels like real app |
| **Learning Curve** | Medium - React concepts in Python syntax |
| **Customization** | Excellent - CSS, Tailwind, custom components |
| **Deployment** | `reflex deploy` to their cloud, or Docker anywhere |
| **State Management** | Built-in reactive state, very clean |
| **Community** | Growing fast, good docs, active Discord |

**Example code:**
```python
import reflex as rx

class State(rx.State):
    words: list[dict] = []
    
    async def load_words(self):
        self.words = await api.get_vocabulary()

def vocabulary_page():
    return rx.vstack(
        rx.heading("My Vocabulary"),
        rx.foreach(State.words, word_card),
        on_mount=State.load_words,
    )
```

### NiceGUI
**What it is**: Python UI framework using Vue.js/Quasar under the hood

| Aspect | Details |
|--------|---------|
| **Look & Feel** | ⭐⭐⭐⭐ Clean Material Design, slightly more "tool-like" |
| **Mobile** | ⭐⭐⭐ Works but feels more like mobile website |
| **Learning Curve** | Easy - very intuitive, less boilerplate |
| **Customization** | Good - Tailwind, CSS, Quasar components |
| **Deployment** | Any Python host, Docker, simpler than Reflex |
| **State Management** | Simpler, more imperative style |
| **Community** | Smaller but helpful, good for quick prototypes |

### 📌 Recommendation: **Reflex**

For a learning app that should "look really nice":

1. **Better aesthetics** - Radix UI components look more polished
2. **PWA support** - Compiles to React, mature PWA tooling
3. **Mobile experience** - Feels more like a native app
4. **Audio/media** - Better component ecosystem
5. **Future-proof** - Larger community, active development

---

## ❓ Open Questions to Decide

### 1. Token Limit Strategy
- **Proposed: 50,000 tokens/month free** ≈
  - ~200 word enhancements (GPT lemma + translate)
  - ~50 TTS generations
  - ~20 story generations
- Is this enough? Too generous?

### 2. When limit exceeded?
- **Option A**: Hard block - "Add your API key to continue"
- **Option B**: Soft warning at 80% - "Consider adding your key"
- **Option C**: Graceful degradation - Disable TTS, keep translations

### 3. Transcription Mode?
- Keep it? (users upload audio → backend transcribes with Whisper)
- Drop for MVP? Focus on vocabulary + review first
- Make it own-key-only feature?

### 4. Audio Storage Duration
- Keep TTS files forever? (accumulates storage)
- Delete after 30 days? (re-generate on demand)
- Only cache in browser? (no server storage)

### 5. User Onboarding
- Require mother tongue on signup?
- Pre-populate with starter vocabulary?
- Tutorial walkthrough?

### 6. Vocabulary Migration
- One-time import from desktop app?
- If word already exists: merge? skip? ask?
