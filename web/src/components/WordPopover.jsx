import { useState, useEffect, useRef } from 'react'
import { vocabularyApi } from '../services/api'

// 5-level frequency scale judged by the LLM
const FREQUENCY_COLORS = {
  'Essential': { bg: '#2D8A7B', text: 'white' },
  'Common': { bg: '#3D9E8C', text: 'white' },
  'Intermediate': { bg: '#5AAF8F', text: 'white' },
  'Advanced': { bg: '#D4880F', text: 'white' },
  'Rare': { bg: '#C53030', text: 'white' },
  'Unknown': { bg: '#78756F', text: 'white' },
}

export default function WordPopover({ word, rect, language, motherTongue, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const popoverRef = useRef(null)
  const [pos, setPos] = useState({ top: 0, left: 0, flipped: false })

  // Position the popover below (or above) the word
  useEffect(() => {
    if (!popoverRef.current) return
    const popEl = popoverRef.current
    const popRect = popEl.getBoundingClientRect()
    const parentRect = popEl.offsetParent.getBoundingClientRect()

    // Horizontal: center on the word, clamp to parent edges
    let left = rect.left + rect.width / 2 - parentRect.left - popRect.width / 2
    left = Math.max(0, Math.min(left, parentRect.width - popRect.width))

    // Vertical: prefer below the word
    const spaceBelow = window.innerHeight - rect.bottom
    const flipped = spaceBelow < popRect.height + 8
    let top
    if (flipped) {
      top = rect.top - parentRect.top - popRect.height - 4
    } else {
      top = rect.bottom - parentRect.top + 4
    }

    setPos({ top, left, flipped })
  }, [rect, data, loading])

  // Fetch translation
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setData(null)
    setSaved(false)

    vocabularyApi.enhance({ word, language_from: language, language_to: motherTongue })
      .then(({ data: result }) => {
        if (!cancelled) setData(result)
      })
      .catch(err => {
        if (!cancelled) setError(err.response?.data?.detail || 'Translation failed')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [word, language, motherTongue])

  // Close on click/tap outside
  useEffect(() => {
    const handle = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        onClose()
      }
    }
    // Delay so the interaction that opened us doesn't immediately close us
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handle)
      document.addEventListener('touchstart', handle)
    }, 100)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('mousedown', handle)
      document.removeEventListener('touchstart', handle)
    }
  }, [onClose])

  const handleSave = async () => {
    if (!data || saving) return
    setSaving(true)
    try {
      await vocabularyApi.create({
        word,
        lemma: data.lemma,
        translation: data.translation,
        secondary_translation: data.secondary_translation || null,
        language_from: language,
        language_to: motherTongue,
        frequency_level: data.frequency_level,
        example_sentence_original: data.example_sentence_original || null,
        example_sentence_translation: data.example_sentence_translation || null,
      })
      setSaved(true)
      setTimeout(onClose, 800)
    } catch (err) {
      alert('Failed to save: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  const freqColors = FREQUENCY_COLORS[data?.frequency_level] || FREQUENCY_COLORS['Unknown']

  return (
    <div
      ref={popoverRef}
      className="word-popover absolute z-50 w-72 bg-surface rounded-xl shadow-lift border border-border animate-scale-in"
      style={{ top: pos.top, left: pos.left }}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-2 right-2 p-1.5 text-muted hover:text-text hover:bg-bg rounded-lg transition-all"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div className="p-4">
        {/* Loading state */}
        {loading && (
          <div className="flex items-center gap-3 py-2">
            <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-muted">Translating "{word}"...</span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="text-sm text-accent">{error}</div>
        )}

        {/* Result */}
        {data && !data.enhancement_failed && (
          <div className="space-y-3">
            {/* Lemma */}
            <p className="text-lg font-semibold text-text pr-6">{data.lemma}</p>

            {/* Translation */}
            <div>
              <p className="text-accent font-medium">{data.translation}</p>
              {data.secondary_translation && (
                <p className="text-sm text-muted">{data.secondary_translation}</p>
              )}
            </div>

            {/* Frequency badge */}
            <span
              className="inline-block px-2 py-0.5 rounded text-xs font-medium"
              style={{ backgroundColor: freqColors.bg, color: freqColors.text }}
            >
              {data.frequency_level || 'Unknown'}
            </span>

            {/* Example sentence */}
            {data.example_sentence_original && (
              <div className="border-t border-border pt-3">
                <p className="text-sm text-text italic">{data.example_sentence_original}</p>
                {data.example_sentence_translation && (
                  <p className="text-xs text-muted mt-1">{data.example_sentence_translation}</p>
                )}
              </div>
            )}

            {/* Save button */}
            <button
              onClick={handleSave}
              disabled={saving || saved}
              className={`w-full py-2 rounded-lg text-sm font-medium transition-all ${
                saved
                  ? 'bg-success-light text-success border border-success/20'
                  : 'bg-accent text-white hover:bg-accent-hover disabled:opacity-50'
              }`}
            >
              {saved ? 'Saved!' : saving ? 'Saving...' : 'Save to Vocabulary'}
            </button>
          </div>
        )}

        {/* Enhancement failed */}
        {data?.enhancement_failed && (
          <div className="text-sm text-muted py-2">
            Could not translate "{word}".
          </div>
        )}
      </div>
    </div>
  )
}
