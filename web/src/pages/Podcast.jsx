import { useState, useEffect, useRef } from 'react'
import { podcastApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import { useLanguages } from '../hooks/useLanguages'
import useWordPopover from '../hooks/useWordPopover'
import WordPopover from '../components/WordPopover'
import AudioPlayer from '../components/AudioPlayer'

export default function Podcast() {
  const { settings, updateSettings } = useAuthStore()
  // Languages from single source of truth
  const { languages: availableLanguages } = useLanguages()

  // Navigation state — controls which of the 3 views is shown
  const [view, setView] = useState('list') // 'list' | 'episodes' | 'study'
  const [selectedPodcast, setSelectedPodcast] = useState(null)
  const [selectedEpisode, setSelectedEpisode] = useState(null)

  // Language filter — prefer last used language, fall back to first available
  const [language, setLanguage] = useState(settings?.last_language || '')

  // Podcast list state
  const [podcasts, setPodcasts] = useState([])
  const [loadingPodcasts, setLoadingPodcasts] = useState(true)

  // Search state — replaces the old RSS input
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])  // [{title, artist, image_url, rss_url}, ...]
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')      // '' | 'unavailable' | 'add-failed'
  const [showDropdown, setShowDropdown] = useState(false)
  const [addError, setAddError] = useState('')
  const [adding, setAdding] = useState(false)             // kept: blocks UI during add
  const [deletingId, setDeletingId] = useState(null)

  // Tracks the latest query that fired a request, so out-of-order responses
  // (slow network, fast typing) can be discarded instead of overwriting fresh results.
  const latestQueryRef = useRef('')

  // Episode list state
  const [episodes, setEpisodes] = useState([])
  const [loadingEpisodes, setLoadingEpisodes] = useState(false)
  const [transcribingGuid, setTranscribingGuid] = useState(null)

  // Study mode state
  const [transcript, setTranscript] = useState([])
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(-1)
  const transcriptRef = useRef(null)

  // Word popover (shared hook)
  const { popover, openPopover, closePopover } = useWordPopover()

  // Fall back to first available language if nothing is set yet
  useEffect(() => {
    if (!language && availableLanguages.length > 0) {
      setLanguage(availableLanguages[0].code)
    }
  }, [availableLanguages, language])

  // ── Fetch podcasts when language changes ──
  useEffect(() => {
    if (!language) return
    setLoadingPodcasts(true)
    podcastApi.list(language)
      .then(({ data }) => setPodcasts(data.podcasts || []))
      .catch(console.error)
      .finally(() => setLoadingPodcasts(false))
  }, [language])

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

    setSearchError('')
    latestQueryRef.current = q

    const timer = setTimeout(async () => {
      // Loading flips on only after the debounce fires, so the spinner
      // doesn't flicker on every keystroke while the user is mid-word.
      setSearchLoading(true)
      try {
        const { data } = await podcastApi.search(q, language)
        // Drop stale response if the user has typed more since this request fired
        if (latestQueryRef.current !== q) return
        setSearchResults(data.results || [])
        setShowDropdown(true)
      } catch {
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

  // Click outside the search wrapper closes the dropdown — standard
  // dropdown UX. Uses mousedown so the close happens before any click
  // handler inside the dropdown could fire.
  const searchWrapperRef = useRef(null)
  useEffect(() => {
    const onMouseDown = (e) => {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [])

  // ── Delete podcast ──
  const handleDelete = async (e, podcastId) => {
    e.stopPropagation()
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
      setView('study')
    } catch (err) {
      console.error(err)
    }
  }

  // ── Audio time update → highlight current transcript segment ──
  const handleAudioTimeUpdate = (t) => {
    const idx = transcript.findIndex(seg => t >= seg.start && t < seg.end)
    if (idx !== currentSegmentIndex) {
      setCurrentSegmentIndex(idx)
      const el = document.getElementById(`segment-${idx}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  // ── Word click handler ──
  const handleWordClick = (word, e) => {
    const clean = word.replace(/[^\p{L}\p{M}'-]/gu, '').trim()
    if (!clean) return
    closePopover()
    const rect = e.target.getBoundingClientRect()
    openPopover(clean, rect)
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
        {/* Search input + dropdown */}
        <div ref={searchWrapperRef} className="relative mb-2">
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
              disabled={adding}
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
        </div>
        {addError && <p className="text-red-400 text-sm mb-4">{addError}</p>}

        {/* Language selector */}
        <select
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value)
            updateSettings({ last_language: e.target.value })
            // Clear search — results from another language would be misleading
            setSearchQuery('')
            setSearchResults([])
            setShowDropdown(false)
          }}
          className="mb-6 px-4 py-2.5 bg-surface border border-border rounded-xl text-text text-sm appearance-none cursor-pointer focus:outline-none focus:border-accent"
          style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', backgroundSize: '16px' }}
        >
          {availableLanguages.map(lang => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>

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
          onClick={() => setView('list')}
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
                      <button
                        onClick={() => handleTranscribe(ep)}
                        disabled={transcribingGuid === ep.guid}
                        className="px-3 py-1.5 bg-accent text-white text-xs rounded-md hover:bg-accent/90 disabled:opacity-50"
                      >
                        {transcribingGuid === ep.guid ? 'Transcribing...' : 'Save & Transcribe'}
                      </button>
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
  // VIEW 3: STUDY MODE
  // ═══════════════════════════════════════════
  return (
    <div>
      {/* Back button */}
      <button
        onClick={() => setView('episodes')}
        className="text-accent text-sm mb-4 hover:underline"
      >
        ← Back to Episodes
      </button>

      {/* Episode title */}
      <h2 className="text-lg font-bold text-text mb-4">{selectedEpisode?.title}</h2>

      {/* Audio player */}
      {/* sticky: sticks to top of viewport when scrolled past, so controls
           are always reachable. z-10 keeps it above transcript text. */}
      <div className="bg-surface border border-border rounded-xl p-4 mb-6 sticky top-2 z-10 shadow-sm">
        <AudioPlayer
          src={selectedEpisode?.audio_url}
          onTimeUpdate={handleAudioTimeUpdate}
        />
      </div>

      {/* Transcript + popover share a relative container */}
      <div ref={transcriptRef} className="leading-relaxed text-base relative">
        {transcript.map((seg, i) => (
          <span
            key={i}
            id={`segment-${i}`}
            className={`inline ${
              i === currentSegmentIndex
                ? 'bg-accent/10 rounded-sm'
                : 'text-muted'
            }`}
            style={{ transition: 'all 0.3s ease' }}
          >
            {seg.text.split(/(\s+)/).map((token, j) => {
              const isWord = /\p{L}/u.test(token)
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

        {/* Word popover — must be inside the relative container */}
        {popover && (
          <WordPopover
            word={popover.word}
            rect={popover.rect}
            language={language}
            motherTongue={settings?.mother_tongue}
            onClose={closePopover}
          />
        )}
      </div>
    </div>
  )
}
