# Cross-Platform PWA Design - InfiniLing

## Architecture

```
React PWA (Vite) → FastAPI (Vercel) → Supabase (PostgreSQL + Storage + Auth)
```

**Tech Stack:**
- Frontend: React + Vite, Vercel hosting (free)
- Backend: FastAPI, Vercel Serverless (free)
- Database: Supabase PostgreSQL (500MB free)
- Storage: Supabase Storage (1GB free)
- Auth: Supabase Auth

---

## Database Schema

```sql
-- User table handled by Supabase auth.users

Vocabulary
├── id, user_id (FK), word, lemma, translation
├── language_from, language_to, frequency_rank
├── example_sentence, audio_file_id (FK)
├── next_review_date, review_interval_days, easiness_factor
└── UNIQUE(user_id, lemma, language_from, language_to)

VocabularyOccurrence
├── id, vocabulary_id (FK), review_date, score (0-5)

UserSettings
├── user_id (FK), openai_api_key_encrypted
├── tokens_used_this_month, token_limit (default: 50000)
├── mother_tongue, last_language_pair, reset_date

AudioFile
├── id, user_id (FK), vocabulary_id (FK, nullable)
├── transcript_id (FK, nullable), storage_path
├── file_size_bytes, last_accessed_at

Transcript
├── id, user_id (FK), title, language
├── audio_path, srt_content, vocabulary_extracted (jsonb)
```

---

## API Endpoints

### Authentication
- `POST /auth/signup` - Create account
- `POST /auth/login` - Get JWT
- `POST /auth/logout` - Invalidate session

### Vocabulary
- `GET /api/vocabulary` - List user's words (paginated, filterable)
- `POST /api/vocabulary` - Add word (basic)
- `POST /api/vocabulary/enhance` - Lemmatize + translate + frequency (GPT)
- `GET /api/vocabulary/{id}` - Get word details
- `PUT /api/vocabulary/{id}` - Update word
- `DELETE /api/vocabulary/{id}` - Delete word
- `POST /api/vocabulary/batch` - Bulk add

### Spaced Repetition
- `GET /api/review/due` - Words due today
- `GET /api/review/session` - Create review session
- `POST /api/review/{id}/result` - Record result (score 0-5)
- `GET /api/review/stats` - Progress statistics

### Generation
- `POST /api/generate/story` - Generate story with vocabulary
- `POST /api/generate/audio` - Generate TTS

### Audio
- `GET /api/audio/word/{id}` - Get/generate TTS for word
- `POST /api/audio/text` - Generate TTS for text
- `GET /api/audio/stream/{file_id}` - Stream audio file

### Transcription
- `GET /api/transcripts` - List transcripts
- `POST /api/transcripts` - Upload audio → Whisper transcription
- `POST /api/transcripts/srt` - Upload existing SRT
- `GET /api/transcripts/{id}` - Get transcript
- `DELETE /api/transcripts/{id}` - Delete transcript
- `POST /api/transcripts/{id}/extract` - Extract vocabulary from transcript

### User
- `GET /api/user/settings` - Get settings
- `PUT /api/user/settings` - Update settings
- `GET /api/user/usage` - Token usage this month
- `PUT /api/user/api-key` - Set OpenAI key
- `DELETE /api/user/api-key` - Remove key

### Import/Export
- `GET /api/export` - Download vocabulary CSV/JSON
- `POST /api/import` - Upload vocabulary (conflict resolution)

---

## Frontend Structure

```
src/
├── components/
│   ├── ui/ (Button, Card, Input, Modal)
│   ├── VocabularyCard.jsx
│   ├── FlashCard.jsx
│   ├── AudioPlayer.jsx
│   ├── ProgressBar.jsx
│   └── TranscriptViewer.jsx
├── pages/
│   ├── Login.jsx, Dashboard.jsx
│   ├── VocabularyList.jsx, Review.jsx
│   ├── Transcripts.jsx, Settings.jsx
├── hooks/
│   ├── useVocabulary.js, useAudioPlayer.js
│   ├── useSpacedRepetition.js, useAuth.js
│   └── useTranscript.js
├── services/
│   ├── api.js (Axios + auth interceptor)
│   ├── vocabularyService.js, reviewService.js
│   ├── audioService.js, transcriptService.js
├── stores/ (Zustand)
│   ├── authStore.js, vocabularyStore.js
└── utils/
    ├── srsAlgorithm.js, formatters.js
```

**Routes:**
- `/login`, `/signup` - Auth
- `/dashboard` - Stats, streak, upcoming reviews
- `/vocabulary` - List, search, add words
- `/review` - Flashcard session
- `/transcripts`, `/transcripts/:id` - Transcription feature
- `/settings` - Language pair, API key, account

---

## Backend Structure

```
api/
├── main.py (FastAPI entry point)
├── auth.py (Supabase auth middleware)
├── config.py (Environment variables)
├── routes/
│   ├── vocabulary.py, review.py
│   ├── generate.py, transcripts.py, user.py
├── services/
│   ├── openai_service.py (GPT + TTS + Whisper)
│   ├── token_tracker.py
│   └── storage_service.py (Supabase storage)
├── shared/ (Reuse from existing codebase)
│   ├── database_models.py
│   └── spaced_repetition_selector.py
```

---

## Token & Storage Strategy

**Token Limits:**
- Default: 50,000 tokens/month free (shared backend key)
- Enables: ~200 word enhancements + ~50 TTS + ~20 stories
- 80% usage: Warning notification
- 100% usage: Disable TTS/stories, keep basic translations
- User can add own key to bypass limits

**Transcription:**
- Requires user's own OpenAI API key (Whisper is expensive)
- Check for key before allowing transcription uploads

**Storage (Supabase 1GB free):**
```
audio/
├── {user_id}/
│   ├── tts/{word_id}.mp3 (store vocabulary word TTS)
│   └── transcriptions/{transcript_id}.mp3 + .srt (store uploads)
```

**Caching:**
1. Check browser cache (PWA offline)
2. Check Supabase storage
3. Generate fresh if missing
4. Delete files not accessed in 90 days if approaching limit

---

## PWA Configuration

**Install vite-plugin-pwa:**
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

## Code Reuse from Existing Codebase

**Keep (adapt for multi-user):**
- SQLAlchemy models (add `user_id`)
- Spaced repetition logic
- GPT translation/lemmatization
- Frequency analysis (wordfreq)

**Replace:**
- Tkinter UI → React components
- Local SQLite → Supabase PostgreSQL
- VLC audio → Web Audio API
- Single-user → Multi-user with auth

**Estimated scope:**
- Backend: ~1,200 lines new Python
- Frontend: ~1,500 lines React/JS
- Reused: ~2,000 lines existing logic

---

## Implementation Order

### Phase 1: Backend (3-4 days)
1. Set up Supabase (database + storage + auth)
2. Create FastAPI structure
3. Implement vocabulary CRUD (reuse DB models)
4. Implement review endpoints (reuse SRS logic)
5. Add translation/enhancement (reuse GPT code)
6. Add transcription endpoints (Whisper integration)
7. Implement token tracking middleware
8. Deploy to Vercel, test with Postman

### Phase 2: React Frontend (1-2 weeks)
**Days 1-2:** Setup
- `npm create vite@latest infiniling -- --template react`
- Install: `react-router-dom`, `@supabase/supabase-js`, `zustand`, `axios`
- Configure PWA plugin
- Build login/signup pages, auth hook
- Protected routes

**Days 3-5:** Vocabulary
- List page (search, filter, pagination)
- Add word modal with enhancement
- Vocabulary card component
- Edit/delete functionality
- Token usage indicator

**Days 6-8:** Review System
- Flashcard component
- SRS calculations (client-side)
- Review session flow
- Audio player component
- Progress tracking

**Days 9-11:** Transcription Feature
- Upload page (audio or SRT)
- Whisper transcription flow (check user API key)
- Transcript viewer with SRT display
- Extract vocabulary from transcript
- Bulk add to vocabulary

**Days 12-14:** Polish
- Dashboard with stats
- Settings page (language pair, API key)
- Onboarding flow (language selection)
- Mobile responsive design
- PWA manifest + icons

### Phase 3: Launch (3-5 days)
1. Import/export for existing users (CSV/JSON)
2. Conflict resolution (merge vs skip)
3. Beta testing with 5-10 users
4. Bug fixes
5. Deploy to production

---

## User Onboarding

1. **Sign up:** Email + password
2. **Language selection:** Mother tongue + learning language (required)
3. **Quick tour:** Optional walkthrough
4. **Dashboard:** Welcome, empty state, import option for existing users

---

## Migration from Desktop App

**Import flow:**
- Upload CSV/JSON export from Tkinter app
- Conflict resolution modal if duplicates exist
- Options: Merge, Skip duplicates, Replace all
- Preserve review history

---

## Deployment

**Vercel (Frontend + Backend):**
- Frontend: `npm run build` → deploy `dist/`
- Backend: Serverless functions in `api/` folder

**Environment Variables:**
```bash
# Backend
SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY

# Frontend
VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
```

---

## Success Criteria

- 100% free tier hosting (0-100 users)
- <2s page load time
- Works offline (vocabulary browsing)
- Installable as app on all devices
- Mobile-first responsive design
- Smooth review session flow

**Total development time:** 3-4 weeks for MVP
