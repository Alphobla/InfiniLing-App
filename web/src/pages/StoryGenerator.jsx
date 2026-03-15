import { useState, useEffect, useRef } from 'react'
import { generateApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import useWordPopover from '../hooks/useWordPopover'
import WordPopover from '../components/WordPopover'
import AudioPlayer from '../components/AudioPlayer'
import { useLanguages } from '../hooks/useLanguages'

// Presets control wordCount, newWordCount, and targetLength together
const PRESETS = [
  { key: 'quick', label: '⚡', tip: 'Quick', words: 5, newWords: 1, length: 50 },
  { key: 'standard', label: '📖', tip: 'Standard', words: 10, newWords: 3, length: 150 },
  { key: 'deep', label: '🏋️', tip: 'Deep Dive', words: 15, newWords: 5, length: 300 },
]

const STYLE_OPTIONS = [
  { label: '😊', value: 'Casual', tip: 'Casual' },
  { label: '💼', value: 'Formal', tip: 'Formal' },
  { label: '📚', value: 'Academic', tip: 'Academic' },
  { label: '😂', value: 'Humorous', tip: 'Humorous' },
]
const FORMAT_OPTIONS = [
  { label: '💬', value: 'Dialogue', tip: 'Dialogue' },
  { label: '📝', value: 'Essay', tip: 'Essay' },
  { label: '📰', value: 'Article', tip: 'Article' },
  { label: '✉️', value: 'Letter', tip: 'Letter' },
]

export default function StoryGenerator() {
  // Languages from single source of truth
  const { languages: availableLanguages, languageMap, loading: loadingLanguages } = useLanguages()
  
  // Settings state
  const [language, setLanguage] = useState('')
  const [preset, setPreset] = useState('standard')
  const [wordCount, setWordCount] = useState(10)
  const [newWordCount, setNewWordCount] = useState(3)
  const [targetLength, setTargetLength] = useState(150)
  const [topic, setTopic] = useState('')
  const [style, setStyle] = useState('')
  const [customStyle, setCustomStyle] = useState('')
  const [format, setFormat] = useState('')
  const [customFormat, setCustomFormat] = useState('')

  // Generation state
  const [generating, setGenerating] = useState(false)
  const [story, setStory] = useState(null)
  const [storyTitle, setStoryTitle] = useState('')
  const [stale, setStale] = useState(false)

  // Audio state
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioLoading, setAudioLoading] = useState(false)
  const [currentWordIndex, setCurrentWordIndex] = useState(-1)
  const storyRef = useRef(null)

  // Word popover state
  const { popover, openPopover, closePopover } = useWordPopover()
  const { settings } = useAuthStore()

  // Set default language when languages load
  useEffect(() => {
    if (availableLanguages.length > 0 && !language) {
      // Default to first available language
      setLanguage(availableLanguages[0].code)
    }
  }, [availableLanguages, language])

  // Apply preset values when preset changes
  const applyPreset = (key) => {
    const p = PRESETS.find(pr => pr.key === key)
    if (!p) return
    setPreset(key)
    setWordCount(p.words)
    setNewWordCount(p.newWords)
    setTargetLength(p.length)
  }

  // When any setting changes after a story was generated, mark as stale
  useEffect(() => {
    if (story) setStale(true)
  }, [language, preset, topic, style, customStyle, format, customFormat])

  const resetSettings = () => {
    applyPreset('standard')
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

  // Word click handler (single click, same as podcast)
  const handleWordClick = (word, e) => {
    const clean = word.replace(/[^\p{L}\p{M}'-]/gu, '').trim()
    if (!clean) return
    closePopover()
    const rect = e.target.getBoundingClientRect()
    openPopover(clean, rect)
  }

  if (loadingLanguages) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (availableLanguages.length === 0) {
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
      {/* Settings Panel — single flowing card */}
      <div className="bg-surface rounded-2xl shadow-soft border border-border overflow-hidden animate-fade-up px-6 py-6 space-y-5">

        {/* Topic + Language — side by side */}
        <div className="flex gap-2">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Topic (optional)"
            className="flex-1 px-4 py-3 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60"
          />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="shrink-0 px-4 py-3 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', backgroundSize: '16px', paddingRight: '32px' }}
          >
            <option value="">Language...</option>
            {availableLanguages.map(lang => (
              <option key={lang.code} value={lang.code}>{lang.name}</option>
            ))}
          </select>
        </div>

        {/* Preset cards — emoji + label, selected shows accent border */}
        <div className="flex gap-2">
          {PRESETS.map(p => (
            <button
              key={p.key}
              onClick={() => applyPreset(p.key)}
              className={`flex-1 py-2.5 rounded-xl border transition-all flex flex-col items-center gap-0.5 ${
                preset === p.key
                  ? 'border-accent bg-accent-light'
                  : 'border-border hover:border-muted'
              }`}
            >
              <span className="text-xl">{p.label}</span>
              <span className={`text-xs ${preset === p.key ? 'text-accent' : 'text-muted'}`}>{p.tip}</span>
            </button>
          ))}
        </div>
        {/* Subtle specs for the active preset */}
        <p className="text-xs text-muted text-center -mt-2">
          ~{targetLength} words · {newWordCount} new · {wordCount - newWordCount} review
        </p>

        {/* Style & Format — icon chips */}
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted w-12">Style</span>
          <div className="flex gap-2">
            {STYLE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                title={opt.tip}
                onClick={() => setStyle(s => s === opt.value ? '' : opt.value)}
                className={`w-9 h-9 text-lg rounded-lg border transition-all flex items-center justify-center ${
                  style === opt.value
                    ? 'border-accent bg-accent-light'
                    : 'border-border hover:border-muted'
                }`}
              >
                {opt.label}
              </button>
            ))}
            <button
              title="Custom style"
              onClick={() => setStyle(s => s === 'Other' ? '' : 'Other')}
              className={`w-9 h-9 text-sm rounded-lg border transition-all flex items-center justify-center ${
                style === 'Other'
                  ? 'border-accent bg-accent-light text-accent'
                  : 'border-border text-muted hover:border-muted'
              }`}
            >
              ...
            </button>
          </div>
        </div>
        {style === 'Other' && (
          <input
            type="text"
            value={customStyle}
            onChange={(e) => setCustomStyle(e.target.value)}
            placeholder="Custom style..."
            className="w-full px-4 py-2.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 text-sm"
          />
        )}

        <div className="flex items-center gap-4">
          <span className="text-sm text-muted w-12">Format</span>
          <div className="flex gap-2">
            {FORMAT_OPTIONS.map(opt => (
              <button
                key={opt.value}
                title={opt.tip}
                onClick={() => setFormat(f => f === opt.value ? '' : opt.value)}
                className={`w-9 h-9 text-lg rounded-lg border transition-all flex items-center justify-center ${
                  format === opt.value
                    ? 'border-accent bg-accent-light'
                    : 'border-border hover:border-muted'
                }`}
              >
                {opt.label}
              </button>
            ))}
            <button
              title="Custom format"
              onClick={() => setFormat(f => f === 'Other' ? '' : 'Other')}
              className={`w-9 h-9 text-sm rounded-lg border transition-all flex items-center justify-center ${
                format === 'Other'
                  ? 'border-accent bg-accent-light text-accent'
                  : 'border-border text-muted hover:border-muted'
              }`}
            >
              ...
            </button>
          </div>
        </div>
        {format === 'Other' && (
          <input
            type="text"
            value={customFormat}
            onChange={(e) => setCustomFormat(e.target.value)}
            placeholder="Custom format..."
            className="w-full px-4 py-2.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 text-sm"
          />
        )}

        {/* Dynamic summary sentence */}
        {language && (
          <p className="text-sm text-muted text-center">
            Generate {style && style !== 'Other' ? `a ${style.toLowerCase()} ` : 'a '}{format && format !== 'Other' ? format.toLowerCase() : 'text'} in {languageMap[language] || language}{topic ? ` about "${topic}"` : ''}.
          </p>
        )}

        {/* Generate button — full width, hero CTA */}
        {story && !generating && !stale ? (
          <button
            onClick={() => storyRef.current?.scrollIntoView({ behavior: 'smooth' })}
            className="w-full py-3 bg-accent text-white rounded-xl text-sm font-medium transition-all hover:-translate-y-0.5 flex items-center justify-center gap-2 animate-pulse"
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
            className="w-full py-3 bg-accent text-white rounded-xl text-sm font-medium hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0 flex items-center justify-center gap-2"
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

        {/* Reset — subtle link */}
        <button
          onClick={resetSettings}
          className="w-full text-xs text-muted hover:text-text transition-colors"
        >
          Reset to defaults
        </button>
      </div>

      {/* Generated Text */}
      {story && (
        <div ref={storyRef} className="bg-surface rounded-2xl shadow-soft border border-border mt-8 overflow-hidden animate-fade-up">
          <div className="px-6 py-5 border-b border-border flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text">{storyTitle || 'Generated Text'}</h2>
            {!audioUrl && (
              <button
                onClick={handleAudio}
                disabled={audioLoading}
                className="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-xl hover:bg-accent-hover disabled:opacity-50 transition-all text-sm font-medium animate-pulse"
              >
                {audioLoading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    </svg>
                    Read aloud
                  </>
                )}
              </button>
            )}
          </div>

          {/* Audio Player */}
          {audioUrl && (
            <div className="px-6 py-4 border-b border-border">
              <AudioPlayer
                src={audioUrl}
                onTimeUpdate={(currentTime, duration) => {
                  if (!duration) return
                  // Estimate which word chunk we're on based on linear time progression
                  // Highlight chunks of ~8 words at a time for smoother reading
                  const CHUNK_SIZE = 8
                  const tokens = story.split(/(\s+)/)
                  const totalWords = tokens.filter(t => /\p{L}/u.test(t)).length
                  const rawIdx = Math.floor((currentTime / duration) * totalWords)
                  // Snap to chunk boundaries
                  const chunkStart = Math.floor(rawIdx / CHUNK_SIZE) * CHUNK_SIZE
                  setCurrentWordIndex(chunkStart < totalWords ? chunkStart : -1)
                }}
              />
            </div>
          )}

          {/* Text Content — click a word to translate, highlight current chunk during playback */}
          <div className="px-6 py-6 relative leading-relaxed text-base">
            {(() => {
              const CHUNK_SIZE = 8
              const tokens = story.split(/(\s+)/)
              
              // Group tokens into chunks of CHUNK_SIZE words each
              const chunks = []
              let currentChunk = []
              let wordCount = 0
              
              tokens.forEach(token => {
                const isWord = /\p{L}/u.test(token)
                currentChunk.push({ token, isWord })
                if (isWord) {
                  wordCount++
                  if (wordCount % CHUNK_SIZE === 0) {
                    chunks.push(currentChunk)
                    currentChunk = []
                  }
                }
              })
              // Push remaining tokens
              if (currentChunk.length > 0) {
                chunks.push(currentChunk)
              }
              
              // Calculate which chunk is active based on currentWordIndex
              const activeChunkIdx = currentWordIndex >= 0 ? Math.floor(currentWordIndex / CHUNK_SIZE) : -1
              
              return chunks.map((chunk, chunkIdx) => {
                const isActiveChunk = audioUrl && chunkIdx === activeChunkIdx
                return (
                  <span
                    key={chunkIdx}
                    className={`inline ${
                      isActiveChunk ? 'bg-accent/10 rounded-sm text-text' : 'text-muted'
                    }`}
                    style={{ transition: 'all 0.3s ease' }}
                  >
                    {chunk.map(({ token, isWord }, j) => (
                      isWord ? (
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
                    ))}
                  </span>
                )
              })
            })()}

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
