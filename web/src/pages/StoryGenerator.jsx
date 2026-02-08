import { useState, useEffect, useRef, useCallback } from 'react'
import { generateApi, vocabularyApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

const STYLE_OPTIONS = ['Informal', 'Business', 'Academic', 'Creative']
const FORMAT_OPTIONS = ['Dialogue', 'Essay', 'Monologue', 'Creative']

export default function StoryGenerator() {
  // Settings state
  const [languages, setLanguages] = useState([])
  const [language, setLanguage] = useState('')
  const [wordCount, setWordCount] = useState(10)
  const [newWordCount, setNewWordCount] = useState(2)
  const [targetLength, setTargetLength] = useState(150)
  const [topic, setTopic] = useState('')
  const [style, setStyle] = useState('')
  const [customStyle, setCustomStyle] = useState('')
  const [format, setFormat] = useState('')
  const [customFormat, setCustomFormat] = useState('')

  // Generation state
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [story, setStory] = useState(null)
  const [storyTitle, setStoryTitle] = useState('')
  const [stale, setStale] = useState(false) // true when settings changed after last generation

  // Audio state
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioLoading, setAudioLoading] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const audioRef = useRef(null)
  const storyRef = useRef(null)

  // Word popover state
  const [popover, setPopover] = useState(null) // { word, x, y }
  const { settings } = useAuthStore()

  useEffect(() => {
    generateApi.languages()
      .then(({ data }) => {
        const langs = data.languages || []
        setLanguages(langs)
        if (langs.length === 1) setLanguage(langs[0])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // Clamp newWordCount when wordCount changes
  useEffect(() => {
    if (newWordCount > wordCount) setNewWordCount(wordCount)
  }, [wordCount])

  // When any setting changes after a story was generated, mark as stale
  // so the Generate button reappears instead of "View Text"
  useEffect(() => {
    if (story) setStale(true)
  }, [language, wordCount, newWordCount, targetLength, topic, style, customStyle, format, customFormat])

  // Sync playback rate to audio element
  useEffect(() => {
    if (audioRef.current) audioRef.current.playbackRate = playbackRate
  }, [playbackRate, audioUrl])

  const resetSettings = () => {
    setWordCount(10)
    setNewWordCount(2)
    setTargetLength(150)
    setTopic('')
    setStyle('')
    setCustomStyle('')
    setFormat('')
    setCustomFormat('')
  }

  const handleGenerate = async () => {
    if (!language) return
    setGenerating(true)
    setStale(false)
    setStory(null)
    setAudioUrl(null)
    setPlaybackRate(1.0)

    try {
      const effectiveStyle = style === 'Other' ? customStyle : style
      const effectiveFormat = format === 'Other' ? customFormat : format

      const { data } = await generateApi.story({
        language,
        word_count: wordCount,
        new_word_count: newWordCount,
        target_length: targetLength,
        topic: topic || undefined,
        style: effectiveStyle || undefined,
        format: effectiveFormat || undefined,
      })
      setStoryTitle(data.title || '')
      setStory(data.story)
    } catch (err) {
      console.error('Failed to generate text:', err)
      alert('Failed to generate text. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const handleAudio = async () => {
    if (!story) return
    setAudioLoading(true)

    try {
      const cacheKey = `/audio/${btoa(unescape(encodeURIComponent(story.slice(0, 100))))}`
      const cache = await caches.open('infinilig-audio')
      const cached = await cache.match(cacheKey)

      if (cached) {
        const blob = await cached.blob()
        setAudioUrl(URL.createObjectURL(blob))
        setAudioLoading(false)
        return
      }

      const { data: blob } = await generateApi.audio({ text: story })
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)
      await cache.put(cacheKey, new Response(blob))
    } catch (err) {
      console.error('Failed to generate audio:', err)
      alert('Failed to generate audio. Please try again.')
    } finally {
      setAudioLoading(false)
    }
  }

  // Read the word the browser selected (after double-click or long-press selection)
  const getSelectedWord = () => {
    const sel = window.getSelection()
    if (!sel || sel.isCollapsed || !sel.rangeCount) return null

    const word = sel.toString().trim().replace(/[^\p{L}\p{M}'-]/gu, '')
    if (!word) return null

    const rect = sel.getRangeAt(0).getBoundingClientRect()
    return { word, rect }
  }

  // Desktop: double-click selects a word automatically, we just read it
  const handleWordDoubleClick = () => {
    const result = getSelectedWord()
    if (result) {
      setPopover({ word: result.word, rect: result.rect })
    }
  }

  // Mobile: long-press a word — use caretRangeFromPoint since there's no auto-selection
  const longPressTimer = useRef(null)
  const handleTouchStart = (e) => {
    const touch = e.touches[0]
    const tx = touch.clientX, ty = touch.clientY
    longPressTimer.current = setTimeout(() => {
      // Try to get word at touch point
      const range = document.caretRangeFromPoint?.(tx, ty)
      if (!range) return

      // Expand to word boundaries manually
      const textNode = range.startContainer
      if (textNode.nodeType !== Node.TEXT_NODE) return
      const text = textNode.textContent
      let start = range.startOffset, end = range.startOffset
      const isWordChar = (c) => /[\p{L}\p{M}'-]/u.test(c)
      while (start > 0 && isWordChar(text[start - 1])) start--
      while (end < text.length && isWordChar(text[end])) end++

      const word = text.slice(start, end).trim()
      if (!word) return

      // Create a range for positioning
      const wordRange = document.createRange()
      wordRange.setStart(textNode, start)
      wordRange.setEnd(textNode, end)
      const rect = wordRange.getBoundingClientRect()

      setPopover({ word, rect })
    }, 500)
  }
  const handleTouchEnd = () => {
    clearTimeout(longPressTimer.current)
  }

  const closePopover = useCallback(() => setPopover(null), [])

  const slower = () => setPlaybackRate(r => Math.max(0.5, +(r - 0.05).toFixed(2)))
  const faster = () => setPlaybackRate(r => Math.min(2.0, +(r + 0.05).toFixed(2)))
  const resetSpeed = () => setPlaybackRate(1.0)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (languages.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-up">
        <div className="w-20 h-20 bg-warning-light rounded-2xl flex items-center justify-center mx-auto mb-6">
          <span className="text-4xl">📚</span>
        </div>
        <h1 className="text-xl font-semibold text-text mb-2">No vocabulary yet</h1>
        <p className="text-muted">Add some words first to generate texts.</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Settings Panel */}
      <div className="bg-surface rounded-2xl shadow-soft border border-border overflow-hidden animate-fade-up">
        {/* Header */}
        <div className="px-6 py-5 border-b border-border">
          <h1 className="text-lg font-semibold text-text">Text Generator</h1>
        </div>

        {/* Language + Word Sliders */}
        <div className="px-6 py-6 border-b border-border space-y-5">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-3 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', backgroundSize: '20px' }}
          >
            <option value="">Language...</option>
            {languages.map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted">Words to include</span>
              <span className="text-accent font-semibold">{wordCount}</span>
            </div>
            <input
              type="range" min="5" max="20" value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <div className="flex items-center text-sm mb-2">
              <span className="text-muted">New</span>
              <span className="text-accent font-semibold ml-1.5">{newWordCount}</span>
              <span className="text-border mx-3">·</span>
              <span className="text-muted">Review</span>
              <span className="text-accent font-semibold ml-1.5">{wordCount - newWordCount}</span>
            </div>
            <input
              type="range" min="0" max={wordCount} value={newWordCount}
              onChange={(e) => setNewWordCount(Number(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        {/* Length + Refinements */}
        <div className="px-6 py-6 border-b border-border space-y-5">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted">Target length</span>
              <span className="text-accent font-semibold">{targetLength} words</span>
            </div>
            <input
              type="range" min="20" max="300" step="10" value={targetLength}
              onChange={(e) => setTargetLength(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Topic (optional)"
            className="w-full px-4 py-3 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60"
          />

          <div>
            <span className="text-sm text-muted">Style</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {STYLE_OPTIONS.map(opt => (
                <button
                  key={opt}
                  onClick={() => setStyle(s => s === opt ? '' : opt)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
                    style === opt
                      ? 'border-accent bg-accent-light text-accent'
                      : 'border-border text-muted hover:border-muted'
                  }`}
                >
                  {opt}
                </button>
              ))}
              <button
                onClick={() => setStyle(s => s === 'Other' ? '' : 'Other')}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
                  style === 'Other'
                    ? 'border-accent bg-accent-light text-accent'
                    : 'border-border text-muted hover:border-muted'
                }`}
              >
                Other...
              </button>
            </div>
            {style === 'Other' && (
              <input
                type="text"
                value={customStyle}
                onChange={(e) => setCustomStyle(e.target.value)}
                placeholder="Custom style..."
                className="w-full mt-2 px-4 py-2.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 text-sm"
              />
            )}
          </div>

          <div>
            <span className="text-sm text-muted">Format</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {FORMAT_OPTIONS.map(opt => (
                <button
                  key={opt}
                  onClick={() => setFormat(f => f === opt ? '' : opt)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
                    format === opt
                      ? 'border-accent bg-accent-light text-accent'
                      : 'border-border text-muted hover:border-muted'
                  }`}
                >
                  {opt}
                </button>
              ))}
              <button
                onClick={() => setFormat(f => f === 'Other' ? '' : 'Other')}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
                  format === 'Other'
                    ? 'border-accent bg-accent-light text-accent'
                    : 'border-border text-muted hover:border-muted'
                }`}
              >
                Other...
              </button>
            </div>
            {format === 'Other' && (
              <input
                type="text"
                value={customFormat}
                onChange={(e) => setCustomFormat(e.target.value)}
                placeholder="Custom format..."
                className="w-full mt-2 px-4 py-2.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 text-sm"
              />
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex items-center justify-between">
          <button
            onClick={resetSettings}
            className="text-sm text-muted hover:text-text transition-colors"
          >
            Reset
          </button>
          {story && !generating && !stale ? (
            <button
              onClick={() => storyRef.current?.scrollIntoView({ behavior: 'smooth' })}
              className="px-6 py-2.5 bg-accent text-white rounded-xl text-sm font-medium transition-all hover:-translate-y-0.5 flex items-center gap-2 animate-pulse"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              View Text
            </button>
          ) : (
            <button
              onClick={handleGenerate}
              disabled={!language || generating}
              className="px-6 py-2.5 bg-accent text-white rounded-xl text-sm font-medium hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0 flex items-center gap-2"
            >
              {generating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Generating...
                </>
              ) : (
                'Generate'
              )}
            </button>
          )}
        </div>
      </div>

      {/* Generated Text */}
      {story && (
        <div ref={storyRef} className="bg-surface rounded-2xl shadow-soft border border-border mt-8 overflow-hidden animate-fade-up">
          <div className="px-6 py-5 border-b border-border flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text">{storyTitle || 'Generated Text'}</h2>
            <button
              onClick={handleAudio}
              disabled={audioLoading}
              className="flex items-center gap-2 px-4 py-2 bg-bg border border-border rounded-xl hover:bg-border/50 disabled:opacity-50 transition-all text-sm text-muted"
            >
              {audioLoading ? (
                <>
                  <span className="w-4 h-4 border-2 border-muted/30 border-t-muted rounded-full animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  </svg>
                  Listen
                </>
              )}
            </button>
          </div>

          {/* Audio Player with Speed Controls */}
          {audioUrl && (
            <div className="px-4 sm:px-6 py-4 border-b border-border flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
              {/* Speed controls */}
              <div className="flex items-center justify-center gap-1 bg-bg rounded-lg p-1">
                <button
                  onClick={slower}
                  disabled={playbackRate <= 0.5}
                  className="px-2.5 py-1.5 rounded text-sm font-medium text-muted hover:bg-surface hover:shadow-soft disabled:opacity-30 transition-all"
                  title="Slower"
                >
                  −
                </button>
                <button
                  onClick={resetSpeed}
                  className="px-2.5 py-1.5 rounded text-sm font-mono font-semibold text-text hover:bg-surface hover:shadow-soft transition-all min-w-[3.5rem] text-center"
                  title="Reset to 1.0x"
                >
                  {playbackRate.toFixed(2)}x
                </button>
                <button
                  onClick={faster}
                  disabled={playbackRate >= 2.0}
                  className="px-2.5 py-1.5 rounded text-sm font-medium text-muted hover:bg-surface hover:shadow-soft disabled:opacity-30 transition-all"
                  title="Faster"
                >
                  +
                </button>
              </div>

              {/* Audio element */}
              <audio
                ref={audioRef}
                controls
                className="flex-1 h-10 sm:h-8 w-full"
                src={audioUrl}
                onLoadedMetadata={() => {
                  if (audioRef.current) audioRef.current.playbackRate = playbackRate
                }}
              />
            </div>
          )}

          {/* Text Content — double-click (desktop) or long-press (mobile) a word to look it up */}
          <div className="px-6 py-6 relative">
            <p
              className="text-text leading-relaxed whitespace-pre-wrap text-lg cursor-text select-text"
              onDoubleClick={handleWordDoubleClick}
              onTouchStart={handleTouchStart}
              onTouchEnd={handleTouchEnd}
              onTouchMove={handleTouchEnd}
            >
              {story}
            </p>
            <p className="text-xs text-muted/50 mt-4 pointer-fine">Double-click a word to translate</p>
            <p className="text-xs text-muted/50 mt-4 pointer-coarse">Hold a word to translate</p>
            {popover && (
              <WordPopover
                word={popover.word}
                rect={popover.rect}
                language={language}
                motherTongue={settings?.mother_tongue || 'en'}
                onClose={closePopover}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Word Popover — shown when double-clicking/long-pressing a word in the story
// ============================================================================

const FREQUENCY_COLORS = {
  'Top 1,000': { bg: '#2D8A7B', text: 'white' },
  'Top 5,000': { bg: '#3D9E8C', text: 'white' },
  'Top 10,000': { bg: '#5AAF8F', text: 'white' },
  'Top 20,000': { bg: '#D4880F', text: 'white' },
  'Top 50,000': { bg: '#E69B3A', text: 'white' },
  'Rare': { bg: '#C53030', text: 'white' },
  'Unknown': { bg: '#78756F', text: 'white' },
}

function WordPopover({ word, rect, language, motherTongue, onClose }) {
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

  // Close on click outside
  useEffect(() => {
    const handle = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        onClose()
      }
    }
    // Delay so the double-click that opened us doesn't immediately close us
    const timer = setTimeout(() => document.addEventListener('mousedown', handle), 10)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('mousedown', handle)
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
        frequency_rank: data.frequency_rank,
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
      className="absolute z-50 w-72 bg-surface rounded-xl shadow-lift border border-border animate-scale-in"
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
