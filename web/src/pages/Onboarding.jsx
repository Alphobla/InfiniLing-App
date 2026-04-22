import { useState, useRef } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useLanguages } from '../hooks/useLanguages'
import { onboardingApi, importExportApi } from '../services/api'

// Step indicator shown at the top of every screen.
// `current` is 0-indexed, `total` is the number of steps.
// Each dot fills in as you progress, connected by a thin line.
function StepIndicator({ current, total }) {
  return (
    <div className="flex items-center justify-center gap-0 mb-10 animate-fade-up">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex items-center">
          {/* Dot */}
          <div
            className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${
              i <= current
                ? 'bg-accent scale-100'
                : 'bg-border scale-75'
            }`}
          />
          {/* Connecting line between dots */}
          {i < total - 1 && (
            <div className="w-10 h-0.5 mx-1">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  i < current ? 'bg-accent' : 'bg-border'
                }`}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function Onboarding() {
  const { user, settings, loading, createSettings } = useAuthStore()
  const { languages, loading: loadingLanguages } = useLanguages()
  const navigate = useNavigate()

  // Ref to track that the user has started onboarding (survived createSettings re-render).
  // Unlike useState, a ref update is synchronous and doesn't wait for React to re-render,
  // so it's already true by the time Zustand's set({ settings }) triggers a re-render.
  const onboardingStarted = useRef(false)

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
  // Only redirect if settings already exist AND onboarding hasn't started yet.
  // This means the user completed onboarding previously and navigated here by accident.
  // Once onboardingStarted is set (before createSettings), we stay put even though
  // settings becomes truthy mid-flow.
  if (settings && !onboardingStarted.current) return <Navigate to="/" replace />

  // Filter target languages: exclude the selected native language
  const targetLanguages = languages.filter(l => l.name !== motherTongue)

  // Map screen names to step indices for the progress indicator
  const stepMap = { languages: 0, paths: 1, wordPicker: 2, import: 2 }

  // Screen 1 → Screen 2: save settings, then show path choices
  const handleLanguagesContinue = async () => {
    setSaving(true)
    try {
      // Mark onboarding as in-progress BEFORE the async call.
      // createSettings will set({ settings }) in Zustand, triggering a re-render.
      // Without this ref, the guard would see settings=truthy and redirect to '/'.
      onboardingStarted.current = true

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

  // Custom chevron for <select> elements
  const selectStyle = {
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    backgroundSize: '20px',
  }

  // Path card data for Screen 2 — keeps JSX clean
  const pathCards = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      ),
      title: 'Start Fresh',
      desc: 'Begin with an empty vocabulary and add words as you discover them',
      onClick: () => seedWelcomeAndNavigate('/vocabulary'),
      disabled: saving,
      color: 'text-accent',
      bg: 'bg-accent/8',
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
      ),
      title: 'Pick Unknown Words',
      desc: 'Select from common words to kickstart your vocabulary list',
      onClick: enterWordPicker,
      disabled: loadingWords,
      color: 'text-success',
      bg: 'bg-success/8',
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
        </svg>
      ),
      title: 'Import Vocabulary',
      desc: 'Already have a word list? Upload a CSV or JSON file',
      onClick: () => setScreen('import'),
      disabled: false,
      color: 'text-warning',
      bg: 'bg-warning/8',
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
        </svg>
      ),
      title: 'Start with Podcasts',
      desc: 'Listen to podcasts and collect unknown words as you go',
      onClick: () => seedWelcomeAndNavigate('/podcast'),
      disabled: saving,
      color: 'text-[#7C3AED]',
      bg: 'bg-[#7C3AED]/8',
    },
  ]

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background texture — subtle dot grid pattern */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle, #1A1A18 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* Decorative blurs — positioned differently per screen for subtle variety */}
      <div className="fixed top-[-8rem] left-[-6rem] w-80 h-80 bg-accent/5 rounded-full blur-3xl" />
      <div className="fixed bottom-[-8rem] right-[-6rem] w-[28rem] h-[28rem] bg-accent/4 rounded-full blur-3xl" />

      <div className={`w-full relative z-10 ${screen === 'wordPicker' ? 'max-w-2xl' : 'max-w-md'}`}>

        {/* Logo — consistent across all screens */}
        <div className="flex justify-center mb-2 animate-fade-up">
          <div className="flex items-center gap-1.5">
            <img src="/zoom_logo.png" alt="InfiniLing" className="w-11 h-11 rounded-xl" />
            <span className="text-2xl tracking-tight">
              <span className="font-semibold text-text">Infini</span>
              <span className="font-light text-muted">Ling</span>
            </span>
          </div>
        </div>

        {/* Step progress indicator */}
        <StepIndicator current={stepMap[screen]} total={3} />


        {/* ── Screen 1: Language Setup ────────────────────────── */}
        {screen === 'languages' && (
          <div className="animate-fade-up delay-2">
            {/* Heading outside the card for a more editorial feel */}
            <div className="text-center mb-6">
              <h1 className="font-display text-4xl text-text mb-2">
                Welcome aboard
              </h1>
              <p className="text-muted text-sm">
                Let's set up your languages to get started
              </p>
            </div>

            <div className="bg-surface rounded-2xl p-8 shadow-medium border border-border">
              {/* Native language */}
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-2">
                I speak
              </label>
              <select
                value={motherTongue}
                onChange={(e) => {
                  setMotherTongue(e.target.value)
                  if (e.target.value === targetLanguage) setTargetLanguage('')
                }}
                className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer mb-6 transition-all hover:border-muted/40"
                style={selectStyle}
              >
                <option value="">Select your native language</option>
                {languages.map(lang => (
                  <option key={lang.code} value={lang.name}>{lang.name}</option>
                ))}
              </select>

              {/* Decorative divider with arrow */}
              <div className="flex items-center gap-3 mb-6">
                <div className="flex-1 h-px bg-border" />
                <svg className="w-4 h-4 text-muted/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
                <div className="flex-1 h-px bg-border" />
              </div>

              {/* Target language */}
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted mb-2">
                I want to learn
              </label>
              <select
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer mb-2 transition-all hover:border-muted/40"
                style={selectStyle}
              >
                <option value="">Select the language you're learning</option>
                {targetLanguages.map(lang => (
                  <option key={lang.code} value={lang.name}>{lang.name}</option>
                ))}
              </select>

              <p className="text-xs text-muted/60 text-center mb-6">You can add more languages later</p>

              <button
                onClick={handleLanguagesContinue}
                disabled={!motherTongue || !targetLanguage || saving}
                className="w-full py-3.5 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0 group"
              >
                {saving ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Setting up...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Continue
                    <svg className="w-4 h-4 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </span>
                )}
              </button>
            </div>
          </div>
        )}


        {/* ── Screen 2: Choose Your Path ────────────────────── */}
        {screen === 'paths' && (
          <div className="animate-fade-up">
            <button
              onClick={() => setScreen('languages')}
              className="text-muted hover:text-text transition-colors mb-6 flex items-center gap-1.5 text-sm group"
            >
              <span className="transition-transform group-hover:-translate-x-0.5"><BackArrow /></span>
              Back
            </button>

            <div className="text-center mb-6">
              <h1 className="font-display text-4xl text-text mb-2">
                Choose your path
              </h1>
              <p className="text-muted text-sm max-w-xs mx-auto leading-relaxed">
                InfiniLing creates stories and flashcards from your word list.
                How would you like to build it?
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {pathCards.map((card, i) => (
                <button
                  key={card.title}
                  onClick={card.onClick}
                  disabled={card.disabled}
                  className="bg-surface border border-border rounded-2xl p-5 text-left
                    hover:border-accent/30 hover:shadow-medium
                    transition-all duration-200 group animate-fade-up"
                  style={{ animationDelay: `${0.1 + i * 0.06}s` }}
                >
                  {/* Icon badge with per-card color */}
                  <div className={`w-11 h-11 ${card.bg} rounded-xl flex items-center justify-center mb-3
                    transition-transform duration-200 group-hover:scale-110 ${card.color}`}>
                    {card.icon}
                  </div>
                  <p className="font-semibold text-text mb-1 text-[15px]">{card.title}</p>
                  <p className="text-xs text-muted leading-relaxed">{card.desc}</p>
                </button>
              ))}
            </div>

            {(saving || loadingWords) && (
              <div className="flex justify-center mt-5">
                <span className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        )}


        {/* ── Screen 3a: Word Picker ────────────────────────── */}
        {screen === 'wordPicker' && (
          <div className="animate-fade-up">
            <button
              onClick={() => { setScreen('paths'); setSelectedIndices(new Set()) }}
              className="text-muted hover:text-text transition-colors mb-6 flex items-center gap-1.5 text-sm group"
            >
              <span className="transition-transform group-hover:-translate-x-0.5"><BackArrow /></span>
              Back
            </button>

            <div className="text-center mb-6">
              <h1 className="font-display text-3xl text-text mb-2">
                Pick 10 unknown words
              </h1>
              {/* Progress counter with a fill bar */}
              <div className="flex items-center justify-center gap-3">
                <div className="w-32 h-1.5 bg-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${(selectedIndices.size / 10) * 100}%` }}
                  />
                </div>
                <span className={`text-sm font-medium tabular-nums transition-colors ${
                  selectedIndices.size === 10 ? 'text-accent' : 'text-muted'
                }`}>
                  {selectedIndices.size}/10
                </span>
              </div>
            </div>

            <div className="bg-surface rounded-2xl shadow-medium border border-border p-5">
              <div className="max-h-[55vh] overflow-y-auto space-y-1.5 pr-1 mb-5">
                {onboardingWords.map((word, index) => {
                  const isSelected = selectedIndices.has(index)
                  const isFull = selectedIndices.size >= 10 && !isSelected
                  return (
                    <button
                      key={index}
                      onClick={() => toggleWord(index)}
                      disabled={isFull}
                      className={`w-full px-4 py-3 rounded-xl text-left flex justify-between items-center transition-all text-sm group ${
                        isSelected
                          ? 'bg-accent/8 border-2 border-accent/40 text-text'
                          : isFull
                            ? 'bg-bg border border-border text-muted/40 cursor-not-allowed'
                            : 'bg-bg border border-border text-text hover:border-accent/25 hover:bg-accent/3'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {/* Selection indicator — checkbox-like circle */}
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                          isSelected
                            ? 'border-accent bg-accent'
                            : 'border-border group-hover:border-muted'
                        }`}>
                          {isSelected && (
                            <svg className="w-3 h-3 text-white animate-check-pop" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                        <span className="font-medium">{word.word}</span>
                      </div>
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
                ) : 'Continue with these words'}
              </button>
            </div>
          </div>
        )}


        {/* ── Screen 3b: Import ─────────────────────────────── */}
        {screen === 'import' && (
          <div className="animate-fade-up">
            <button
              onClick={() => { setScreen('paths'); setImportFile(null); setImportResult(null) }}
              className="text-muted hover:text-text transition-colors mb-6 flex items-center gap-1.5 text-sm group"
            >
              <span className="transition-transform group-hover:-translate-x-0.5"><BackArrow /></span>
              Back
            </button>

            <div className="text-center mb-6">
              <h1 className="font-display text-3xl text-text mb-2">
                Import your words
              </h1>
              <p className="text-muted text-sm">Upload an existing vocabulary list</p>
            </div>

            <div className="bg-surface rounded-2xl p-6 shadow-medium border border-border">
              {/* Format info — compact, scannable */}
              <div className="bg-bg rounded-xl p-4 border border-border text-sm text-muted space-y-1.5 mb-5">
                <p className="font-medium text-text text-xs uppercase tracking-wider mb-2">Accepted formats</p>
                <p>
                  <span className="inline-block bg-surface border border-border rounded-md px-1.5 py-0.5 text-xs font-mono mr-1">CSV</span>
                  <span className="inline-block bg-surface border border-border rounded-md px-1.5 py-0.5 text-xs font-mono">JSON</span>
                </p>
                <p className="text-xs leading-relaxed">
                  Required: <code className="bg-surface px-1 rounded text-text">word</code> + <code className="bg-surface px-1 rounded text-text">translation</code>
                </p>
                <p className="text-xs leading-relaxed">
                  Also accepts: <code className="bg-surface px-1 rounded">source</code>/<code className="bg-surface px-1 rounded">term</code> and <code className="bg-surface px-1 rounded">target</code>/<code className="bg-surface px-1 rounded">meaning</code>
                </p>
              </div>

              {/* File upload area */}
              <label className={`block w-full border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all mb-2 ${
                importFile
                  ? 'border-accent/40 bg-accent/3'
                  : 'border-border hover:border-accent/30 hover:bg-accent/2'
              }`}>
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="hidden"
                />
                {importFile ? (
                  <div>
                    <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                      </svg>
                    </div>
                    <p className="text-text font-medium text-sm">{importFile.name}</p>
                    <p className="text-muted text-xs mt-1">Click to change file</p>
                  </div>
                ) : (
                  <div>
                    <div className="w-12 h-12 bg-bg rounded-xl flex items-center justify-center mx-auto mb-3 border border-border">
                      <svg className="w-6 h-6 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                      </svg>
                    </div>
                    <p className="text-muted text-sm">Click to select a CSV or JSON file</p>
                  </div>
                )}
              </label>

              <p className="text-xs text-muted/50 text-center mb-5">
                Different format? Send me an email and I'll help you convert it.
              </p>

              {importResult && (
                <div className="bg-success/10 border border-success/20 rounded-xl p-3 mb-4 text-sm text-success text-center font-medium">
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
          </div>
        )}
      </div>
    </div>
  )
}
