# Cross-Platform PWA Design

## Overview

Migrate InfiniLing from a desktop-only Tkinter app to a cross-platform PWA (Progressive Web App) that works on both computer and phone with shared cloud data.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PWA Client    │────▶│   FastAPI       │────▶│   Supabase      │
│   (React)       │◀────│   Backend       │◀────│   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     Phone/PC              Railway              Free hosted DB
```

### Tech Stack (All Free Tier)

| Component | Technology | Hosting |
|-----------|------------|---------|
| Frontend | React + PWA | Vercel (free) |
| Backend | Python FastAPI | Railway (free $5/month) |
| Database | PostgreSQL | Supabase (free 500MB) |
| Auth | Email/password | Supabase Auth (free) |
| Code | Git | GitHub |

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
GET    /api/vocabulary           → List user's words (paginated)
POST   /api/vocabulary           → Add new word
GET    /api/vocabulary/{id}      → Get single word
PUT    /api/vocabulary/{id}      → Update word
DELETE /api/vocabulary/{id}      → Delete word
```

### Spaced Repetition
```
GET  /api/review/due             → Get words due for review
POST /api/review/{id}/result     → Record review (correct/incorrect)
GET  /api/review/stats           → User's progress statistics
```

### Translation
```
POST /api/translate              → Translate word via GPT
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

### Phase 2: React PWA
1. Create React app with routing
2. Build login/signup pages (connect to Supabase Auth)
3. Build vocabulary list page
4. Build review/flashcard page
5. Add PWA manifest + service worker
6. Deploy to Vercel

### Phase 3: Polish
1. Add import/export for existing users
2. Mobile-friendly CSS
3. Offline caching (service worker)
4. Invite friends to test

## Code Reuse

| Keep (reuse) | Rebuild |
|--------------|---------|
| SQLAlchemy models | Tkinter UI → React |
| Spaced repetition logic | Local DB → Cloud DB |
| Frequency analysis | Add user accounts |
| GPT translation calls | Add REST API layer |

### Estimated Scope
- Backend: ~500-800 lines of new Python
- Frontend: ~1500-2500 lines of React
- Existing logic reused: ~2000 lines

## Migration Notes

- Current Tkinter app continues to work during development
- Could make Tkinter talk to new API as intermediate step
- Import/export feature allows migrating existing vocabulary
