import { useState, useEffect } from 'react'
import { vocabularyApi } from '../services/api'

export default function VocabularyList() {
  const [words, setWords] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingWord, setEditingWord] = useState(null)

  const fetchWords = () => {
    setLoading(true)
    vocabularyApi.list({ search: search || undefined })
      .then(({ data }) => setWords(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchWords() }, [search])

  const handleDelete = async (id) => {
    if (!confirm('Delete this word?')) return
    await vocabularyApi.delete(id)
    fetchWords()
  }

  const openAdd = () => { setEditingWord(null); setShowModal(true) }
  const openEdit = (word) => { setEditingWord(word); setShowModal(true) }
  const closeModal = () => { setShowModal(false); setEditingWord(null) }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Vocabulary</h1>
        <button onClick={openAdd} className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
          Add Word
        </button>
      </div>

      <input
        type="text"
        placeholder="Search words..."
        className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-6 focus:ring-2 focus:ring-primary-500 focus:outline-none"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {loading ? (
        <p className="text-center py-8">Loading...</p>
      ) : words.length === 0 ? (
        <p className="text-center py-8 text-gray-500">No words yet. Add your first word!</p>
      ) : (
        <div className="grid gap-4">
          {words.map((word) => (
            <div key={word.id} className="bg-white p-4 rounded-lg shadow-sm flex justify-between items-center">
              <div>
                <p className="font-medium">{word.lemma || word.word}</p>
                <p className="text-gray-600 text-sm">{word.translation}</p>
                {word.frequency_level && (
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded mt-1 inline-block">
                    {word.frequency_level}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={() => openEdit(word)} className="text-gray-600 hover:text-primary-600">Edit</button>
                <button onClick={() => handleDelete(word.id)} className="text-gray-600 hover:text-red-600">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <WordModal
          word={editingWord}
          onClose={closeModal}
          onSave={() => { closeModal(); fetchWords() }}
        />
      )}
    </div>
  )
}

function WordModal({ word, onClose, onSave }) {
  const [form, setForm] = useState({
    word: word?.word || '',
    translation: word?.translation || '',
    language_from: word?.language_from || 'en',
    language_to: word?.language_to || 'de',
  })
  const [loading, setLoading] = useState(false)
  const [enhancing, setEnhancing] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (word) {
        await vocabularyApi.update(word.id, form)
      } else {
        // Auto-enhance on add
        setEnhancing(true)
        const { data: enhanced } = await vocabularyApi.enhance({
          word: form.word,
          language_from: form.language_from,
          language_to: form.language_to,
          existing_translation: form.translation || undefined,
        })
        setEnhancing(false)

        await vocabularyApi.create({
          ...form,
          lemma: enhanced.lemma,
          translation: enhanced.translation,
          secondary_translation: enhanced.secondary_translation,
          frequency_rank: enhanced.frequency_rank,
          frequency_level: enhanced.frequency_level,
        })
      }
      onSave()
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
      setEnhancing(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">{word ? 'Edit Word' : 'Add Word'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Word</label>
            <input
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
              value={form.word}
              onChange={(e) => setForm({ ...form, word: e.target.value })}
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Translation (optional)</label>
            <input
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none"
              value={form.translation}
              onChange={(e) => setForm({ ...form, translation: e.target.value })}
              placeholder="Leave empty for auto-translation"
            />
          </div>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium mb-1">From</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={form.language_from}
                onChange={(e) => setForm({ ...form, language_from: e.target.value })}
              >
                <option value="en">English</option>
                <option value="de">German</option>
                <option value="fr">French</option>
                <option value="es">Spanish</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">To</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                value={form.language_to}
                onChange={(e) => setForm({ ...form, language_to: e.target.value })}
              >
                <option value="de">German</option>
                <option value="en">English</option>
                <option value="fr">French</option>
                <option value="es">Spanish</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {enhancing ? 'Enhancing...' : loading ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
