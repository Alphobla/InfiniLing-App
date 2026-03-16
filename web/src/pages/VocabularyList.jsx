import { useState, useEffect, useMemo } from 'react'
import { vocabularyApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import { useLanguages } from '../hooks/useLanguages'

// Frequency badge colors - more refined palette
const FREQUENCY_COLORS = {
  'Top 1,000': { bg: '#2D8A7B', text: 'white' },
  'Top 5,000': { bg: '#3D9E8C', text: 'white' },
  'Top 10,000': { bg: '#5AAF8F', text: 'white' },
  'Top 20,000': { bg: '#D4880F', text: 'white' },
  'Top 50,000': { bg: '#E69B3A', text: 'white' },
  'Rare': { bg: '#C53030', text: 'white' },
  'Unknown': { bg: '#78756F', text: 'white' },
}

export default function VocabularyList() {
  const { settings, updateSettings } = useAuthStore()
  // languageMap: { code: name } lookup, e.g. { en: 'English' }
  const { languages: availableLanguages, languageMap } = useLanguages()
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
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="animate-fade-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
        <button
          onClick={() => setShowAddForm(true)}
          disabled={showAddForm}
          className="bg-accent text-white px-5 py-2.5 rounded-xl font-medium hover:bg-accent-hover disabled:opacity-50 transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0 w-full sm:w-auto"
        >
          + Add Word
        </button>
      </div>

      {/* Language Tabs */}
      {Object.keys(languages).length > 0 && (
        <div className="flex gap-1 mb-6 border-b border-border overflow-x-auto">
          {Object.entries(languages).map(([lang, count]) => (
            <button
              key={lang}
              onClick={() => {
                setActiveTab(lang)
                updateSettings({ last_language: lang })
              }}
              className={`nav-link px-5 py-3 font-medium transition-colors flex-shrink-0 ${
                activeTab === lang
                  ? 'text-accent active'
                  : 'text-muted hover:text-text'
              }`}
            >
              {languageMap[lang] || lang} ({count})
            </button>
          ))}
        </div>
      )}

      {/* Sort Controls & Search */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex gap-2 items-center flex-wrap">
          <span className="text-muted text-sm">Sort:</span>
          <SortButton active={sortBy === 'date'} asc={sortAsc} onClick={() => handleSort('date')}>
            Date
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
          className="flex-1 min-w-0 px-4 py-2 bg-bg border border-border rounded-xl text-sm text-text placeholder:text-muted/60"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Add Word Form */}
      {showAddForm && (
        <AddWordForm
          defaultLanguage={activeTab}
          motherTongue={settings?.mother_tongue || 'en'}
          availableLanguages={availableLanguages}
          onComplete={handleAddComplete}
        />
      )}

      {/* Word List */}
      {filteredWords.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 bg-bg rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">📝</span>
          </div>
          <p className="text-muted">
            {words.length === 0 ? 'No words yet. Add your first word!' : 'No words match your search.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredWords.map((word, index) => (
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
              style={{ animationDelay: `${Math.min(index * 0.03, 0.3)}s` }}
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
      className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
        active
          ? 'border-accent bg-accent-light text-accent font-medium'
          : 'border-border text-muted hover:border-muted'
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
      <span className="px-2 py-0.5 rounded text-xs font-medium bg-success-light text-success border border-success/20">
        New
      </span>
    )
  }

  const today = new Date().toISOString().split('T')[0]
  if (nextReviewDate <= today) {
    return <span className="w-2.5 h-2.5 rounded-full bg-accent inline-block" title="Due" />
  }

  return null
}

function WordCard({ word, expanded, editing, onExpand, onEdit, onCancelEdit, onSave, onDelete, style }) {
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
        style={style}
        className="bg-surface p-4 rounded-xl border border-border flex justify-between items-center cursor-pointer card-hover"
      >
        <div className="flex items-center gap-4 min-w-0 flex-1">
          <div className="truncate">
            <span className="font-medium text-text">{word.lemma || word.word}</span>
            <span className="text-border mx-2 sm:mx-3">—</span>
            <span className="text-muted">{word.translation}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          <FrequencyBadge level={word.frequency_level} />
          <DueIndicator nextReviewDate={word.next_review_date} />
        </div>
      </div>
    )
  }

  // Expanded view
  return (
    <div className="bg-surface rounded-xl border border-border overflow-hidden shadow-soft animate-scale-in">
      <form onSubmit={handleSubmit}>
        {/* Header */}
        <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          {editing ? (
            <input
              className="text-lg font-semibold bg-bg border border-border rounded-lg px-3 py-1.5 text-text w-full sm:w-auto"
              value={form.lemma}
              onChange={(e) => setForm({ ...form, lemma: e.target.value })}
            />
          ) : (
            <h3 className="text-lg font-semibold text-text">{word.lemma || word.word}</h3>
          )}
          <div className="flex gap-2 flex-wrap">
            {editing ? (
              <>
                <button type="submit" className="px-4 py-1.5 text-sm bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors">
                  Save
                </button>
                <button type="button" onClick={onCancelEdit} className="px-4 py-1.5 text-sm bg-bg text-muted border border-border rounded-lg hover:bg-border/50 transition-colors">
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button type="button" onClick={onEdit} className="px-4 py-1.5 text-sm bg-bg text-muted border border-border rounded-lg hover:bg-border/50 transition-colors">
                  Edit
                </button>
              </>
            )}
            <button type="button" onClick={onDelete} className="px-4 py-1.5 text-sm text-accent hover:bg-accent-light rounded-lg transition-colors">
              Delete
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-5 space-y-4">
          {/* Translation */}
          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start">
            <span className="text-muted text-sm">Translation</span>
            {editing ? (
              <input
                className="bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text w-full"
                value={form.translation}
                onChange={(e) => setForm({ ...form, translation: e.target.value })}
              />
            ) : (
              <span className="text-text">{word.translation}</span>
            )}
          </div>

          {/* Secondary Translation */}
          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start">
            <span className="text-muted text-sm">Secondary</span>
            {editing ? (
              <input
                className="bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text w-full"
                value={form.secondary_translation}
                onChange={(e) => setForm({ ...form, secondary_translation: e.target.value })}
                placeholder="Alternative meaning"
              />
            ) : (
              <span className="text-muted">{word.secondary_translation || '—'}</span>
            )}
          </div>

          {/* Frequency */}
          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start sm:items-center">
            <span className="text-muted text-sm">Frequency</span>
            <div className="flex items-center gap-2">
              <FrequencyBadge level={word.frequency_level} />
              {word.frequency_rank && (
                <span className="text-muted text-sm">(#{word.frequency_rank.toLocaleString()})</span>
              )}
            </div>
          </div>

          {/* Example Sentence */}
          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start">
            <span className="text-muted text-sm">Example</span>
            {editing ? (
              <div className="space-y-2">
                <input
                  className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text"
                  value={form.example_sentence_original}
                  onChange={(e) => setForm({ ...form, example_sentence_original: e.target.value })}
                  placeholder="Example sentence"
                />
                <input
                  className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-muted"
                  value={form.example_sentence_translation}
                  onChange={(e) => setForm({ ...form, example_sentence_translation: e.target.value })}
                  placeholder="Translation"
                />
              </div>
            ) : (
              <div>
                {word.example_sentence_original ? (
                  <>
                    <p className="italic text-text">{word.example_sentence_original}</p>
                    {word.example_sentence_translation && (
                      <p className="text-muted text-sm mt-1">{word.example_sentence_translation}</p>
                    )}
                  </>
                ) : (
                  <span className="text-muted/50">—</span>
                )}
              </div>
            )}
          </div>

          {/* Divider */}
          <hr className="border-border" />

          {/* Stats */}
          <div className="text-sm text-muted space-y-1">
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

function AddWordForm({ defaultLanguage, motherTongue, availableLanguages, onComplete }) {
  const [word, setWord] = useState('')
  // Default to first language that isn't the mother tongue
  const getDefaultLanguage = () => {
    if (defaultLanguage) return defaultLanguage
    const filtered = availableLanguages.filter(l => l.code !== motherTongue)
    return filtered[0]?.code || availableLanguages[0]?.code || 'en'
  }
  const [language, setLanguage] = useState(getDefaultLanguage())
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
      <div className="bg-surface rounded-xl border border-border p-5 mb-6 animate-scale-in">
        <form onSubmit={handleTranslate}>
          <div className="flex justify-between items-center mb-5">
            <h3 className="font-semibold text-text">Add Word</h3>
            <button type="button" onClick={handleCancel} className="text-muted hover:text-text transition-colors">
              Cancel
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_150px] gap-4 mb-5">
            <div>
              <label className="block text-sm text-muted mb-2">Word</label>
              <input
                type="text"
                className="w-full px-4 py-2.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60"
                value={word}
                onChange={(e) => setWord(e.target.value)}
                placeholder="Enter a word..."
                autoFocus
                required
              />
            </div>
            <div>
              <label className="block text-sm text-muted mb-2">Language</label>
              <select
                className="w-full px-4 py-2.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer"
                style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', backgroundSize: '16px' }}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {availableLanguages.filter(l => l.code !== motherTongue).map(l => (
                  <option key={l.code} value={l.code}>{l.name}</option>
                ))}
              </select>
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !word.trim()}
            className="w-full bg-accent text-white py-2.5 rounded-xl font-medium hover:bg-accent-hover disabled:opacity-50 transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Translating...
              </span>
            ) : (
              'Translate'
            )}
          </button>
        </form>
      </div>
    )
  }

  // Edit form after translation
  return (
    <div className="bg-surface rounded-xl border border-border overflow-hidden mb-6 shadow-soft animate-scale-in">
      <form onSubmit={handleSave}>
        {/* Header */}
        <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <input
            className="text-lg font-semibold bg-bg border border-border rounded-lg px-3 py-1.5 text-text w-full sm:w-auto"
            value={form.lemma}
            onChange={(e) => setForm({ ...form, lemma: e.target.value })}
          />
          <div className="flex gap-2">
            <button type="submit" disabled={loading} className="px-4 py-1.5 text-sm bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50 transition-colors">
              {loading ? 'Saving...' : 'Save'}
            </button>
            <button type="button" onClick={handleCancel} className="px-4 py-1.5 text-sm bg-bg text-muted border border-border rounded-lg hover:bg-border/50 transition-colors">
              Cancel
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start">
            <span className="text-muted text-sm">Translation</span>
            <input
              className="bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text w-full"
              value={form.translation}
              onChange={(e) => setForm({ ...form, translation: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start">
            <span className="text-muted text-sm">Secondary</span>
            <input
              className="bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text w-full"
              value={form.secondary_translation}
              onChange={(e) => setForm({ ...form, secondary_translation: e.target.value })}
              placeholder="Alternative meaning"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start sm:items-center">
            <span className="text-muted text-sm">Frequency</span>
            <div className="flex items-center gap-2">
              <FrequencyBadge level={enhanced.frequency_level} />
              {enhanced.frequency_rank && (
                <span className="text-muted text-sm">(#{enhanced.frequency_rank.toLocaleString()})</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[120px_1fr] gap-1 sm:gap-3 items-start">
            <span className="text-muted text-sm">Example</span>
            <div className="space-y-2">
              <input
                className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text"
                value={form.example_sentence_original}
                onChange={(e) => setForm({ ...form, example_sentence_original: e.target.value })}
                placeholder="Example sentence (optional)"
              />
              <input
                className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-muted"
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
