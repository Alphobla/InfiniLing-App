# Podcast Search via iTunes — Design Spec

**Date:** 2026-04-22
**Status:** Approved (brainstorm); pending implementation plan

## Problem

Adding a podcast currently requires pasting an RSS URL into a bare text input on the Podcasts page. Most users don't know how to find an RSS URL for a show; this is a friction point that effectively gates the feature behind technical knowledge.

## Goal

Let users add their favourite podcast by typing its name. No URLs, no copy-pasting.

## Approach

Use Apple's public iTunes Search API (free, no auth, no real rate limits — the same API most podcast clients use under the hood) as the search backend. The user types a podcast name; we surface matching shows; they click one; we save the underlying RSS feed transparently.

## Decisions

| Question | Decision |
|---|---|
| Result placement | Dropdown directly under the search input |
| Language biasing | Always bias to the currently selected language (via iTunes `country` param) |
| Curated `STARTER_PODCASTS` | Keep auto-seeding on first visit to a language (unchanged) |
| Bare RSS URL input | Drop entirely — search is the only entry point |

## Architecture

### Backend

**New helper** in `api/services/podcast_service.py`:
```python
def search_itunes_podcasts(term: str, language: str | None = None, limit: int = 10) -> list[dict]
```
- Calls `https://itunes.apple.com/search` with `term`, `media=podcast`, and `country` resolved from `LANGUAGE_TO_ITUNES_COUNTRY` in `api/services/languages.py` (the central language registry — already extended with this map).
- Returns lightweight cards: `[{title, artist, image_url, rss_url}]`.
- Skips entries without a `feedUrl`.
- 8s timeout.
- Raises `requests.RequestException` on network/timeout error (does NOT swallow it — the route handler distinguishes failure from empty-results below).

**New route** in `api/routes/podcast.py`:
```
GET /api/podcasts/search?q=<term>&language=<code>
→ 200 {"results": [...]}                              # success (results may be empty)
→ 503 {"detail": "Podcast search unavailable"}         # iTunes API failed
```
- Auth required (`Depends(get_current_user_id)`).
- Calls the helper inside a try/except: on `RequestException`, returns 503. Otherwise returns 200 with results.
- Validates `q` has at least 2 chars (matching frontend gate).
- The 503 distinction lets the frontend show "Search unavailable" vs "No results".

**Existing routes are unchanged.** `POST /api/podcasts` still does the actual add — search is purely a way to discover the right `rss_url` to feed it.

### Frontend

**`web/src/services/api.js`** — add to `podcastApi`:
```js
search: (q, language) => api.get('/api/podcasts/search', { params: { q, language } }),
```

**`web/src/pages/Podcast.jsx`** — replace the existing RSS input form (lines ~178-188) with a search-as-you-type component:

- Input placeholder: `"Search for a podcast"`
- Magnifying-glass icon on left, spinner on right while request is in flight
- Debounced 250ms after each keystroke
- Min 2 chars before firing
- Results render in an absolute-positioned dropdown below the input
- Each row: 40×40 cover thumbnail · title (1 line, truncated) · artist (smaller, muted)
- Helper caps results at 10; dropdown renders all returned
- Click a row → calls `podcastApi.add({rss_url, language})` → optimistically prepend a placeholder card to the grid → on success, replace with real card → on failure, remove placeholder + show inline error

### Data Flow

```
user types "easy polish"
  └─► debounced 250ms
        └─► GET /api/podcasts/search?q=easy+polish&language=pl
              └─► iTunes Search API (country=PL, media=podcast)
                    └─► dropdown renders ≤10 result cards
                          └─► user clicks "Easy Polish Podcast"
                                └─► POST /api/podcasts {rss_url, language}
                                      └─► RSS parsed → DB row inserted
                                            └─► card appears in grid, dropdown closes
```

Note: the `POST /api/podcasts` endpoint re-parses the RSS feed for the canonical title/description/image. The iTunes data is only used for *selection* — the saved metadata comes from the feed itself.

## Component Behavior Details

### Debounce + race-safety

- A `useEffect` listens on the query string. On change: `setTimeout(fire, 250)`, returning a cleanup that clears the timer.
- Each fired request is tagged with the query that triggered it. When the response arrives, compare against the *current* query — if different, discard. Prevents flicker if a fast typer pauses mid-word.

### Dropdown dismissal

- Click outside: closes dropdown, query stays
- Esc key: clears query and closes dropdown
- Picking a result: closes dropdown
- Switching the language selector: clears query + results + closes dropdown (otherwise stale results from another language would show)

### "Already in library" state

- For each result, compare its `rss_url` against the user's current `podcasts` state
- Matching rows show a small "Added" badge, are visually de-emphasized, and clicking is a no-op

### Add flow (optimistic)

1. Dropdown closes immediately on click
2. A placeholder card with the iTunes cover image is prepended to the grid with a small spinner overlay
3. `POST /api/podcasts` runs in the background
4. On success: replace placeholder with the real DB row
5. On failure: remove placeholder, show inline error near the search input ("Couldn't add this podcast — try another")

## Edge Cases

| Case | Behavior |
|---|---|
| Query < 2 chars | No request, dropdown hidden |
| Empty results | Dropdown shows "No results for '…'" row |
| iTunes entry without `feedUrl` | Skipped server-side |
| iTunes API timeout/network error | Route returns 503; frontend shows "Search unavailable — try again" inline |
| User picks a podcast already in library | Row shows "Added" badge, click no-op |
| Stale response arrives after newer query | Discarded via query-tag check |
| User switches language mid-search | Query + results cleared |
| RSS parse fails on add | Backend 400; frontend removes placeholder, shows "Couldn't add this podcast" |
| DB unique-constraint violation on `(user_id, rss_url)` | Same as duplicate: surface "Already in your library" |

## Error Handling Philosophy

- **Search failures are silent-ish**: small inline message, no modal. Page still works without search.
- **Add failures must be visible**: user took an explicit action that didn't complete — inline error near the search input.

## Testing

**Backend** (`api/tests/`):
- Unit test `search_itunes_podcasts` with `requests` mocked:
  - Verifies `country` param is passed when language is in `LANGUAGE_TO_ITUNES_COUNTRY`, omitted otherwise
  - Verifies entries without `feedUrl` are skipped
  - Verifies returned dict shape `{title, artist, image_url, rss_url}`
  - Verifies network error raises `RequestException` (not swallowed)
- Route test for `GET /api/podcasts/search`:
  - 401 without auth
  - 200 with `{"results": [...]}` on success
  - 200 with `{"results": []}` when iTunes returns nothing
  - 503 when helper raises `RequestException`

**Frontend** (`web/cypress/e2e/`):
- One happy-path e2e: type "easy", wait for dropdown, click first result, verify it appears in the grid. Mock `/api/podcasts/search` via `cy.intercept` so the test doesn't depend on the live external API.

## Out of Scope (Deliberately)

- Keyboard arrow-key navigation in dropdown — defer
- Recently-searched / search history
- "Search worldwide" escape hatch (rejected: language bias is correct ~95% of the time)
- Bare RSS URL paste fallback (rejected: iTunes catalog is comprehensive enough)
- Loading skeletons for search results (single inline spinner is enough)

## Files Touched

- `api/services/languages.py` — already extended with `LANGUAGE_TO_ITUNES_COUNTRY`
- `api/services/podcast_service.py` — add `search_itunes_podcasts`
- `api/routes/podcast.py` — add `GET /search` route
- `web/src/services/api.js` — add `podcastApi.search`
- `web/src/pages/Podcast.jsx` — replace RSS input with search component
- `api/tests/` — new test file for search helper + route
- `web/cypress/e2e/` — new spec for happy-path search-and-add
