# Podcast Search via iTunes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bare RSS-URL input on the Podcasts page with a search-as-you-type box that uses the iTunes Search API, so users can add a podcast by name without ever seeing a URL.

**Architecture:** Backend exposes `GET /api/podcasts/search?q=&language=` — a thin auth-gated wrapper around a new `search_itunes_podcasts()` helper that calls Apple's free iTunes Search API. Frontend gains a debounced search input on `Podcast.jsx` whose dropdown results call the existing `POST /api/podcasts` (add by RSS URL) when clicked. Language biasing comes from `LANGUAGE_TO_ITUNES_COUNTRY` in `api/services/languages.py` (the central language registry).

**Tech Stack:** FastAPI · `requests` · pytest with `unittest.mock` · React 19 · Vite · Cypress.

**Commit style:** Author = Valentin (default git config). Do NOT pass `--author=`, do NOT add `Co-Authored-By` trailers, do NOT mention Claude/AI anywhere in commit messages. Match the existing short, lowercase commit-message style (e.g. "update podcasts. dont show play button").

**Reference:** Spec at `docs/superpowers/specs/2026-04-22-podcast-search-design.md`.

---

## File Structure

| File | Role | Status |
|---|---|---|
| `api/services/languages.py` | Central language registry — already extended with `LANGUAGE_TO_ITUNES_COUNTRY` map (uncommitted) | Modified |
| `api/services/podcast_service.py` | New helper `search_itunes_podcasts(term, language, limit)` | Modified |
| `api/routes/podcast.py` | New route `GET /api/podcasts/search` | Modified |
| `web/src/services/api.js` | New API client method `podcastApi.search(q, language)` | Modified |
| `web/src/pages/Podcast.jsx` | Replace RSS input with search input + dropdown + optimistic add flow | Modified |
| `tests/test_podcast_service.py` | New tests for `search_itunes_podcasts` | Modified |
| `web/cypress/e2e/podcast.cy.js` | New e2e for search-and-add happy path | Created |

**Note on test scope:** The existing test suite is service-level only (no FastAPI TestClient setup). To match patterns, this plan adds unit tests for the helper and a Cypress e2e for the full route+UI path, but does NOT introduce route-level pytest tests. If the project ever adopts TestClient, route tests can be added then.

**Working-tree caveat:** The repo currently has unrelated uncommitted changes (font swap on `index.css`/`index.html`, `italic` removal on Onboarding/Settings/Help, dev "Reset Onboarding" button on `SettingsModal.jsx`/`user.py`/`api.js`, npm install on `package-lock.json`). These are NOT part of this plan — leave them in the working tree. Commit only the files this plan touches.

---

## Task 1: Commit the existing `LANGUAGE_TO_ITUNES_COUNTRY` addition

The map was added to `api/services/languages.py` during brainstorming. It needs its own commit before the helper that consumes it.

**Files:**
- Modify: `api/services/languages.py` (already modified, uncommitted)

- [ ] **Step 1: Verify the map is present in the working tree**

Run:
```bash
git -C /home/magnebotix/repos/InfiniLing-App diff api/services/languages.py | head -30
```

Expected: A diff hunk showing `LANGUAGE_TO_ITUNES_COUNTRY = {...}` with codes `en/de/fr/es/it/ru/ar/zh/tr/pl` mapped to country codes.

- [ ] **Step 2: Stage and commit just this file**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add api/services/languages.py
git -C /home/magnebotix/repos/InfiniLing-App commit -m "add language → iTunes country map"
```

- [ ] **Step 3: Verify author is Valentin and no Claude attribution**

Run:
```bash
git -C /home/magnebotix/repos/InfiniLing-App log -1 --pretty=fuller
```

Expected: `Author: Valentin <valentinmaissen@gmail.com>`. No "Claude", no "Co-Authored-By", no "Generated with" lines.

---

## Task 2: Backend helper — `search_itunes_podcasts`

Add a service-layer function that calls the iTunes Search API. TDD: write the test first.

**Files:**
- Modify: `tests/test_podcast_service.py`
- Modify: `api/services/podcast_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_podcast_service.py`:

```python
from unittest.mock import patch, MagicMock
import requests
from api.services.podcast_service import search_itunes_podcasts


def _make_itunes_response(results):
    """Build a fake requests.Response.json() payload from iTunes."""
    mock = MagicMock()
    mock.json.return_value = {"resultCount": len(results), "results": results}
    mock.raise_for_status.return_value = None
    return mock


def test_search_itunes_podcasts_passes_country_for_known_language():
    """Polish search must include country=PL so results are biased to Polish shows."""
    response = _make_itunes_response([
        {
            "collectionName": "Easy Polish",
            "artistName": "Easy Languages",
            "feedUrl": "https://example.com/feed.xml",
            "artworkUrl600": "https://example.com/cover.jpg",
        }
    ])
    with patch("api.services.podcast_service.requests.get", return_value=response) as mock_get:
        results = search_itunes_podcasts("easy polish", language="pl")

    assert len(results) == 1
    assert results[0] == {
        "title": "Easy Polish",
        "artist": "Easy Languages",
        "image_url": "https://example.com/cover.jpg",
        "rss_url": "https://example.com/feed.xml",
    }
    # Verify country=PL was passed
    called_params = mock_get.call_args.kwargs["params"]
    assert called_params["country"] == "PL"
    assert called_params["term"] == "easy polish"
    assert called_params["media"] == "podcast"


def test_search_itunes_podcasts_omits_country_for_unknown_language():
    """If the language isn't in the country map, no country param is sent."""
    response = _make_itunes_response([])
    with patch("api.services.podcast_service.requests.get", return_value=response) as mock_get:
        search_itunes_podcasts("anything", language="xyz")

    called_params = mock_get.call_args.kwargs["params"]
    assert "country" not in called_params


def test_search_itunes_podcasts_skips_entries_without_feedurl():
    """Entries without a feedUrl can't be added to a user, so drop them."""
    response = _make_itunes_response([
        {"collectionName": "No Feed", "artistName": "X"},  # no feedUrl
        {
            "collectionName": "Has Feed",
            "artistName": "Y",
            "feedUrl": "https://example.com/feed.xml",
            "artworkUrl600": "https://example.com/cover.jpg",
        },
    ])
    with patch("api.services.podcast_service.requests.get", return_value=response):
        results = search_itunes_podcasts("test", language="en")

    assert len(results) == 1
    assert results[0]["title"] == "Has Feed"


def test_search_itunes_podcasts_falls_back_to_artworkurl100():
    """If artworkUrl600 is missing, use artworkUrl100 instead of empty string."""
    response = _make_itunes_response([
        {
            "collectionName": "Small Art",
            "artistName": "X",
            "feedUrl": "https://example.com/feed.xml",
            "artworkUrl100": "https://example.com/small.jpg",
        }
    ])
    with patch("api.services.podcast_service.requests.get", return_value=response):
        results = search_itunes_podcasts("test", language="en")

    assert results[0]["image_url"] == "https://example.com/small.jpg"


def test_search_itunes_podcasts_raises_on_network_error():
    """Network failures must propagate so the route can return 503,
    distinguishing 'iTunes broken' from 'iTunes returned empty'."""
    with patch("api.services.podcast_service.requests.get",
               side_effect=requests.RequestException("connection refused")):
        with pytest.raises(requests.RequestException):
            search_itunes_podcasts("test", language="en")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
uv run pytest tests/test_podcast_service.py -v -k search_itunes
```

Expected: 5 tests FAIL with `ImportError: cannot import name 'search_itunes_podcasts'`.

- [ ] **Step 3: Implement `search_itunes_podcasts`**

In `api/services/podcast_service.py`, add this function just before the existing `parse_rss_feed` function (around line 63). First add the import at the top of the file if not already present:

```python
from api.services.languages import LANGUAGE_TO_ITUNES_COUNTRY
```

Then add:

```python
def search_itunes_podcasts(term: str, language: str | None = None, limit: int = 10) -> list[dict]:
    """
    Search Apple's public iTunes Search API for podcasts by name.

    No auth required, no real rate limits — this is the same API most
    podcast apps use under the hood. Returns lightweight result cards
    `{title, artist, image_url, rss_url}` suitable for a search dropdown.
    The rss_url is what we feed into the existing add-podcast flow,
    so the user never sees a URL.

    Raises requests.RequestException on network/timeout error so the
    caller can distinguish "iTunes broken" (503) from "iTunes returned
    nothing" (200 with empty results).
    """
    params = {"term": term, "media": "podcast", "limit": str(limit)}
    country = LANGUAGE_TO_ITUNES_COUNTRY.get((language or "").lower())
    if country:
        params["country"] = country

    r = requests.get("https://itunes.apple.com/search", params=params, timeout=8)
    r.raise_for_status()

    results = []
    for item in r.json().get("results", []):
        feed_url = item.get("feedUrl")
        if not feed_url:
            continue  # No RSS feed = can't add, skip
        results.append({
            "title": item.get("collectionName", ""),
            "artist": item.get("artistName", ""),
            # 600x600 is sharper than the 100x100 default thumbnail
            "image_url": item.get("artworkUrl600") or item.get("artworkUrl100", ""),
            "rss_url": feed_url,
        })
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/test_podcast_service.py -v -k search_itunes
```

Expected: 5 tests PASS.

- [ ] **Step 5: Run the full podcast service test file (regression check)**

Run:
```bash
uv run pytest tests/test_podcast_service.py -v
```

Expected: All previous tests still pass.

- [ ] **Step 6: Commit**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add tests/test_podcast_service.py api/services/podcast_service.py
git -C /home/magnebotix/repos/InfiniLing-App commit -m "add itunes podcast search helper"
```

---

## Task 3: Backend route — `GET /api/podcasts/search`

Thin auth-gated wrapper around the helper. No pytest test (matches existing pattern of no route-level tests); covered by Cypress e2e in Task 7.

**Files:**
- Modify: `api/routes/podcast.py`

- [ ] **Step 1: Add the route**

In `api/routes/podcast.py`:

1. Update the import line at the top to include the new helper:

```python
from api.services.podcast_service import (
    STARTER_PODCASTS,
    parse_rss_feed,
    parse_episodes_from_feed,
    transcribe_audio,
    search_itunes_podcasts,  # ← add this
)
```

2. Also add `requests` to the imports (the route catches `RequestException`):

```python
import requests
```

3. Insert this new route between the existing `list_podcasts` (`@router.get("")`) and `add_podcast` (`@router.post("")`) handlers, around line 71:

```python
@router.get("/search")
def search_podcasts(
    q: str = Query(..., min_length=2),
    language: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
):
    """
    Search iTunes for podcasts by name. Returns lightweight result cards
    so the user can add a podcast by clicking instead of pasting an RSS URL.

    Returns 503 (not 200 with empty results) when iTunes is unreachable so
    the frontend can distinguish "no matches" from "search broken".
    """
    try:
        results = search_itunes_podcasts(q, language=language)
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Podcast search unavailable")
    return {"results": results}
```

- [ ] **Step 2: Manually verify the route works**

Start the backend in one terminal (if not already running):
```bash
uv run uvicorn api.main:app --reload --port 8000
```

In a second terminal, hit the route. You'll need a valid Bearer token from a logged-in session. Easiest: open the browser, log in, copy the token from `localStorage` (`sb-...-auth-token` → parse JSON → `access_token`).

Run:
```bash
TOKEN="<paste-your-access-token>"
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/podcasts/search?q=easy%20polish&language=pl" | head -50
```

Expected: JSON `{"results": [...]}` with at least one result whose `title` contains "Polish" and `rss_url` is a real URL. (Or `{"results": []}` if iTunes finds nothing.)

Also verify auth gating:
```bash
curl -s "http://localhost:8000/api/podcasts/search?q=test"
```

Expected: HTTP 401 / 403, not 200.

- [ ] **Step 3: Commit**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add api/routes/podcast.py
git -C /home/magnebotix/repos/InfiniLing-App commit -m "add /api/podcasts/search route"
```

---

## Task 4: Frontend API client — `podcastApi.search`

Tiny addition. No tests at this layer in the project (axios is trusted).

**Files:**
- Modify: `web/src/services/api.js`

- [ ] **Step 1: Add the search method**

In `web/src/services/api.js`, locate the `podcastApi` object (currently lines 81-88). Add a `search` method as the first entry (so it's discoverable):

```js
// Podcasts
export const podcastApi = {
  search: (q, language) => api.get('/api/podcasts/search', { params: { q, language } }),
  list: (language) => api.get('/api/podcasts', { params: { language } }),
  add: (data) => api.post('/api/podcasts', data),
  remove: (id) => api.delete(`/api/podcasts/${id}`),
  episodes: (podcastId) => api.get(`/api/podcasts/${podcastId}/episodes`),
  transcribe: (podcastId, data) => api.post(`/api/podcasts/${podcastId}/episodes/transcribe`, data),
  getEpisode: (podcastId, episodeId) => api.get(`/api/podcasts/${podcastId}/episodes/${episodeId}`),
}
```

- [ ] **Step 2: Verify no syntax errors**

Run:
```bash
cd /home/magnebotix/repos/InfiniLing-App/web && npm run lint -- src/services/api.js
```

Expected: No errors. (If lint isn't configured for a single file, run `npm run lint` and check api.js is clean.)

- [ ] **Step 3: Commit**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add web/src/services/api.js
git -C /home/magnebotix/repos/InfiniLing-App commit -m "add podcast search api client"
```

---

## Task 5: Frontend — Search state, debounced effect, race-safety

Lay the state foundation in `Podcast.jsx`. UI rendering comes in Task 6.

**Files:**
- Modify: `web/src/pages/Podcast.jsx`

- [ ] **Step 1: Replace search-related state**

In `web/src/pages/Podcast.jsx`, locate the existing podcast-list state (around line 25-28):

```js
const [rssUrl, setRssUrl] = useState('')
const [addError, setAddError] = useState('')
const [adding, setAdding] = useState(false)
const [deletingId, setDeletingId] = useState(null)
```

Replace with:

```js
// Search state — replaces the old RSS input
const [searchQuery, setSearchQuery] = useState('')
const [searchResults, setSearchResults] = useState([])  // [{title, artist, image_url, rss_url}, ...]
const [searchLoading, setSearchLoading] = useState(false)
const [searchError, setSearchError] = useState('')      // '' | 'unavailable' | 'add-failed'
const [showDropdown, setShowDropdown] = useState(false)
const [addError, setAddError] = useState('')
const [adding, setAdding] = useState(false)             // kept: blocks UI during add
const [deletingId, setDeletingId] = useState(null)
```

- [ ] **Step 2: Remove the old `handleAddPodcast` function**

Locate (around lines 60-77):

```js
// ── Add podcast from RSS ──
const handleAddPodcast = async () => {
  if (!rssUrl.trim()) return
  setAdding(true)
  setAddError('')
  try {
    const { data } = await podcastApi.add({
      rss_url: rssUrl.trim(),
      language,
    })
    setPodcasts(prev => [...prev, data])
    setRssUrl('')
  } catch (err) {
    setAddError(err.response?.data?.detail || 'Could not add podcast')
  } finally {
    setAdding(false)
  }
}
```

Delete it entirely. The new add flow lives inside `handleSelectResult` (Task 6).

- [ ] **Step 3: Add the debounced search effect with race-safety**

Add this `useEffect` immediately below the existing `useEffect` that fetches podcasts (around line 58, just after the `}, [language])` closing line). It also needs a ref for tracking the latest in-flight query — put the ref declaration with the other state:

```js
// Tracks the latest query that fired a request, so out-of-order responses
// (slow network, fast typing) can be discarded instead of overwriting fresh results.
const latestQueryRef = useRef('')
```

Then the effect:

```js
// ── Debounced search effect ──
// Why 250ms: long enough to skip mid-word noise, short enough that pausing feels instant.
// Why the ref check: a slow request fired for "easy" can land AFTER a faster request for
// "easy polish" — we drop the stale one to avoid flicker.
useEffect(() => {
  const q = searchQuery.trim()
  if (q.length < 2) {
    setSearchResults([])
    setSearchLoading(false)
    setSearchError('')
    setShowDropdown(false)
    return
  }

  setSearchLoading(true)
  setSearchError('')
  latestQueryRef.current = q

  const timer = setTimeout(async () => {
    try {
      const { data } = await podcastApi.search(q, language)
      // Drop stale response if the user has typed more since this request fired
      if (latestQueryRef.current !== q) return
      setSearchResults(data.results || [])
      setShowDropdown(true)
    } catch (err) {
      if (latestQueryRef.current !== q) return
      // 503 from backend = iTunes unavailable; anything else = treat the same
      setSearchError('unavailable')
      setSearchResults([])
      setShowDropdown(true)
    } finally {
      if (latestQueryRef.current === q) setSearchLoading(false)
    }
  }, 250)

  // Cleanup: cancel the pending timer if query changes again before it fires
  return () => clearTimeout(timer)
}, [searchQuery, language])
```

- [ ] **Step 4: Clear search when language changes**

Find the existing language `<select>` `onChange` handler (around line 192-197):

```js
onChange={(e) => {
  setLanguage(e.target.value)
  // Persist the selected language so it's remembered next time
  updateSettings({ last_language: e.target.value })
}}
```

Replace with:

```js
onChange={(e) => {
  setLanguage(e.target.value)
  updateSettings({ last_language: e.target.value })
  // Clear search — results from another language would be misleading
  setSearchQuery('')
  setSearchResults([])
  setShowDropdown(false)
}}
```

- [ ] **Step 5: Verify no JS errors yet (UI still broken — that's expected)**

Run the dev server if not running:
```bash
cd /home/magnebotix/repos/InfiniLing-App/web && npm run dev
```

Open the Podcasts page in the browser. The page will render but the old RSS input is gone and the new one isn't added yet. Check the browser console: no JS errors from missing imports / undefined references. (If `useRef` isn't imported, add it: `import { useState, useEffect, useRef } from 'react'` — already present at top of file.)

- [ ] **Step 6: Commit**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add web/src/pages/Podcast.jsx
git -C /home/magnebotix/repos/InfiniLing-App commit -m "wire up podcast search state + debounced effect"
```

---

## Task 6: Frontend — Search input, dropdown UI, click-to-add

Render the new search box and dropdown in place of the deleted RSS form, plus the optimistic add handler.

**Files:**
- Modify: `web/src/pages/Podcast.jsx`

- [ ] **Step 1: Add the `handleSelectResult` handler**

Place this above the existing `handleDelete` function (around line 79):

```js
// ── Click a search result → add it to the user's library ──
// Optimistic UX: prepend a placeholder card immediately so the click feels instant.
// On success, replace the placeholder with the real DB row. On failure, remove it.
const handleSelectResult = async (result) => {
  // De-dupe: if the user already has this podcast, do nothing
  if (podcasts.some(p => p.rss_url === result.rss_url)) {
    setShowDropdown(false)
    return
  }

  setShowDropdown(false)
  setSearchQuery('')

  // Temporary client-side id so React can key the placeholder card
  const placeholderId = `pending-${Date.now()}`
  const placeholder = {
    id: placeholderId,
    title: result.title,
    image_url: result.image_url,
    _pending: true,  // marker the grid uses to render a spinner overlay
  }
  setPodcasts(prev => [placeholder, ...prev])
  setAdding(true)
  setAddError('')

  try {
    const { data } = await podcastApi.add({
      rss_url: result.rss_url,
      language,
    })
    setPodcasts(prev => prev.map(p => p.id === placeholderId ? data : p))
  } catch (err) {
    setPodcasts(prev => prev.filter(p => p.id !== placeholderId))
    const detail = err.response?.data?.detail || ''
    if (err.response?.status === 409 || detail.toLowerCase().includes('duplicate')) {
      setAddError('Already in your library')
    } else {
      setAddError("Couldn't add this podcast — try another")
    }
  } finally {
    setAdding(false)
  }
}
```

- [ ] **Step 2: Add an Esc-to-close handler**

Below `handleSelectResult`:

```js
// Esc clears query and closes dropdown
useEffect(() => {
  const onKey = (e) => {
    if (e.key === 'Escape') {
      setSearchQuery('')
      setShowDropdown(false)
    }
  }
  window.addEventListener('keydown', onKey)
  return () => window.removeEventListener('keydown', onKey)
}, [])
```

- [ ] **Step 3: Replace the old RSS form with the new search input**

Find the old form in the View 1 render block (around lines 178-188):

```jsx
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
```

Replace with:

```jsx
{/* Search input + dropdown */}
<div className="relative mb-6">
  <div className="relative">
    {/* Magnifying glass icon */}
    <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none"
         fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round"
            d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
    <input
      type="text"
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
      onFocus={() => { if (searchResults.length > 0 || searchError) setShowDropdown(true) }}
      placeholder="Search for a podcast"
      className="w-full pl-10 pr-10 py-3 bg-surface border border-border rounded-lg text-text placeholder-muted focus:outline-none focus:border-accent"
      data-cy="podcast-search-input"
    />
    {/* Inline spinner while a request is in flight */}
    {searchLoading && (
      <div className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
    )}
  </div>

  {/* Dropdown */}
  {showDropdown && (
    <div className="absolute left-0 right-0 mt-1 bg-surface border border-border rounded-lg shadow-lg z-20 max-h-80 overflow-y-auto"
         data-cy="podcast-search-dropdown">
      {searchError === 'unavailable' ? (
        <div className="px-4 py-3 text-sm text-muted">Search unavailable — try again</div>
      ) : searchResults.length === 0 ? (
        <div className="px-4 py-3 text-sm text-muted">No results for "{searchQuery.trim()}"</div>
      ) : (
        searchResults.map((r) => {
          const alreadyAdded = podcasts.some(p => p.rss_url === r.rss_url)
          return (
            <button
              key={r.rss_url}
              onClick={() => handleSelectResult(r)}
              disabled={alreadyAdded}
              className={`w-full px-3 py-2 flex items-center gap-3 text-left hover:bg-bg transition-colors ${
                alreadyAdded ? 'opacity-50 cursor-default' : ''
              }`}
              data-cy="podcast-search-result"
            >
              {r.image_url ? (
                <img src={r.image_url} alt="" className="w-10 h-10 rounded object-cover flex-shrink-0" />
              ) : (
                <div className="w-10 h-10 rounded bg-bg flex items-center justify-center text-lg flex-shrink-0">🎙️</div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm text-text truncate">{r.title}</div>
                <div className="text-xs text-muted truncate">{r.artist}</div>
              </div>
              {alreadyAdded && (
                <span className="text-xs text-success font-medium flex-shrink-0">Added</span>
              )}
            </button>
          )
        })
      )}
    </div>
  )}
  {addError && <p className="text-red-400 text-sm mt-2">{addError}</p>}
</div>
```

- [ ] **Step 4: Render the placeholder spinner overlay in the grid**

Find the existing podcast-card render (around lines 213-233) and update the `<button>` to overlay a spinner when `pod._pending`:

```jsx
{podcasts.map((pod) => (
  <button
    key={pod.id}
    onClick={() => !pod._pending && openPodcast(pod)}
    disabled={pod._pending}
    className="aspect-square rounded-xl overflow-hidden bg-surface border border-border hover:border-accent transition-colors relative group"
  >
    {pod.image_url ? (
      <img src={pod.image_url} alt={pod.title} className="w-full h-full object-cover" />
    ) : (
      <div className="w-full h-full flex items-center justify-center text-4xl bg-surface">
        🎙️
      </div>
    )}
    {pod._pending && (
      <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
      </div>
    )}
    {!pod._pending && (
      <div
        onClick={(e) => handleDelete(e, pod.id)}
        className="absolute top-1 right-1 w-6 h-6 bg-black/60 rounded-full flex items-center justify-center text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity"
      >
        ✕
      </div>
    )}
  </button>
))}
```

- [ ] **Step 5: Manually test in browser**

With dev server running:

1. **Search basic flow:** Navigate to Podcasts. Type "easy polish" (with Polish selected). After ~250ms, dropdown appears with results. Verify each row has cover, title, artist.
2. **Click to add:** Click a result. Dropdown closes, placeholder card appears in grid with spinner, then the spinner is replaced by the real card.
3. **Already-added:** Search the same term again. The result shows "Added" badge and is unclickable.
4. **No results:** Type "asdfqwerty12345". Dropdown shows "No results for…".
5. **Min chars:** Type a single letter "a". No request fires (check Network tab), dropdown stays hidden.
6. **Esc:** With dropdown open, press Esc. Query clears, dropdown closes.
7. **Click outside:** With dropdown open, click on the language dropdown. The search dropdown closes (when language changes — verify this clears the search).
8. **Language switch:** With "easy polish" results showing, switch language to German. Dropdown closes, query clears.

If any of these fail, fix before committing.

- [ ] **Step 6: Commit**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add web/src/pages/Podcast.jsx
git -C /home/magnebotix/repos/InfiniLing-App commit -m "podcast search dropdown UI + optimistic add"
```

---

## Task 7: Cypress e2e — happy path search and add

One end-to-end spec that exercises the full route + UI. Mock `/api/podcasts/search` to keep the test deterministic and avoid hitting iTunes during CI.

**Files:**
- Create: `web/cypress/e2e/podcast.cy.js`

- [ ] **Step 1: Write the e2e spec**

Create `web/cypress/e2e/podcast.cy.js`:

```js
describe('Podcast search', () => {
  it('searches by name and adds a podcast via the dropdown', () => {
    const uniqueEmail = `podcast-search-${Date.now()}@test.com`

    // Mock the search endpoint so the test doesn't depend on iTunes
    cy.intercept('GET', '/api/podcasts/search*', {
      statusCode: 200,
      body: {
        results: [
          {
            title: 'Test Mock Podcast',
            artist: 'Mock Host',
            image_url: 'https://via.placeholder.com/100',
            rss_url: 'https://example.com/test-mock-feed.xml',
          },
        ],
      },
    }).as('searchPodcasts')

    // Mock the add endpoint so we don't actually fetch & parse a fake RSS feed
    cy.intercept('POST', '/api/podcasts', {
      statusCode: 200,
      body: {
        id: 'mock-id-123',
        title: 'Test Mock Podcast',
        description: 'Mock description',
        rss_url: 'https://example.com/test-mock-feed.xml',
        image_url: 'https://via.placeholder.com/100',
        language: 'pl',
        is_starter: false,
      },
    }).as('addPodcast')

    // Sign up a fresh user, complete onboarding briefly
    cy.visit('/signup')
    cy.get('input[type="email"]').type(uniqueEmail)
    cy.get('input[type="password"]').type('TestPassword123!')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/onboarding', { timeout: 15000 })
    cy.get('select').first().select('English')
    cy.get('select').last().select('Polish')
    cy.contains('button', 'Continue').click()
    cy.contains('Start Fresh', { timeout: 5000 }).click()
    cy.url().should('include', '/vocabulary', { timeout: 10000 })

    // Navigate to Podcasts
    cy.visit('/podcast')

    // Type into the search input — the debounce is 250ms
    cy.get('[data-cy="podcast-search-input"]').type('test mock')
    cy.wait('@searchPodcasts')

    // Dropdown shows the mocked result
    cy.get('[data-cy="podcast-search-dropdown"]').should('be.visible')
    cy.get('[data-cy="podcast-search-result"]').should('contain', 'Test Mock Podcast')
    cy.get('[data-cy="podcast-search-result"]').should('contain', 'Mock Host')

    // Click the result → triggers add
    cy.get('[data-cy="podcast-search-result"]').first().click()
    cy.wait('@addPodcast')

    // Dropdown closes; the new podcast appears in the grid
    cy.get('[data-cy="podcast-search-dropdown"]').should('not.exist')
    cy.contains('Test Mock Podcast').should('be.visible')

    // Search input is cleared
    cy.get('[data-cy="podcast-search-input"]').should('have.value', '')
  })
})
```

- [ ] **Step 2: Run the e2e test**

In one terminal, ensure backend is running:
```bash
uv run uvicorn api.main:app --reload --port 8000
```

In another, ensure frontend dev server is running:
```bash
cd /home/magnebotix/repos/InfiniLing-App/web && npm run dev
```

In a third, run the spec:
```bash
cd /home/magnebotix/repos/InfiniLing-App/web && npx cypress run --spec "cypress/e2e/podcast.cy.js"
```

Expected: 1 test passes. If signup fails because the project requires email confirmation in the test env, check `auth.cy.js` for the existing pattern (signup is already wired in `onboarding.cy.js`).

- [ ] **Step 3: Commit**

```bash
git -C /home/magnebotix/repos/InfiniLing-App add web/cypress/e2e/podcast.cy.js
git -C /home/magnebotix/repos/InfiniLing-App commit -m "e2e: podcast search and add"
```

---

## Task 8: Final smoke test

End-to-end manual verification with no mocks — proving the real iTunes API path works.

- [ ] **Step 1: With dev server and backend running, hit the real iTunes path**

In the browser, log in. Visit `/podcast`. Select Polish from the language dropdown. Type "easy polish" into the search box. Pause. Real iTunes results should appear within ~1 second.

- [ ] **Step 2: Add a real podcast**

Click "Easy Polish Podcast" (or any result). Verify:
- Dropdown closes immediately
- Placeholder card appears in grid with spinner
- Within ~2-3 seconds, the spinner is replaced by the real card with the podcast's actual cover art (which may differ slightly from the iTunes thumbnail since the backend re-parses the RSS feed for canonical metadata)
- Click the new card — episode list loads

- [ ] **Step 3: Confirm starter auto-seeding still works**

Sign out, sign in as a fresh user (or use the dev-only "Reset Onboarding" button if it's been merged). Visit `/podcast` → starter podcasts should still auto-seed for the chosen language.

- [ ] **Step 4: Confirm error path**

Stop the backend. In the browser, type a search query. Network request fails. Frontend should show "Search unavailable — try again" in the dropdown (or in browser console — depending on whether axios returns a 503 vs network error). Restart backend; verify recovery.

- [ ] **Step 5: No commit needed**

This is verification only.

---

## Self-Review Checklist (run after writing the plan)

- ✅ Spec coverage: every section of the spec maps to a task (helper → Task 2, route → Task 3, API client → Task 4, UI behavior + edge cases → Tasks 5-6, tests → Tasks 2 + 7).
- ✅ No placeholders / TBDs.
- ✅ Type/name consistency: `searchQuery`, `searchResults`, `searchLoading`, `searchError`, `showDropdown`, `latestQueryRef`, `handleSelectResult`, `_pending`, `placeholderId` — all referenced consistently across tasks 5-6.
- ✅ File paths verified (`tests/test_podcast_service.py` not `api/tests/`, `web/cypress/e2e/`, etc.).
- ✅ Test patterns match existing project (service-level pytest with MagicMock, Cypress e2e with intercept).
- ✅ Commit messages match the project's lowercase short style.
- ✅ No Claude attribution in any commit step.
