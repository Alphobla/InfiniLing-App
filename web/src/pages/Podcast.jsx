import { useState, useEffect, useRef, useCallback } from 'react'
import { podcastApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import useWordPopover from '../hooks/useWordPopover'
import WordPopover from '../components/WordPopover'

export default function Podcast() {
  const { settings } = useAuthStore()

  // Navigation state — controls which of the 3 views is shown
  const [view, setView] = useState('list') // 'list' | 'episodes' | 'study'
  const [selectedPodcast, setSelectedPodcast] = useState(null)
  const [selectedEpisode, setSelectedEpisode] = useState(null)

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
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const audioRef = useRef(null)
  const transcriptRef = useRef(null)

  // Preview audio (episode list play button)
  const [previewAudioUrl, setPreviewAudioUrl] = useState(null)
  const previewAudioRef = useRef(null)

  // Word popover (shared hook)
  const { popover, openPopover, closePopover } = useWordPopover()

  // ── Fetch podcasts on mount ──
  useEffect(() => {
    podcastApi.list()
      .then(({ data }) => setPodcasts(data.podcasts || []))
      .catch(console.error)
      .finally(() => setLoadingPodcasts(false))
  }, [])

  // ── Sync playback rate ──
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = playbackRate
  }, [playbackRate])

  // ── Add podcast from RSS ──
  const handleAddPodcast = async () => {
    if (!rssUrl.trim()) return
    setAdding(true)
    setAddError('')
    try {
      const { data } = await podcastApi.add({
        rss_url: rssUrl.trim(),
        language: settings?.last_language || 'fr',
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
      setCurrentTime(0)
      setIsPlaying(false)
      setView('study')
    } catch (err) {
      console.error(err)
    }
  }

  // ── Audio time update → find current segment ──
  const handleTimeUpdate = useCallback(() => {
    if (!audioRef.current) return
    const t = audioRef.current.currentTime
    setCurrentTime(t)
    const idx = transcript.findIndex(seg => t >= seg.start && t < seg.end)
    if (idx !== currentSegmentIndex) {
      setCurrentSegmentIndex(idx)
      const el = document.getElementById(`segment-${idx}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [transcript, currentSegmentIndex])

  // ── Word click handler ──
  const handleWordClick = (word, e) => {
    const clean = word.replace(/[^\p{L}\p{M}'-]/gu, '').trim()
    if (!clean) return
    closePopover()
    const rect = e.target.getBoundingClientRect()
    openPopover(clean, rect)
  }

  // ── Format time ──
  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
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
                    {ep.is_transcribed && (
                      <p className="text-xs text-accent mt-1">✓ Transcribed</p>
                    )}
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
        onClick={() => { setView('episodes'); setIsPlaying(false); if (audioRef.current) audioRef.current.pause() }}
        className="text-accent text-sm mb-4 hover:underline"
      >
        ← Back to Episodes
      </button>

      {/* Audio player */}
      <div className="bg-surface border border-border rounded-xl p-4 mb-6">
        <audio
          ref={audioRef}
          src={selectedEpisode?.audio_url}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />
        <div className="flex items-center gap-3">
          {/* Play/pause */}
          <button
            onClick={() => {
              if (isPlaying) audioRef.current?.pause()
              else audioRef.current?.play()
            }}
            className="w-10 h-10 rounded-full bg-accent text-white flex items-center justify-center text-lg flex-shrink-0"
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          {/* Progress bar */}
          <div className="flex-1">
            <div
              className="h-1.5 bg-border rounded-full cursor-pointer relative"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const ratio = (e.clientX - rect.left) / rect.width
                if (audioRef.current) audioRef.current.currentTime = ratio * duration
              }}
            >
              <div
                className="h-full bg-accent rounded-full"
                style={{ width: duration ? `${(currentTime / duration) * 100}%` : '0%' }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-muted">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Speed controls */}
          <div className="flex gap-1 flex-shrink-0">
            {[0.75, 1, 1.25].map((rate) => (
              <button
                key={rate}
                onClick={() => setPlaybackRate(rate)}
                className={`px-2 py-1 text-xs rounded ${
                  playbackRate === rate
                    ? 'bg-accent text-white'
                    : 'bg-surface border border-border text-muted hover:text-text'
                }`}
              >
                {rate}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Transcript */}
      <div ref={transcriptRef} className="leading-relaxed text-base relative">
        {transcript.map((seg, i) => (
          <span
            key={i}
            id={`segment-${i}`}
            className={`inline ${
              i === currentSegmentIndex
                ? 'bg-accent/10 border-l-2 border-accent pl-1.5 rounded-sm'
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
      </div>

      {/* Word popover */}
      {popover && (
        <WordPopover
          word={popover.word}
          rect={popover.rect}
          language={settings?.last_language}
          motherTongue={settings?.mother_tongue}
          onClose={closePopover}
        />
      )}
    </div>
  )
}
