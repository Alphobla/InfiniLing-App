import { useState, useEffect, useRef } from 'react'
import { vocabularyApi, generateApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

export default function StoryGenerator() {
  const settings = useAuthStore((s) => s.settings)
  const [words, setWords] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [multiplier, setMultiplier] = useState(2)
  const [difficulty, setDifficulty] = useState('intermediate')
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [story, setStory] = useState(null)
  const [wordsUsed, setWordsUsed] = useState([])
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioLoading, setAudioLoading] = useState(false)
  const audioRef = useRef(null)

  useEffect(() => {
    vocabularyApi.list({ limit: 100 })
      .then(({ data }) => setWords(data.items || data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const toggleWord = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const selectAll = () => setSelectedIds(words.map(w => w.id))
  const clearSelection = () => setSelectedIds([])

  const generateStory = async () => {
    if (selectedIds.length === 0) return
    setGenerating(true)
    setStory(null)
    setWordsUsed([])
    setAudioUrl(null)

    try {
      const language = words.find(w => selectedIds.includes(w.id))?.language_from || 'English'
      const { data } = await generateApi.story({
        word_ids: selectedIds,
        language,
        difficulty,
        word_multiplier: multiplier,
      })
      setStory(data.story)
      setWordsUsed(data.words_used)
    } catch (err) {
      console.error('Failed to generate story:', err)
      alert('Failed to generate story. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const generateAudio = async () => {
    if (!story) return
    setAudioLoading(true)

    try {
      // Check cache first
      const cacheKey = `audio-${btoa(story.slice(0, 100))}`
      const cache = await caches.open('infinilig-audio')
      const cached = await cache.match(cacheKey)

      if (cached) {
        const blob = await cached.blob()
        setAudioUrl(URL.createObjectURL(blob))
        setAudioLoading(false)
        return
      }

      // Generate new audio
      const { data: blob } = await generateApi.audio({ text: story })
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)

      // Cache the audio
      await cache.put(cacheKey, new Response(blob))
    } catch (err) {
      console.error('Failed to generate audio:', err)
      alert('Failed to generate audio. Please try again.')
    } finally {
      setAudioLoading(false)
    }
  }

  // Highlight words used in story
  const highlightStory = (text) => {
    if (!wordsUsed.length) return text

    const pattern = new RegExp(`\\b(${wordsUsed.join('|')})\\b`, 'gi')
    const parts = text.split(pattern)

    return parts.map((part, i) => {
      const isHighlighted = wordsUsed.some(w => w.toLowerCase() === part.toLowerCase())
      return isHighlighted ? (
        <span key={i} className="bg-yellow-200 px-0.5 rounded">{part}</span>
      ) : part
    })
  }

  if (loading) {
    return <div className="text-center py-12">Loading vocabulary...</div>
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Story Generator</h1>

      {/* Word Selection */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Select Words ({selectedIds.length})</h2>
          <div className="flex gap-2">
            <button onClick={selectAll} className="text-sm text-primary-600 hover:underline">
              Select all
            </button>
            <button onClick={clearSelection} className="text-sm text-gray-500 hover:underline">
              Clear
            </button>
          </div>
        </div>

        {words.length === 0 ? (
          <p className="text-gray-500">No vocabulary words yet. Add some first!</p>
        ) : (
          <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
            {words.map(word => (
              <button
                key={word.id}
                onClick={() => toggleWord(word.id)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  selectedIds.includes(word.id)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {word.word}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold mb-4">Settings</h2>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Word Multiplier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Word Repetition: {multiplier}x
            </label>
            <input
              type="range"
              min="1"
              max="5"
              value={multiplier}
              onChange={(e) => setMultiplier(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Each word will appear approximately {multiplier} times
            </p>
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficulty
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
      </div>

      {/* Generate Button */}
      <button
        onClick={generateStory}
        disabled={selectedIds.length === 0 || generating}
        className="w-full py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed mb-6"
      >
        {generating ? 'Generating...' : `Generate Story (${selectedIds.length} words)`}
      </button>

      {/* Story Display */}
      {story && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Your Story</h2>
            <button
              onClick={generateAudio}
              disabled={audioLoading}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              {audioLoading ? (
                'Loading...'
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  </svg>
                  Listen
                </>
              )}
            </button>
          </div>

          {audioUrl && (
            <div className="mb-4">
              <audio ref={audioRef} controls className="w-full" src={audioUrl} />
            </div>
          )}

          <div className="prose max-w-none">
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {highlightStory(story)}
            </p>
          </div>

          {wordsUsed.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm text-gray-500">
                Words used: {wordsUsed.join(', ')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
