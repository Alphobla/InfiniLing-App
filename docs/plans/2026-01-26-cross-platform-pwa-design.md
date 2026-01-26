# Cross-Platform PWA Design - InfiniLing

## Overview

Migrate InfiniLing from desktop Tkinter app to a cross-platform web app (PWA) that works on phone and computer. Online-only for MVP.

**Tech Stack (All Free Tier):**

| Layer | Technology | Hosting |
|-------|------------|---------|
| Frontend | React + Vite | Vercel (free) |
| Backend | FastAPI | Vercel Serverless (free) |
| Database | PostgreSQL | Supabase (500MB free) |
| Auth | Email/password | Supabase Auth (free) |
| Audio | Browser cache only | No server storage |

**Architecture:**
```
React PWA (Vite)  →  FastAPI (Vercel)  →  Supabase PostgreSQL
     ↓                    ↓
Browser Cache        OpenAI API
(TTS audio)         (GPT + TTS)
```

**What's IN the MVP:**
- Vocabulary management (add, edit, delete, search)
- Word enhancement (GPT lemmatization + translation + frequency)
- Spaced repetition review system
- Story generation with vocabulary words
- TTS audio playback for stories (cached in browser)
- Import from desktop app (CSV/JSON)
- User accounts with token limits
- Starter words per language

**What's OUT of MVP:**
- Transcription mode (add later)
- Server-side audio storage
- Offline mode

---

## Database Schema

**User table** - handled by Supabase `auth.users` (email, password, created_at)

**Vocabulary**
```sql
CREATE TABLE vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    word TEXT NOT NULL,              -- original word entered
    lemma TEXT,                      -- base form from GPT
    translation TEXT,
    language_from TEXT NOT NULL,
    language_to TEXT NOT NULL,
    frequency_rank INTEGER,          -- from wordfreq
    example_sentence TEXT,
    next_review_date DATE,
    review_interval_days INTEGER DEFAULT 1,
    easiness_factor FLOAT DEFAULT 2.5,  -- SM-2 algorithm
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, lemma, language_from, language_to)
);
```

**VocabularyOccurrence** (review history)
```sql
CREATE TABLE vocabulary_occurrence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vocabulary_id UUID REFERENCES vocabulary(id) ON DELETE CASCADE,
    review_date DATE NOT NULL,
    score INTEGER CHECK (score >= 0 AND score <= 5)  -- SM-2 style
);
```

**UserSettings**
```sql
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    openai_api_key_encrypted TEXT,   -- nullable, user's own key
    tokens_used_this_month INTEGER DEFAULT 0,
    token_limit INTEGER DEFAULT 100000,
    mother_tongue TEXT NOT NULL,
    last_language_pair TEXT,         -- for convenience
    reset_date DATE DEFAULT date_trunc('month', NOW()) + INTERVAL '1 month',
    has_seen_intro BOOLEAN DEFAULT FALSE
);
```

**Capacity estimate:**
- 400 words ≈ 170KB
- Target: 50-100 users
- Estimated: ~50-200MB total (well within 500MB free tier)

---

## API Endpoints

### Authentication (Supabase handles)
```
POST /auth/signup     → Create account
POST /auth/login      → Get JWT token
POST /auth/logout     → Invalidate session
```

### Vocabulary
```
GET    /api/vocabulary           → List words (paginated, filterable)
POST   /api/vocabulary           → Add word (basic)
POST   /api/vocabulary/enhance   → Lemmatize + translate + frequency (GPT)
GET    /api/vocabulary/{id}      → Get word details
PUT    /api/vocabulary/{id}      → Update word
DELETE /api/vocabulary/{id}      → Delete word
```

### Spaced Repetition
```
GET  /api/review/due             → Words due for review today
GET  /api/review/session         → Get review session (mix of due + new)
POST /api/review/{id}/result     → Record result (score 0-5)
GET  /api/review/stats           → Progress statistics
```

### Generation
```
POST /api/generate/story         → Generate story with vocabulary words
POST /api/generate/audio         → Generate TTS for story text (streaming)
```

### User & Settings
```
GET  /api/user/settings          → Get settings
PUT  /api/user/settings          → Update settings (mother tongue, etc.)
GET  /api/user/usage             → Token usage this month
PUT  /api/user/api-key           → Set own OpenAI key
DELETE /api/user/api-key         → Remove key
```

### Import/Export
```
GET  /api/export                 → Download vocabulary as CSV or JSON
POST /api/import                 → Upload vocabulary file
```

### Starter Words
```
GET  /api/starter-words/{language}  → Get starter word list for language
```

---

## Frontend Structure

**Project Setup:**
```bash
npm create vite@latest infiniling-web -- --template react
```

**Folder Structure:**
```
src/
├── components/
│   ├── ui/                    # Reusable: Button, Card, Input, Modal
│   ├── VocabularyCard.jsx     # Single word display
│   ├── FlashCard.jsx          # Review card with flip animation
│   ├── AudioButton.jsx        # Play TTS button (for stories)
│   ├── ProgressBar.jsx        # Review progress
│   └── StarterWordPicker.jsx  # Word selection during onboarding
│
├── pages/
│   ├── Login.jsx              # Email/password form
│   ├── Signup.jsx             # Registration + mother tongue
│   ├── Onboarding.jsx         # Language selection + starter words
│   ├── Dashboard.jsx          # Stats, streak, due words
│   ├── VocabularyList.jsx     # All words, search, add
│   ├── Review.jsx             # Flashcard session
│   ├── StoryGenerator.jsx     # Generate + read stories
│   └── Settings.jsx           # Languages, API key, intro text
│
├── hooks/
│   ├── useAuth.js             # Login state, token refresh
│   ├── useVocabulary.js       # CRUD operations
│   ├── useReview.js           # Session management
│   └── useAudio.js            # TTS playback + browser caching
│
├── stores/                    # Zustand for state
│   ├── authStore.js
│   └── vocabularyStore.js
│
└── services/
    └── api.js                 # Axios + auth interceptor
```

**Routes:**
- `/login`, `/signup` — Auth pages
- `/onboarding` — Language + starter words (first login or new language)
- `/` — Dashboard (protected)
- `/vocabulary` — Word list
- `/review` — Flashcard session
- `/story` — Story generation
- `/settings` — User preferences

---

## Token & API Key Strategy

**Default: Shared Backend Key**
- New users get 100,000 tokens/month free from your OpenAI key
- Covers approximately:
  - ~400 word enhancements (lemma + translate)
  - ~100 TTS generations
  - ~40 story generations

**Token Tracking:**
- Every API call that uses OpenAI logs token count to `UserSettings.tokens_used_this_month`
- `reset_date` = 1st of each month, auto-resets counter

**When Limit Reached (Hard Block):**
```
┌─────────────────────────────────────────┐
│  You've used your free tokens this      │
│  month.                                 │
│                                         │
│  To continue using InfiniLing, add      │
│  your own OpenAI API key in Settings.   │
│                                         │
│  [Go to Settings]                       │
└─────────────────────────────────────────┘
```

**User's Own Key:**
- Added in Settings page
- Stored encrypted in Supabase
- Bypasses all limits
- Required for continued use after free tier exhausted

**Backend Logic:**
```python
def get_openai_key(user: User) -> str:
    if user.openai_api_key_encrypted:
        return decrypt(user.openai_api_key_encrypted)
    if user.tokens_used_this_month >= user.token_limit:
        raise HTTPException(403, "Token limit reached")
    return os.environ["OPENAI_API_KEY"]
```

---

## Audio Strategy (Browser Cache Only)

TTS audio is used for generated stories only (not individual words).

**How it works:**
1. User generates a story and clicks play
2. Frontend checks browser cache (Cache API)
3. If cached → play immediately
4. If not cached → call `/api/generate/audio` → stream audio → cache it → play

**Frontend Implementation:**
```javascript
// useAudio.js hook
const playStoryAudio = async (text, language) => {
  const cacheKey = `tts-${hashText(text)}`;
  const cache = await caches.open('infiniling-audio');

  let response = await cache.match(cacheKey);
  if (!response) {
    response = await api.post('/api/generate/audio', { text, language });
    await cache.put(cacheKey, response.clone());
  }

  const audioUrl = URL.createObjectURL(await response.blob());
  audioRef.current.src = audioUrl;
  audioRef.current.play();
};
```

**Benefits:**
- Zero server storage costs
- Audio persists across sessions (until browser clears cache)
- Simple implementation

---

## User Onboarding Flow

### Signup Page
1. Email + password
2. Mother tongue (required dropdown)
3. Submit → account created → redirect to onboarding

### Onboarding Step 1: Language Selection
```
┌─────────────────────────────────────────┐
│  Which language do you want to learn?   │
│                                         │
│  [Dropdown: Spanish, French, German...] │
│                                         │
│  (You can add more languages later)     │
│                                         │
│  [Continue]                             │
└─────────────────────────────────────────┘
```

### Onboarding Step 2: Starter Words
```
┌─────────────────────────────────────────┐
│  Pick words you'd like to learn         │
│  (sorted easiest → hardest)             │
│                                         │
│  ☑ hello (hola)                         │
│  ☑ thank you (gracias)                  │
│  ☑ water (agua)                         │
│  ☐ house (casa)                         │
│  ☐ to eat (comer)                       │
│  ☐ beautiful (hermoso)                  │
│  ...                                    │
│                                         │
│  Selected: 3 words    [Add & Continue]  │
└─────────────────────────────────────────┘
```

### Onboarding Step 3: Intro Text
```
┌─────────────────────────────────────────┐
│  Welcome to InfiniLing!                 │
│                                         │
│  InfiniLing helps you learn vocabulary  │
│  through spaced repetition and AI-      │
│  generated stories.                     │
│                                         │
│  • Add words you want to learn          │
│  • Review them with smart flashcards    │
│  • Read stories featuring your words    │
│                                         │
│  [Get Started]                          │
└─────────────────────────────────────────┘
```

### Adding New Language Later
Settings → "Add Language" → Same flow (language selection + starter words)

### Starter Word Lists
- Pre-defined per language (stored in backend JSON or database)
- Sorted by frequency rank (most common first)
- ~50-100 words per language

---

## Backend Structure

**Folder Structure:**
```
api/
├── main.py                 # FastAPI entry point
├── config.py               # Environment variables
├── auth.py                 # Supabase auth middleware
├── dependencies.py         # DB session, current user helpers
│
├── routes/
│   ├── vocabulary.py       # CRUD + enhance endpoints
│   ├── review.py           # Spaced repetition endpoints
│   ├── generate.py         # Story + TTS generation
│   ├── user.py             # Settings, API key, usage
│   └── import_export.py    # CSV/JSON import/export
│
├── services/
│   ├── openai_service.py   # GPT + TTS calls
│   ├── token_tracker.py    # Usage tracking middleware
│   └── starter_words.py    # Pre-defined word lists per language
│
└── shared/                 # Reuse from existing codebase
    ├── database_models.py  # SQLAlchemy models (add user_id)
    ├── spaced_repetition_selector.py
    └── frequency_analysis.py
```

**Code Reuse from Desktop App:**

| Keep & Adapt | Replace |
|--------------|---------|
| SQLAlchemy models (add `user_id`) | Tkinter UI → React |
| Spaced repetition logic | Local SQLite → Supabase |
| GPT translation/lemmatization | VLC audio → Web Audio API |
| Frequency analysis (wordfreq) | Single-user → multi-user |

**Estimated new code:**
- Backend: ~1,000-1,200 lines Python
- Frontend: ~1,500 lines React/JS

---

## Implementation Phases

### Phase 1: Backend API
1. Set up Supabase project (database + auth)
2. Create FastAPI structure with auth middleware
3. Implement vocabulary CRUD endpoints
4. Implement review endpoints (reuse SRS logic)
5. Add word enhancement endpoint (GPT lemma + translate)
6. Add story generation endpoint
7. Add TTS generation endpoint (streaming)
8. Implement token tracking
9. Add import/export endpoints (CSV + JSON)
10. Create starter word lists per language
11. Deploy to Vercel, test with Postman

### Phase 2: React Frontend
1. Project setup (Vite + React Router + Zustand + Axios)
2. Auth pages (login, signup with mother tongue)
3. Onboarding flow (language selection + starter words + intro)
4. Dashboard page (stats, due words count)
5. Vocabulary list page (search, filter, add, edit, delete)
6. Word enhancement UI (show lemma, translation, frequency)
7. Review session page (flashcards + scoring)
8. Story generation page (with audio playback)
9. Settings page (languages, API key, show intro again)
10. Import/export UI

### Phase 3: Polish & Launch
1. Mobile responsive design
2. PWA manifest + icons
3. Error handling & loading states
4. Beta testing with a few users
5. Bug fixes
6. Deploy to production

---

## Deployment

**Vercel Setup:**

| Service | What | Cost |
|---------|------|------|
| Vercel | Frontend (React) + Backend (Serverless) | Free |
| Supabase | PostgreSQL + Auth | Free (500MB) |

**Environment Variables:**
```bash
# Backend (Vercel)
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
OPENAI_API_KEY=...

# Frontend (Vercel)
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_API_URL=...
```

**PWA Configuration:**
```javascript
// vite.config.js
import { VitePWA } from 'vite-plugin-pwa'

export default {
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'InfiniLing',
        short_name: 'InfiniLing',
        theme_color: '#4F46E5',
        start_url: '/',
        display: 'standalone'
      },
      workbox: {
        runtimeCaching: [
          { urlPattern: /^https:\/\/api\./, handler: 'NetworkFirst' },
          { urlPattern: /\.mp3$/, handler: 'CacheFirst' }
        ]
      }
    })
  ]
}
```

---

## Success Criteria

- 100% free tier hosting (up to ~100 users)
- Works on phone and desktop
- Installable as app (PWA)
- Smooth review session flow
- Import from desktop app works
- Starter words available for major languages

---

## Migration from Desktop App

**Import flow:**
1. Export vocabulary from Tkinter app (CSV or JSON)
2. Upload file in web app Settings → Import
3. Conflict resolution if duplicates exist:
   - Skip duplicates (default)
   - Merge (update existing)
   - Replace all
4. Review history preserved where possible
