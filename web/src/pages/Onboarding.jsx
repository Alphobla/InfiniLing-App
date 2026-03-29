import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useLanguages } from '../hooks/useLanguages'
import { onboardingApi, importExportApi } from '../services/api'

export default function Onboarding() {
  const { user, settings, loading, createSettings } = useAuthStore()
  const { languages, loading: loadingLanguages } = useLanguages()
  const navigate = useNavigate()

  // Which screen is active: 'languages' | 'paths' | 'wordPicker' | 'import'
  const [screen, setScreen] = useState('languages')

  // Screen 1 state
  const [motherTongue, setMotherTongue] = useState('')
  const [targetLanguage, setTargetLanguage] = useState('')
  const [saving, setSaving] = useState(false)

  // Screen 3a state: word picker
  const [onboardingWords, setOnboardingWords] = useState([])
  const [nativeWords, setNativeWords] = useState([])
  const [selectedIndices, setSelectedIndices] = useState(new Set())
  const [loadingWords, setLoadingWords] = useState(false)

  // Screen 3b state: import
  const [importFile, setImportFile] = useState(null)
  const [importResult, setImportResult] = useState(null)
  const [importing, setImporting] = useState(false)

  // Loading / auth guards
  if (loading || loadingLanguages) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (settings) return <Navigate to="/" replace />

  // Filter target languages: exclude the selected native language
  const targetLanguages = languages.filter(l => l.name !== motherTongue)

  // Screen 1 → Screen 2: save settings, then show path choices
  const handleLanguagesContinue = async () => {
    setSaving(true)
    try {
      // motherTongue is the language name (e.g. "German"), backend converts to code
      // targetLanguage is also a name — we need the code for last_language
      const targetCode = languages.find(l => l.name === targetLanguage)?.code
      await createSettings(motherTongue, targetCode)
      setScreen('paths')
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      alert('Failed to save settings: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  // Seed "welcome" word (index 0) and navigate to destination
  const seedWelcomeAndNavigate = async (destination) => {
    setSaving(true)
    try {
      const targetCode = languages.find(l => l.name === targetLanguage)?.code
      const nativeCode = languages.find(l => l.name === motherTongue)?.code
      await onboardingApi.addWords({
        indices: [0],
        language_from: targetCode,
        language_to: nativeCode,
      })
      navigate(destination, { replace: true })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      alert('Something went wrong: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  // Load word lists when entering the word picker screen
  const enterWordPicker = async () => {
    setLoadingWords(true)
    try {
      const targetCode = languages.find(l => l.name === targetLanguage)?.code
      const nativeCode = languages.find(l => l.name === motherTongue)?.code
      const [targetRes, nativeRes] = await Promise.all([
        onboardingApi.getWords(targetCode),
        onboardingApi.getWords(nativeCode),
      ])
      setOnboardingWords(targetRes.data.words)
      setNativeWords(nativeRes.data.words)
      setScreen('wordPicker')
    } catch (err) {
      alert('Failed to load word list: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoadingWords(false)
    }
  }

  // Toggle a word's selection in the picker
  const toggleWord = (index) => {
    setSelectedIndices(prev => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else if (next.size < 10) {
        next.add(index)
      }
      return next
    })
  }

  // Submit the 10 selected words
  const submitSelectedWords = async () => {
    setSaving(true)
    try {
      const targetCode = languages.find(l => l.name === targetLanguage)?.code
      const nativeCode = languages.find(l => l.name === motherTongue)?.code
      await onboardingApi.addWords({
        indices: Array.from(selectedIndices),
        language_from: targetCode,
        language_to: nativeCode,
      })
      navigate('/vocabulary', { replace: true })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      alert('Failed to save words: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  // Handle file import
  const handleImport = async () => {
    if (!importFile) return
    setImporting(true)
    try {
      const targetCode = languages.find(l => l.name === targetLanguage)?.code
      const nativeCode = languages.find(l => l.name === motherTongue)?.code
      const { data } = await importExportApi.import(importFile, targetCode, nativeCode)
      setImportResult(data)
      setTimeout(() => navigate('/vocabulary', { replace: true }), 1500)
    } catch (err) {
      alert('Import failed: ' + (err.response?.data?.detail || err.message))
    } finally {
      setImporting(false)
    }
  }

  // SVG arrow icon reused by back buttons
  const BackArrow = () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  )

  // Shared select dropdown style (the custom chevron SVG)
  const selectStyle = {
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    backgroundSize: '20px',
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6">
      {/* Decorative blurs */}
      <div className="fixed top-0 left-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2" />
      <div className="fixed bottom-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl translate-y-1/2 translate-x-1/2" />

      <div className={`w-full relative ${screen === 'wordPicker' ? 'max-w-2xl' : 'max-w-md'}`}>
        {/* Logo */}
        <div className="flex justify-center mb-8 animate-fade-up">
          <div className="flex items-center gap-1">
            <img src="/zoom_logo.png" alt="InfiniLing" className="w-12 h-12 rounded-xl" />
            <span className="text-2xl tracking-tight">
              <span className="font-semibold text-text">Infini</span>
              <span className="font-light text-muted">Ling</span>
            </span>
          </div>
        </div>

        {/* ── Screen 1: Language Setup ── */}
        {screen === 'languages' && (
          <div className="bg-surface rounded-2xl p-8 shadow-medium border border-border animate-fade-up delay-2">
            <h1 className="text-2xl font-semibold text-center text-text mb-8">Select your languages</h1>

            {/* Native language */}
            <label className="block text-sm font-medium text-muted mb-2">I speak</label>
            <select
              value={motherTongue}
              onChange={(e) => {
                setMotherTongue(e.target.value)
                if (e.target.value === targetLanguage) setTargetLanguage('')
              }}
              className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer mb-6"
              style={selectStyle}
            >
              <option value="">Select your native language</option>
              {languages.map(lang => (
                <option key={lang.code} value={lang.name}>{lang.name}</option>
              ))}
            </select>

            {/* Target language */}
            <label className="block text-sm font-medium text-muted mb-2">I want to learn</label>
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer mb-4"
              style={selectStyle}
            >
              <option value="">Select the language you're learning</option>
              {targetLanguages.map(lang => (
                <option key={lang.code} value={lang.name}>{lang.name}</option>
              ))}
            </select>

            <p className="text-xs text-muted/70 text-center mb-6">You can add more languages later</p>

            <button
              onClick={handleLanguagesContinue}
              disabled={!motherTongue || !targetLanguage || saving}
              className="w-full py-3.5 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0"
            >
              {saving ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Setting up...
                </span>
              ) : 'Continue'}
            </button>
          </div>
        )}

        {/* ── Screen 2: Choose Your Path ── */}
        {screen === 'paths' && (
          <div className="bg-surface rounded-2xl p-8 shadow-medium border border-border animate-fade-up">
            <button
              onClick={() => setScreen('languages')}
              className="text-muted hover:text-text transition-colors mb-4 flex items-center gap-1 text-sm"
            >
              <BackArrow /> Back
            </button>

            <p className="text-sm text-muted text-center mb-2">
              InfiniLing generates stories and flashcards from your personal word list. How would you like to build yours?
            </p>
            <h1 className="text-2xl font-semibold text-center text-text mb-6">How would you like to start?</h1>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={() => seedWelcomeAndNavigate('/vocabulary')}
                disabled={saving}
                className="p-4 bg-bg border border-border rounded-xl text-left hover:border-accent/50 hover:bg-accent/5 transition-all group"
              >
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                  <span className="text-xl">📝</span>
                </div>
                <p className="font-medium text-text mb-1">Start Fresh</p>
                <p className="text-xs text-muted leading-relaxed">Begin with an empty vocabulary list and add words as you go</p>
              </button>

              <button
                onClick={enterWordPicker}
                disabled={loadingWords}
                className="p-4 bg-bg border border-border rounded-xl text-left hover:border-accent/50 hover:bg-accent/5 transition-all group"
              >
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                  <span className="text-xl">🔍</span>
                </div>
                <p className="font-medium text-text mb-1">Pick Unknown Words</p>
                <p className="text-xs text-muted leading-relaxed">Select from a list of common words to build your starting vocabulary</p>
              </button>

              <button
                onClick={() => setScreen('import')}
                className="p-4 bg-bg border border-border rounded-xl text-left hover:border-accent/50 hover:bg-accent/5 transition-all group"
              >
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                  <span className="text-xl">📥</span>
                </div>
                <p className="font-medium text-text mb-1">Import Vocabulary</p>
                <p className="text-xs text-muted leading-relaxed">Already have a word list? Import it directly</p>
              </button>

              <button
                onClick={() => seedWelcomeAndNavigate('/podcast')}
                disabled={saving}
                className="p-4 bg-bg border border-border rounded-xl text-left hover:border-accent/50 hover:bg-accent/5 transition-all group"
              >
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                  <span className="text-xl">🎧</span>
                </div>
                <p className="font-medium text-text mb-1">Start with Podcasts</p>
                <p className="text-xs text-muted leading-relaxed">Listen to podcasts and add unknown words to your list</p>
              </button>
            </div>

            {(saving || loadingWords) && (
              <div className="flex justify-center mt-4">
                <span className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        )}

        {/* ── Screen 3a: Word Picker ── */}
        {screen === 'wordPicker' && (
          <div className="bg-surface rounded-2xl p-6 shadow-medium border border-border animate-fade-up max-w-2xl w-full">
            <button
              onClick={() => { setScreen('paths'); setSelectedIndices(new Set()) }}
              className="text-muted hover:text-text transition-colors mb-4 flex items-center gap-1 text-sm"
            >
              <BackArrow /> Back
            </button>

            <h1 className="text-xl font-semibold text-center text-text mb-1">Pick 10 unknown words</h1>
            <p className="text-sm text-muted text-center mb-4">
              {selectedIndices.size} / 10 selected
            </p>

            <div className="max-h-[60vh] overflow-y-auto space-y-1.5 mb-4 pr-1">
              {onboardingWords.map((word, index) => {
                const isSelected = selectedIndices.has(index)
                const isFull = selectedIndices.size >= 10 && !isSelected
                return (
                  <button
                    key={index}
                    onClick={() => toggleWord(index)}
                    disabled={isFull}
                    className={`w-full px-4 py-2.5 rounded-lg text-left flex justify-between items-center transition-all text-sm ${
                      isSelected
                        ? 'bg-accent/10 border border-accent/40 text-text'
                        : isFull
                          ? 'bg-bg border border-border text-muted/40 cursor-not-allowed'
                          : 'bg-bg border border-border text-text hover:border-accent/30'
                    }`}
                  >
                    <span className="font-medium">{word.word}</span>
                    <span className="text-muted text-xs">{nativeWords[index]?.word}</span>
                  </button>
                )
              })}
            </div>

            <button
              onClick={submitSelectedWords}
              disabled={selectedIndices.size !== 10 || saving}
              className="w-full py-3.5 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0"
            >
              {saving ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Adding words...
                </span>
              ) : 'Continue'}
            </button>
          </div>
        )}

        {/* ── Screen 3b: Import ── */}
        {screen === 'import' && (
          <div className="bg-surface rounded-2xl p-8 shadow-medium border border-border animate-fade-up">
            <button
              onClick={() => { setScreen('paths'); setImportFile(null); setImportResult(null) }}
              className="text-muted hover:text-text transition-colors mb-4 flex items-center gap-1 text-sm"
            >
              <BackArrow /> Back
            </button>

            <h1 className="text-xl font-semibold text-center text-text mb-4">Import your vocabulary</h1>

            <div className="space-y-4 mb-6">
              <div className="bg-bg rounded-xl p-4 border border-border text-sm text-muted space-y-2">
                <p className="font-medium text-text">Accepted formats: CSV or JSON</p>
                <p>Required columns: <code className="bg-surface px-1 rounded">word</code> + <code className="bg-surface px-1 rounded">translation</code></p>
                <p>Also accepts: <code className="bg-surface px-1 rounded">source</code>/<code className="bg-surface px-1 rounded">term</code> and <code className="bg-surface px-1 rounded">target</code>/<code className="bg-surface px-1 rounded">meaning</code></p>
                <p>Optional: <code className="bg-surface px-1 rounded">lemma</code>, <code className="bg-surface px-1 rounded">example_sentence_original</code>, <code className="bg-surface px-1 rounded">example_sentence_translation</code></p>
              </div>

              <label className="block w-full border-2 border-dashed border-border rounded-xl p-6 text-center cursor-pointer hover:border-accent/40 transition-colors">
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="hidden"
                />
                {importFile ? (
                  <p className="text-text font-medium">{importFile.name}</p>
                ) : (
                  <p className="text-muted">Click to select a CSV or JSON file</p>
                )}
              </label>

              <p className="text-xs text-muted/70 text-center">
                Have a different format? Send me an email and I'll help you convert it.
              </p>
            </div>

            {importResult && (
              <div className="bg-accent/10 rounded-xl p-3 mb-4 text-sm text-text text-center">
                Imported {importResult.imported} words! Redirecting...
              </div>
            )}

            <button
              onClick={handleImport}
              disabled={!importFile || importing}
              className="w-full py-3.5 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0"
            >
              {importing ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Importing...
                </span>
              ) : 'Import'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
