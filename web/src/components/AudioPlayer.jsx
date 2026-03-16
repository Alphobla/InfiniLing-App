import { useState, useRef, useEffect } from 'react'

/**
 * AudioPlayer — reusable custom audio player with play/pause, progress bar,
 * and ±0.1 speed controls. Used by Podcast study mode and StoryGenerator.
 *
 * Props:
 *   src        — audio URL
 *   onTimeUpdate(currentTime) — optional callback fired on each time update
 */
export default function AudioPlayer({ src, onTimeUpdate }) {
  const audioRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1.0)

  // Sync playback rate to audio element
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = playbackRate
  }, [playbackRate])

  // Reset state when src changes
  useEffect(() => {
    setIsPlaying(false)
    setCurrentTime(0)
    setDuration(0)
    setPlaybackRate(1.0)
  }, [src])

  const handleTimeUpdate = () => {
    const t = audioRef.current?.currentTime || 0
    const d = audioRef.current?.duration || 0
    setCurrentTime(t)
    onTimeUpdate?.(t, d)
  }

  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    /* sticky — stays at top of viewport once scrolled past.
       top-0: sticks at the very top. z-10: sits above page content.
       bg-background: solid background so content doesn't show through.
       shadow-sm: subtle shadow to visually separate from content below. */
    <div>
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={() => {
          setDuration(audioRef.current?.duration || 0)
          if (audioRef.current) audioRef.current.playbackRate = playbackRate
        }}
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

        {/* Rewind 5s — seeks the audio element backward by 5 seconds.
           Math.max(0, ...) prevents seeking before the start of the track. */}
        <button
          onClick={() => {
            if (audioRef.current) audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 5)
          }}
          className="w-7 h-7 rounded bg-surface border border-border text-muted hover:text-text text-sm flex items-center justify-center flex-shrink-0"
          title="Rewind 5s"
        >
          -5
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
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => setPlaybackRate(r => Math.round(Math.max(0.5, r - 0.1) * 10) / 10)}
            className="w-7 h-7 rounded bg-surface border border-border text-muted hover:text-text text-sm flex items-center justify-center"
          >
            −
          </button>
          <span className="w-10 text-center text-xs text-text">{playbackRate.toFixed(1)}x</span>
          <button
            onClick={() => setPlaybackRate(r => Math.round(Math.min(2.0, r + 0.1) * 10) / 10)}
            className="w-7 h-7 rounded bg-surface border border-border text-muted hover:text-text text-sm flex items-center justify-center"
          >
            +
          </button>
        </div>
      </div>
    </div>
  )
}
