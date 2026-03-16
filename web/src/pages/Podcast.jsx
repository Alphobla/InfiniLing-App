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
  const [rssUrl, setRssUrl] = useState('')
  const [addError, setAddError] = useState('')
  const [adding, setAdding] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  // Episode list state
  const [episodes, setEpisodes] = useState([])
  const [loadingEpisodes, setLoadingEpisodes] = useState(false)
  const [transcribingGuid, setTranscribingGuid] = useState(null)

  // Study mode state
  const [transcript, setTranscript] = useState([])
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(-1)
  const transcriptRef = useRef(null)

  // Preview audio (episode list play button)
  const [previewAudioUrl, setPreviewAudioUrl] = useState(null)
  const previewAudioRef = useRef(null)

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

        {/* Language selector */}
        <select
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value)
            // Persist the selected language so it's remembered next time
            updateSettings({ last_language: e.target.value })
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
                onClick={() => openPodcast(pod)}
                className="aspect-square rounded-xl overflow-hidden bg-surface border border-border hover:border-accent transition-colors relative group"
              >
                {pod.image_url ? (
                  <img src={pod.image_url} alt={pod.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-4xl bg-surface">
                    🎙️
                  </div>
                )}
                <div
                  onClick={(e) => handleDelete(e, pod.id)}
                  className="absolute top-1 right-1 w-6 h-6 bg-black/60 rounded-full flex items-center justify-center text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  ✕
                </div>
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
