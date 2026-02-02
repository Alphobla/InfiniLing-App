# PWA Frontend Implementation Plan

**Goal:** MVP React frontend for InfiniLing with Supabase auth.

**Tech:** React + Vite, React Router, Zustand, Axios, Tailwind CSS

---

## Progress

| Task | Status |
|------|--------|
| 1. Project Setup | ✅ Done |
| 2. Services (API, Supabase) | ✅ Done |
| 3. Auth (Store, Login, Signup) | ✅ Done |
| 4. Layout & Routes | ✅ Done |
| 5. Dashboard | ✅ Done |
| 6. Vocabulary List + Add/Edit | ✅ Done |
| 7. Review Session | ✅ Done |
| 8. Story Generator + Audio | ✅ Done |
| 9. Settings + Import/Export | ✅ Done |
| 10. Onboarding | ✅ Done |
| 11. PWA Config | ✅ Done |

---

## MVP Scope

- **Onboarding:** Mother tongue selection + intro text only (no starter words)
- **Words:** Auto-enhance on add (GPT lemmatize + translate)
- **Review:** Full SM-2 scale (0-5 buttons)
- **Story:** Generate + TTS audio playback
- **Settings:** Token usage, own API key, import/export CSV/JSON

---

## Task 1: Project Setup

```bash
npm create vite@latest web -- --template react
cd web
npm install react-router-dom zustand axios @supabase/supabase-js
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Files: `tailwind.config.js`, `src/index.css`, `.env.example`

---

## Task 2: Services

**`src/services/supabase.js`** - Supabase client

**`src/services/api.js`** - Axios with auth interceptor + endpoints:
- vocabulary: list, create, update, delete, enhance, due, statistics, review
- user: settings CRUD, usage, apiKey
- generate: story, audio
- import/export

---

## Task 3: Auth

**`src/stores/authStore.js`** - Zustand: user, session, settings, signIn/Up/Out

**`src/pages/Login.jsx`** - Email + password form

**`src/pages/Signup.jsx`** - Email + password (redirect to onboarding)

---

## Task 4: Layout & Routes

**`src/components/Layout.jsx`** - Protected wrapper + Navbar

**`src/App.jsx`** - Routes:
- `/login`, `/signup`, `/onboarding` (public)
- `/`, `/vocabulary`, `/review`, `/story`, `/settings` (protected)

---

## Task 5: Dashboard

**`src/pages/Dashboard.jsx`**
- Stats: total words, due, new, mastered
- Start review button
- Quick actions

---

## Task 6: Vocabulary

**`src/pages/VocabularyList.jsx`**
- Search, language filter
- Word cards with edit/delete
- Add modal with auto-enhance

---

## Task 7: Review

**`src/pages/Review.jsx`**
- FlashCard (flip animation)
- SM-2 buttons (0-5)
- Progress bar
- Session complete stats

---

## Task 8: Story

**`src/pages/StoryGenerator.jsx`**
- Word selection
- Word multiplier slider
- Generate button
- Story display
- Audio playback (Cache API)

---

## Task 9: Settings

**`src/pages/Settings.jsx`**
- Mother tongue / learning language
- Token usage + API key input
- Import (file upload) / Export (download)
- Sign out

---

## Task 10: Onboarding

**`src/pages/Onboarding.jsx`**
- Step 1: Mother tongue dropdown
- Step 2: Intro text
- Save settings → redirect to dashboard

---

## Task 11: PWA

- `vite-plugin-pwa`
- `manifest.json`
- Service worker for audio caching

**Note:** Add PWA icons to `public/` folder:
- `pwa-192x192.png`
- `pwa-512x512.png`
- `apple-touch-icon.png` (180x180)
- `favicon.ico`
