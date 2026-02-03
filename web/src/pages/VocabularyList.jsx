import { useState, useEffect, useMemo } from 'react'
import { vocabularyApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

// Frequency badge colors
const FREQUENCY_COLORS = {
  'Top 1,000': { bg: '#2E7D32', text: 'white' },
  'Top 5,000': { bg: '#388E3C', text: 'white' },
  'Top 10,000': { bg: '#689F38', text: 'white' },
  'Top 20,000': { bg: '#FBC02D', text: '#1a1a1a' },
  'Top 50,000': { bg: '#FF8F00', text: 'white' },
  'Rare': { bg: '#D32F2F', text: 'white' },
  'Unknown': { bg: '#757575', text: 'white' },
}

const LANGUAGES = {
  en: 'English',
  de: 'German',
  fr: 'French',
  es: 'Spanish',
  it: 'Italian',
  pt: 'Portuguese',
}

export default function VocabularyList() {
  const { settings } = useAuthStore()
  const [words, setWords] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeTab, setActiveTab] = useState(null)
  const [sortBy, setSortBy] = useState('date')
  const [sortAsc, setSortAsc] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)

  // Fetch all words (we'll filter client-side for tabs)
  const fetchWords = async () => {
    setLoading(true)
    try {
      const { data } = await vocabularyApi.list({ limit: 200 })
      setWords(data)
    } catch (err) {
      console.error('Failed to fetch words:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchWords() }, [])

  // Get unique languages from words
  const languages = useMemo(() => {
    const langs = {}
    words.forEach(w => {
      if (!langs[w.language_from]) langs[w.language_from] = 0
      langs[w.language_from]++
    })
    return langs
  }, [words])

  // Set initial tab
  useEffect(() => {
    if (!activeTab && Object.keys(languages).length > 0) {
      // Prefer last_language from settings, otherwise first available
      const lastLang = settings?.last_language
      if (lastLang && languages[lastLang]) {
        setActiveTab(lastLang)
      } else {
        setActiveTab(Object.keys(languages)[0])
      }
    }
  }, [languages, settings, activeTab])

  // Filter and sort words
  const filteredWords = useMemo(() => {
    let result = words.filter(w => w.language_from === activeTab)

    // Search filter
    if (search) {
      const s = search.toLowerCase()
      result = result.filter(w =>
        w.word?.toLowerCase().includes(s) ||
        w.lemma?.toLowerCase().includes(s) ||
        w.translation?.toLowerCase().includes(s)
      )
    }

    // Sort
    result.sort((a, b) => {
      let cmp = 0
      if (sortBy === 'date') {
        cmp = new Date(b.created_at) - new Date(a.created_at)
      } else if (sortBy === 'frequency') {
        // Lower rank = more common = should come first
        const rankA = a.frequency_rank || 999999
        const rankB = b.frequency_rank || 999999
        cmp = rankA - rankB
      } else if (sortBy === 'due') {
        // null (new) and past dates first
        const today = new Date().toISOString().split('T')[0]
        const dateA = a.next_review_date
        const dateB = b.next_review_date

        const scoreA = !dateA ? 0 : dateA <= today ? 1 : 2
        const scoreB = !dateB ? 0 : dateB <= today ? 1 : 2

        if (scoreA !== scoreB) {
          cmp = scoreA - scoreB
        } else {
          cmp = (dateA || '').localeCompare(dateB || '')
        }
      }
      return sortAsc ? -cmp : cmp
    })

    return result
  }, [words, activeTab, search, sortBy, sortAsc])

  const handleSort = (type) => {
    if (sortBy === type) {
      setSortAsc(!sortAsc)
    } else {
      setSortBy(type)
      setSortAsc(false)
    }
  }

  const handleExpand = (id) => {
    if (expandedId === id) {
      setExpandedId(null)
      setEditingId(null)
    } else {
      setExpandedId(id)
      setEditingId(null)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this word?')) return
    try {
      await vocabularyApi.delete(id)
      setWords(words.filter(w => w.id !== id))
      setExpandedId(null)
      setEditingId(null)
    } catch (err) {
      alert('Failed to delete word')
    }
  }

  const handleSave = async (id, updates) => {
    try {
      await vocabularyApi.update(id, updates)
      await fetchWords()
      setEditingId(null)
    } catch (err) {
      alert('Failed to save changes')
    }
  }

  const handleAddComplete = (newWord) => {
    setShowAddForm(false)
    if (newWord) {
      fetchWords()
      // Switch to the language tab of the new word
      setActiveTab(newWord.language_from)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">My Words</h1>
        <button
          onClick={() => setShowAddForm(true)}
          disabled={showAddForm}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          + Add Word
        </button>
      </div>

      {/* Language Tabs */}
      {Object.keys(languages).length > 0 && (
        <div className="flex gap-2 mb-4 border-b border-gray-200">
          {Object.entries(languages).map(([lang, count]) => (
            <button
              key={lang}
              onClick={() => setActiveTab(lang)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === lang
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {LANGUAGES[lang] || lang} ({count})
            </button>
          ))}
        </div>
      )}

      {/* Sort Controls & Search */}
      <div className="flex flex-wrap gap-4 mb-4 items-center">
        <div className="flex gap-2">
          <span className="text-gray-500 text-sm self-center">Sort:</span>
          <SortButton active={sortBy === 'date'} asc={sortAsc} onClick={() => handleSort('date')}>
            Date added
          </SortButton>
          <SortButton active={sortBy === 'frequency'} asc={sortAsc} onClick={() => handleSort('frequency')}>
            Frequency
          </SortButton>
          <SortButton active={sortBy === 'due'} asc={sortAsc} onClick={() => handleSort('due')}>
            Due
          </SortButton>
        </div>
        <input
          type="text"
          placeholder="Search..."
          className="flex-1 min-w-[200px] px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Add Word Form */}
      {showAddForm && (
        <AddWordForm
          defaultLanguage={activeTab}
          motherTongue={settings?.mother_tongue || 'en'}
          onComplete={handleAddComplete}
        />
      )}

      {/* Word List */}
      {filteredWords.length === 0 ? (
        <p className="text-center py-8 text-gray-500">
          {words.length === 0 ? 'No words yet. Add your first word!' : 'No words match your search.'}
        </p>
      ) : (
        <div className="space-y-2">
          {filteredWords.map((word) => (
            <WordCard
              key={word.id}
              word={word}
              expanded={expandedId === word.id}
              editing={editingId === word.id}
              onExpand={() => handleExpand(word.id)}
              onEdit={() => setEditingId(word.id)}
              onCancelEdit={() => setEditingId(null)}
              onSave={(updates) => handleSave(word.id, updates)}
              onDelete={() => handleDelete(word.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function SortButton({ children, active, asc, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 text-sm rounded-lg transition-colors ${
        active
          ? 'bg-indigo-100 text-indigo-700 font-medium'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {children}
      {active && (
        <span className="ml-1">{asc ? '↑' : '↓'}</span>
      )}
    </button>
  )
}

function FrequencyBadge({ level }) {
  const colors = FREQUENCY_COLORS[level] || FREQUENCY_COLORS['Unknown']
  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-medium"
      style={{ backgroundColor: colors.bg, color: colors.text }}
    >
      {level || 'Unknown'}
    </span>
  )
}

function DueIndicator({ nextReviewDate }) {
  if (!nextReviewDate) {
    return (
      <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
        New
      </span>
    )
  }

  const today = new Date().toISOString().split('T')[0]
  if (nextReviewDate <= today) {
    return <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" title="Due" />
  }

  return null
}

function WordCard({ word, expanded, editing, onExpand, onEdit, onCancelEdit, onSave, onDelete }) {
  const [form, setForm] = useState({})

  useEffect(() => {
    if (editing) {
      setForm({
        lemma: word.lemma || '',
        translation: word.translation || '',
        secondary_translation: word.secondary_translation || '',
        example_sentence_original: word.example_sentence_original || '',
        example_sentence_translation: word.example_sentence_translation || '',
      })
    }
  }, [editing, word])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(form)
  }

  // Collapsed view
  if (!expanded) {
    return (
      <div
        onClick={onExpand}
        className="bg-white p-4 rounded-lg shadow-sm flex justify-between items-center cursor-pointer hover:shadow-md transition-shadow"
      >
        <div className="flex items-center gap-4">
          <div>
            <span className="font-medium">{word.lemma || word.word}</span>
            <span className="text-gray-400 mx-2">—</span>
            <span className="text-gray-600">{word.translation}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <FrequencyBadge level={word.frequency_level} />
          <DueIndicator nextReviewDate={word.next_review_date} />
        </div>
      </div>
    )
  }

  // Expanded view
  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <form onSubmit={handleSubmit}>
        {/* Header */}
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          {editing ? (
            <input
              className="text-lg font-semibold bg-gray-50 border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              value={form.lemma}
              onChange={(e) => setForm({ ...form, lemma: e.target.value })}
            />
          ) : (
            <h3 className="text-lg font-semibold">{word.lemma || word.word}</h3>
          )}
          <div className="flex gap-2">
            {editing ? (
              <>
                <button type="submit" className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">
                  Save
                </button>
                <button type="button" onClick={onCancelEdit} className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button type="button" onClick={onEdit} className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
                  Edit
                </button>
              </>
            )}
            <button type="button" onClick={onDelete} className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded">
              Delete
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Translation */}
          <div className="grid grid-cols-[120px_1fr] gap-2 items-start">
            <span className="text-gray-500 text-sm">Translation</span>
            {editing ? (
              <input
                className="bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                value={form.translation}
                onChange={(e) => setForm({ ...form, translation: e.target.value })}
              />
            ) : (
              <span>{word.translation}</span>
            )}
          </div>

          {/* Secondary Translation */}
          <div className="grid grid-cols-[120px_1fr] gap-2 items-start">
            <span className="text-gray-500 text-sm">Secondary</span>
            {editing ? (
              <input
                className="bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                value={form.secondary_translation}
                onChange={(e) => setForm({ ...form, secondary_translation: e.target.value })}
                placeholder="Alternative meaning"
              />
            ) : (
              <span className="text-gray-600">{word.secondary_translation || '—'}</span>
            )}
          </div>

          {/* Frequency */}
          <div className="grid grid-cols-[120px_1fr] gap-2 items-center">
            <span className="text-gray-500 text-sm">Frequency</span>
            <div className="flex items-center gap-2">
              <FrequencyBadge level={word.frequency_level} />
              {word.frequency_rank && (
                <span className="text-gray-500 text-sm">(#{word.frequency_rank.toLocaleString()})</span>
              )}
            </div>
          </div>

          {/* Example Sentence */}
          <div className="grid grid-cols-[120px_1fr] gap-2 items-start">
            <span className="text-gray-500 text-sm">Example</span>
            {editing ? (
              <div className="space-y-2">
                <input
                  className="w-full bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  value={form.example_sentence_original}
                  onChange={(e) => setForm({ ...form, example_sentence_original: e.target.value })}
                  placeholder="Example sentence"
                />
                <input
                  className="w-full bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm text-gray-600 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  value={form.example_sentence_translation}
                  onChange={(e) => setForm({ ...form, example_sentence_translation: e.target.value })}
                  placeholder="Translation"
                />
              </div>
            ) : (
              <div>
                {word.example_sentence_original ? (
                  <>
                    <p className="italic">{word.example_sentence_original}</p>
                    {word.example_sentence_translation && (
                      <p className="text-gray-500 text-sm">{word.example_sentence_translation}</p>
                    )}
                  </>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </div>
            )}
          </div>

          {/* Divider */}
          <hr className="border-gray-100" />

          {/* Stats */}
          <div className="text-sm text-gray-500 space-y-1">
            <p>Added: {new Date(word.created_at).toLocaleDateString()}</p>
            {word.next_review_date ? (
              <p>
                Next review: {formatReviewDate(word.next_review_date)}
                {word.review_interval_days && ` (interval: ${word.review_interval_days} days)`}
              </p>
            ) : (
              <p>Not yet reviewed</p>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}

function formatReviewDate(dateStr) {
  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  const reviewDate = new Date(dateStr)
  reviewDate.setHours(0, 0, 0, 0)

  if (reviewDate <= today) {
    return 'Today (due)'
  } else if (reviewDate.getTime() === tomorrow.getTime()) {
    return 'Tomorrow'
  } else {
    return date.toLocaleDateString()
  }
}

function AddWordForm({ defaultLanguage, motherTongue, onComplete }) {
  const [word, setWord] = useState('')
  const [language, setLanguage] = useState(defaultLanguage || 'de')
  const [loading, setLoading] = useState(false)
  const [enhanced, setEnhanced] = useState(null)
  const [form, setForm] = useState(null)

  const handleTranslate = async (e) => {
    e.preventDefault()
    if (!word.trim()) return

    setLoading(true)
    try {
      const { data } = await vocabularyApi.enhance({
        word: word.trim(),
        language_from: language,
        language_to: motherTongue,
      })
      setEnhanced(data)
      setForm({
        lemma: data.lemma || word,
        translation: data.translation || '',
        secondary_translation: data.secondary_translation || '',
        example_sentence_original: data.example_sentence_original || '',
        example_sentence_translation: data.example_sentence_translation || '',
      })
    } catch (err) {
      alert('Failed to translate: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await vocabularyApi.create({
        word: word.trim(),
        lemma: form.lemma,
        translation: form.translation,
        secondary_translation: form.secondary_translation || null,
        language_from: language,
        language_to: motherTongue,
        frequency_rank: enhanced?.frequency_rank,
        frequency_level: enhanced?.frequency_level,
        example_sentence_original: form.example_sentence_original || null,
        example_sentence_translation: form.example_sentence_translation || null,
      })
      onComplete(data)
    } catch (err) {
      alert('Failed to save: ' + (err.response?.data?.detail || err.message))
      setLoading(false)
    }
  }

  const handleCancel = () => {
    onComplete(null)
  }

  // Initial form - just word and language
  if (!enhanced) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
        <form onSubmit={handleTranslate}>
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">Add Word</h3>
            <button type="button" onClick={handleCancel} className="text-gray-500 hover:text-gray-700">
              Cancel
            </button>
          </div>
          <div className="grid grid-cols-[1fr_150px] gap-4 mb-4">
            <div>
              <label className="block text-sm text-gray-500 mb-1">Word</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                value={word}
                onChange={(e) => setWord(e.target.value)}
                placeholder="Enter a word..."
                autoFocus
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-1">Language</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {Object.entries(LANGUAGES).filter(([code]) => code !== motherTongue).map(([code, name]) => (
                  <option key={code} value={code}>{name}</option>
                ))}
              </select>
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !word.trim()}
            className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Translating...' : 'Translate'}
          </button>
        </form>
      </div>
    )
  }

  // Edit form after translation
  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-4">
      <form onSubmit={handleSave}>
        {/* Header */}
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          <input
            className="text-lg font-semibold bg-gray-50 border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            value={form.lemma}
            onChange={(e) => setForm({ ...form, lemma: e.target.value })}
          />
          <div className="flex gap-2">
            <button type="submit" disabled={loading} className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50">
              {loading ? 'Saving...' : 'Save'}
            </button>
            <button type="button" onClick={handleCancel} className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200">
              Cancel
            </button>
            <button type="button" onClick={handleCancel} className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded">
              Delete
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-[120px_1fr] gap-2 items-start">
            <span className="text-gray-500 text-sm">Translation</span>
            <input
              className="bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              value={form.translation}
              onChange={(e) => setForm({ ...form, translation: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-[120px_1fr] gap-2 items-start">
            <span className="text-gray-500 text-sm">Secondary</span>
            <input
              className="bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              value={form.secondary_translation}
              onChange={(e) => setForm({ ...form, secondary_translation: e.target.value })}
              placeholder="Alternative meaning"
            />
          </div>

          <div className="grid grid-cols-[120px_1fr] gap-2 items-center">
            <span className="text-gray-500 text-sm">Frequency</span>
            <div className="flex items-center gap-2">
              <FrequencyBadge level={enhanced.frequency_level} />
              {enhanced.frequency_rank && (
                <span className="text-gray-500 text-sm">(#{enhanced.frequency_rank.toLocaleString()})</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-[120px_1fr] gap-2 items-start">
            <span className="text-gray-500 text-sm">Example</span>
            <div className="space-y-2">
              <input
                className="w-full bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                value={form.example_sentence_original}
                onChange={(e) => setForm({ ...form, example_sentence_original: e.target.value })}
                placeholder="Example sentence (optional)"
              />
              <input
                className="w-full bg-gray-50 border border-gray-300 rounded px-2 py-1 text-sm text-gray-600 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                value={form.example_sentence_translation}
                onChange={(e) => setForm({ ...form, example_sentence_translation: e.target.value })}
                placeholder="Translation (optional)"
              />
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}
