import { useState, useEffect, useRef } from 'react'
import { generateApi } from '../services/api'

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

  // Audio state
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioLoading, setAudioLoading] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const audioRef = useRef(null)

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
      const cacheKey = `audio-${btoa(story.slice(0, 100))}`
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

  const slower = () => setPlaybackRate(r => Math.max(0.5, +(r - 0.05).toFixed(2)))
  const faster = () => setPlaybackRate(r => Math.min(2.0, +(r + 0.05).toFixed(2)))
  const resetSpeed = () => setPlaybackRate(1.0)

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Loading...</div>
  }

  if (languages.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No vocabulary found. Add some words first to generate texts.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Settings Panel */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100">
          <h1 className="text-lg font-bold text-gray-800">Text Generator</h1>
        </div>

        {/* Language + Word Sliders */}
        <div className="px-6 py-5 border-b border-gray-100 space-y-4">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
          >
            <option value="">Language...</option>
            {languages.map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Words</span>
              <span className="text-primary-600 font-semibold">{wordCount}</span>
            </div>
            <input
              type="range" min="5" max="20" value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              className="w-full accent-primary-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">New</span>
              <span className="text-primary-600 font-semibold">{newWordCount}</span>
              <span className="text-gray-400">Review</span>
              <span className="text-primary-600 font-semibold">{wordCount - newWordCount}</span>
            </div>
            <input
              type="range" min="0" max={wordCount} value={newWordCount}
              onChange={(e) => setNewWordCount(Number(e.target.value))}
              className="w-full accent-primary-600"
            />
          </div>
        </div>

        {/* Length + Refinements */}
        <div className="px-6 py-5 border-b border-gray-100 space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Length</span>
              <span className="text-primary-600 font-semibold">{targetLength} words</span>
            </div>
            <input
              type="range" min="20" max="300" step="10" value={targetLength}
              onChange={(e) => setTargetLength(Number(e.target.value))}
              className="w-full accent-primary-600"
            />
          </div>

          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Topic (optional)"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none placeholder:text-gray-400"
          />

          <div>
            <span className="text-sm text-gray-600">Style</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {STYLE_OPTIONS.map(opt => (
                <button
                  key={opt}
                  onClick={() => setStyle(s => s === opt ? '' : opt)}
                  className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                    style === opt
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 text-gray-500 hover:border-gray-300'
                  }`}
                >
                  {opt}
                </button>
              ))}
              <button
                onClick={() => setStyle(s => s === 'Other' ? '' : 'Other')}
                className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                  style === 'Other'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 text-gray-500 hover:border-gray-300'
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
                className="w-full mt-1.5 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none placeholder:text-gray-400 text-sm"
              />
            )}
          </div>

          <div>
            <span className="text-sm text-gray-600">Format</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {FORMAT_OPTIONS.map(opt => (
                <button
                  key={opt}
                  onClick={() => setFormat(f => f === opt ? '' : opt)}
                  className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                    format === opt
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 text-gray-500 hover:border-gray-300'
                  }`}
                >
                  {opt}
                </button>
              ))}
              <button
                onClick={() => setFormat(f => f === 'Other' ? '' : 'Other')}
                className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                  format === 'Other'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 text-gray-500 hover:border-gray-300'
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
                className="w-full mt-1.5 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none placeholder:text-gray-400 text-sm"
              />
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 flex items-center justify-between">
          <button
            onClick={resetSettings}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Reset
          </button>
          <button
            onClick={handleGenerate}
            disabled={!language || generating}
            className="px-5 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {generating ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Generating...
              </>
            ) : (
              'Generate'
            )}
          </button>
        </div>
      </div>

      {/* Generated Text */}
      {story && (
        <div className="bg-white rounded-xl shadow-sm mt-6 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800">Generated Text</h2>
            <button
              onClick={handleAudio}
              disabled={audioLoading}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors text-sm"
            >
              {audioLoading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  Loading audio...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  </svg>
                  Listen
                </>
              )}
            </button>
          </div>

          {/* Audio Player with Speed Controls */}
          {audioUrl && (
            <div className="px-6 py-3 border-b border-gray-100 flex items-center gap-3">
              {/* Turtle (slower) */}
              <button
                onClick={slower}
                disabled={playbackRate <= 0.5}
                className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 transition-colors"
                title="Slower"
              >
                <svg className="w-5 h-5 text-gray-600" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19.31 5.6c-.06-.09-.13-.17-.2-.25a4.34 4.34 0 0 0-1.62-1.13 3.29 3.29 0 0 0-1.27-.28 2.85 2.85 0 0 0-1.09.19l-.05.02c-.08.03-.15.07-.22.11A9.83 9.83 0 0 0 10.5 2C5.81 2 2 5.81 2 10.5c0 1.77.55 3.41 1.48 4.77L2.04 18.5a1 1 0 0 0 .97 1.22l3.23-.44A9.4 9.4 0 0 0 10.5 21c.92 0 1.81-.13 2.66-.38l.2.18c.46.38 1.07.7 1.83.7.18 0 .36-.02.54-.06l2.52-.56a1 1 0 0 0 .77-.77l.56-2.52c.16-.72-.04-1.39-.32-1.89A9.44 9.44 0 0 0 20 10.5c0-1.77-.49-3.42-1.33-4.84l.64-.06zm-2.36 10.23c.2.36.26.63.22.83l-.42 1.87-1.87.42c-.2.04-.47-.02-.83-.22a2.37 2.37 0 0 0-.15-.1l-1.1-.73-1.22.44A7.44 7.44 0 0 1 10.5 19a7.5 7.5 0 0 1-3.3-.77l-.6-.3-2.42.33.33-2.42-.3-.6A7.48 7.48 0 0 1 10.5 4c2.03 0 3.88.81 5.24 2.12l-.2.02h-.1a1 1 0 0 0-.14.01c-.93.13-1.6.76-1.98 1.55-.4.82-.55 1.84-.32 2.78a1 1 0 0 0 .44.6l2.68 1.78.83.98z" />
                </svg>
              </button>

              {/* Audio element */}
              <audio
                ref={audioRef}
                controls
                className="flex-1 h-8"
                src={audioUrl}
                onLoadedMetadata={() => {
                  if (audioRef.current) audioRef.current.playbackRate = playbackRate
                }}
              />

              {/* Speed display (click to reset) */}
              <button
                onClick={resetSpeed}
                className="text-xs font-mono font-medium text-gray-500 hover:text-primary-600 min-w-[3rem] text-center transition-colors"
                title="Reset to 1.0x"
              >
                {playbackRate.toFixed(2)}x
              </button>

              {/* Rabbit (faster) */}
              <button
                onClick={faster}
                disabled={playbackRate >= 2.0}
                className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 transition-colors"
                title="Faster"
              >
                <svg className="w-5 h-5 text-gray-600" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.05 4.28c-.47-.2-.97-.28-1.45-.28-.87 0-1.72.32-2.43.87l-.6.46c-1.06-.5-2.26-.83-3.57-.83-1.8 0-3.47.6-4.84 1.6L3.29 4.71a1 1 0 0 0-1.58 1.22l1.73 2.25A8.92 8.92 0 0 0 2 13c0 1.2.24 2.35.67 3.4L2 20a1 1 0 0 0 1 1h1a1 1 0 0 0 .93-.64l.4-1.01C6.72 20.38 8.3 21 10 21c1.13 0 2.2-.25 3.17-.69l.23.47A1 1 0 0 0 14.3 21H16a1 1 0 0 0 .97-.76l.8-3.42c.04-.15.05-.3.03-.45A8.97 8.97 0 0 0 19 13c0-.7-.09-1.37-.24-2.02l2.08-2.42a1 1 0 0 0 .16-.99 4.37 4.37 0 0 0-2.95-3.29zM10 19c-1.26 0-2.43-.38-3.42-1.02l.5-1.24a1 1 0 0 0-.5-1.32A6.96 6.96 0 0 1 4 13c0-3.86 3.14-7 7-7 .77 0 1.52.13 2.22.37l-.72.55a1 1 0 0 0-.05 1.52l1.09 1.02a1 1 0 0 0 .57.24l2.42.2A7 7 0 0 1 10 19zm8.12-10.52l-1.3 1.51a1 1 0 0 0-.2.82c.18.71.28 1.44.28 2.19 0 .55-.07 1.08-.19 1.6l-.6 2.6-.46-.93a1 1 0 0 0-.64-.52l-.13-.03A8.93 8.93 0 0 0 17.86 9a1 1 0 0 0-.04-.11l1.9-1.43a2.38 2.38 0 0 1 .6 1.02l-2.2.01z" />
                </svg>
              </button>
            </div>
          )}

          {/* Text Content */}
          <div className="px-6 py-5">
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {story}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
