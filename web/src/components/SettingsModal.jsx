import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { userApi, importExportApi, onboardingApi } from '../services/api'
import { useLanguages } from '../hooks/useLanguages'

export default function SettingsModal({ onClose }) {
  const { user, settings, signOut } = useAuthStore()
  const navigate = useNavigate()
  const [resetting, setResetting] = useState(false)
  const { languages } = useLanguages()
  const [apiKey, setApiKey] = useState('')
  const [hasApiKey, setHasApiKey] = useState(false)
  const [usage, setUsage] = useState(null)
  const [saving, setSaving] = useState(false)
  const [importLoading, setImportLoading] = useState(false)
  const [exportLoading, setExportLoading] = useState(false)
  const fileInputRef = useRef(null)

  // Word picker state
  const [showWordPicker, setShowWordPicker] = useState(false)
  const [onboardingWords, setOnboardingWords] = useState([])
  const [nativeWords, setNativeWords] = useState([])
  const [selectedIndices, setSelectedIndices] = useState(new Set())
  const [loadingWords, setLoadingWords] = useState(false)
  const [addingWords, setAddingWords] = useState(false)
  const [addedMessage, setAddedMessage] = useState('')
  const [pickerLanguage, setPickerLanguage] = useState(settings?.last_language || 'en')

  useEffect(() => {
    if (settings) {
      setHasApiKey(!!settings.has_api_key)
    }
    loadUsage()
  }, [settings])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const loadUsage = async () => {
    try {
      const { data } = await userApi.getUsage()
      setUsage(data)
    } catch (err) {
      console.error('Failed to load usage:', err)
    }
  }

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) return
    setSaving(true)
    try {
      await userApi.setApiKey(apiKey)
      setHasApiKey(true)
      setApiKey('')
      alert('API key saved')
    } catch (err) {
      console.error('Failed to save API key:', err)
      alert('Failed to save API key')
    } finally {
      setSaving(false)
    }
  }

  const handleRemoveApiKey = async () => {
    if (!confirm('Remove your API key?')) return
    try {
      await userApi.removeApiKey()
      setHasApiKey(false)
    } catch (err) {
      console.error('Failed to remove API key:', err)
    }
  }

  const handleExport = async (format) => {
    setExportLoading(true)
    try {
      const { data: blob } = await importExportApi.export(format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `vocabulary.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export:', err)
      alert('Failed to export vocabulary')
    } finally {
      setExportLoading(false)
    }
  }

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setImportLoading(true)
    try {
      const { data } = await importExportApi.import(
        file,
        settings?.last_language || 'en',
        languages.find(l => l.name === settings?.mother_tongue)?.code || 'en',
        'skip'
      )
      alert(`Imported ${data.imported || 0} words`)
    } catch (err) {
      console.error('Failed to import:', err)
      alert('Failed to import vocabulary')
    } finally {
      setImportLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const nativeCode = languages.find(l => l.name === settings?.mother_tongue)?.code || 'en'

  const fetchWordsForLanguage = async (targetCode) => {
    setLoadingWords(true)
    try {
      const [targetRes, nativeRes] = await Promise.all([
        onboardingApi.getWords(targetCode),
        onboardingApi.getWords(nativeCode),
      ])
      setOnboardingWords(targetRes.data.words)
      setNativeWords(nativeRes.data.words)
      setSelectedIndices(new Set())
      setAddedMessage('')
    } catch (err) {
      alert('Failed to load word list: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoadingWords(false)
    }
  }

  // Load the word list for the "add more words" picker
  const loadWordPicker = async () => {
    if (showWordPicker) {
      setShowWordPicker(false)
      return
    }
    await fetchWordsForLanguage(pickerLanguage)
    setShowWordPicker(true)
  }

  // When the user picks a different language, reload if the picker is already open
  const handlePickerLanguageChange = async (newCode) => {
    setPickerLanguage(newCode)
    if (showWordPicker) {
      await fetchWordsForLanguage(newCode)
    }
  }

  const toggleWord = (index) => {
    setSelectedIndices(prev => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else if (next.size < 10) next.add(index)
      return next
    })
  }

  // Dev-only: wipe settings + vocabulary, then re-enter onboarding.
  // The whole `import.meta.env.DEV` block is stripped from production bundles by Vite.
  const handleResetOnboarding = async () => {
    if (!confirm('Reset onboarding?\n\nThis deletes your settings AND all vocabulary words for this account. The auth account itself stays.')) return
    setResetting(true)
    try {
      await userApi.resetOnboarding()
      // Clear cached settings so the Onboarding guard lets us in.
      // (Zustand exposes setState on the store function for updates from outside React.)
      useAuthStore.setState({ settings: null })
      onClose()
      navigate('/onboarding')
    } catch (err) {
      alert('Reset failed: ' + (err.response?.data?.detail || err.message))
    } finally {
      setResetting(false)
    }
  }

  const submitWords = async () => {
    if (selectedIndices.size === 0) return
    setAddingWords(true)
    try {
      await onboardingApi.addWords({
        indices: Array.from(selectedIndices),
        language_from: pickerLanguage,
        language_to: nativeCode,
      })
      setAddedMessage(`Added ${selectedIndices.size} words!`)
      setSelectedIndices(new Set())
    } catch (err) {
      alert('Failed to add words: ' + (err.response?.data?.detail || err.message))
    } finally {
      setAddingWords(false)
    }
  }

  // Shared chevron style for selects
  const selectChevron = {
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    backgroundSize: '16px',
  }

  // Section heading component — keeps markup DRY
  const SectionHeading = ({ icon, children }) => (
    <div className="flex items-center gap-2 mb-3">
      <div className="w-7 h-7 rounded-lg bg-accent/8 text-accent flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-text">{children}</h3>
    </div>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-text/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-surface rounded-2xl shadow-lift max-w-md w-full max-h-[90dvh] overflow-y-auto border border-border animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border sticky top-0 bg-surface rounded-t-2xl z-10">
          <h2 className="font-display text-2xl text-text">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 text-muted hover:text-text hover:bg-bg rounded-lg transition-all"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">

          {/* ── Account ── */}
          <div>
            <SectionHeading icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
              </svg>
            }>
              Account
            </SectionHeading>

            <div className="bg-bg rounded-xl p-4 border border-border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted mb-0.5">Signed in as</p>
                  <p className="text-sm font-medium text-text">{user?.email}</p>
                </div>
                <button
                  onClick={() => { signOut(); onClose() }}
                  className="px-3 py-1.5 text-xs font-medium text-muted hover:text-accent border border-border hover:border-accent/30 rounded-lg transition-all"
                >
                  Sign out
                </button>
              </div>
            </div>
          </div>

          {/* ── Add More Words ── */}
          <div>
            <SectionHeading icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            }>
              Add More Words
            </SectionHeading>

            <p className="text-xs text-muted mb-3">
              Pick common words you don't know yet to grow your vocabulary.
            </p>

            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs text-muted whitespace-nowrap">Language</span>
              <select
                value={pickerLanguage}
                onChange={(e) => handlePickerLanguageChange(e.target.value)}
                className="flex-1 px-3 py-2 bg-bg border border-border rounded-xl text-sm text-text appearance-none cursor-pointer transition-all hover:border-muted/40"
                style={selectChevron}
              >
                {languages
                  .filter(l => l.code !== nativeCode)
                  .map(l => (
                    <option key={l.code} value={l.code}>{l.name}</option>
                  ))}
              </select>
            </div>

            <button
              onClick={loadWordPicker}
              disabled={loadingWords}
              className={`w-full px-4 py-3 border rounded-xl text-sm font-medium transition-all ${
                showWordPicker
                  ? 'bg-accent/5 border-accent/30 text-accent'
                  : 'bg-bg border-border text-text hover:border-accent/30'
              }`}
            >
              {loadingWords ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                  Loading words...
                </span>
              ) : showWordPicker ? (
                'Hide word list'
              ) : (
                'Browse word list'
              )}
            </button>

            {/* Inline word picker */}
            {showWordPicker && (
              <div className="mt-3 animate-fade-up">
                {addedMessage && (
                  <div className="mb-3 p-2.5 bg-success/10 border border-success/20 rounded-lg text-sm text-success text-center font-medium">
                    {addedMessage}
                  </div>
                )}

                {/* Selection counter + progress bar */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent rounded-full transition-all duration-300"
                      style={{ width: `${(selectedIndices.size / 10) * 100}%` }}
                    />
                  </div>
                  <span className={`text-xs font-medium tabular-nums ${
                    selectedIndices.size === 10 ? 'text-accent' : 'text-muted'
                  }`}>
                    {selectedIndices.size}/10
                  </span>
                </div>

                <div className="max-h-52 overflow-y-auto space-y-1 mb-3 pr-1">
                  {onboardingWords.map((word, index) => {
                    const isSelected = selectedIndices.has(index)
                    const isFull = selectedIndices.size >= 10 && !isSelected
                    return (
                      <button
                        key={index}
                        onClick={() => toggleWord(index)}
                        disabled={isFull}
                        className={`w-full px-3 py-2 rounded-lg text-left flex justify-between items-center transition-all text-sm ${
                          isSelected
                            ? 'bg-accent/8 border border-accent/40 text-text'
                            : isFull
                              ? 'bg-bg border border-border text-muted/40 cursor-not-allowed'
                              : 'bg-bg border border-border text-text hover:border-accent/25'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                            isSelected ? 'border-accent bg-accent' : 'border-border'
                          }`}>
                            {isSelected && (
                              <svg className="w-2.5 h-2.5 text-white animate-check-pop" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
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
                  onClick={submitWords}
                  disabled={selectedIndices.size === 0 || addingWords}
                  className="w-full py-2.5 bg-accent text-white rounded-xl text-sm font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  {addingWords ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Adding...
                    </span>
                  ) : (
                    `Add ${selectedIndices.size} word${selectedIndices.size !== 1 ? 's' : ''}`
                  )}
                </button>
              </div>
            )}
          </div>

          {/* ── Usage ── */}
          <div>
            <SectionHeading icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
            }>
              Token Usage
            </SectionHeading>

            {usage ? (
              <div className="bg-bg rounded-xl p-4 border border-border">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted">Used this month</span>
                  <span className="text-text font-medium tabular-nums">
                    {usage.tokens_used?.toLocaleString() || 0} / {usage.token_limit?.toLocaleString() || '∞'}
                  </span>
                </div>
                <div className="h-2 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-500"
                    style={{ width: `${Math.min((usage.tokens_used / (usage.token_limit || 1)) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ) : (
              <div className="bg-bg rounded-xl p-4 border border-border">
                <p className="text-sm text-muted">Loading...</p>
              </div>
            )}
          </div>

          {/* ── API Key ── */}
          <div>
            <SectionHeading icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
              </svg>
            }>
              API Key
            </SectionHeading>

            <p className="text-xs text-muted mb-3">
              Use your own OpenAI key to bypass token limits.
            </p>

            {hasApiKey ? (
              <div className="flex items-center justify-between text-sm p-3 bg-success/8 rounded-xl border border-success/20">
                <span className="text-success font-medium flex items-center gap-1.5">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                  Configured
                </span>
                <button
                  onClick={handleRemoveApiKey}
                  className="text-accent text-xs hover:underline underline-offset-2"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="flex-1 px-4 py-2.5 bg-bg border border-border rounded-xl text-sm text-text placeholder:text-muted/60"
                />
                <button
                  onClick={handleSaveApiKey}
                  disabled={!apiKey.trim() || saving}
                  className="px-5 py-2.5 bg-accent text-white rounded-xl hover:bg-accent-hover disabled:opacity-50 text-sm font-medium transition-colors"
                >
                  Save
                </button>
              </div>
            )}
          </div>

          {/* ── Import / Export ── */}
          <div>
            <SectionHeading icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            }>
              Import / Export
            </SectionHeading>

            <div className="space-y-3">
              <div className="flex gap-2">
                <button
                  onClick={() => handleExport('csv')}
                  disabled={exportLoading}
                  className="flex-1 px-4 py-2.5 bg-bg border border-border rounded-xl hover:border-accent/30 disabled:opacity-50 text-sm text-muted hover:text-text transition-all"
                >
                  Export CSV
                </button>
                <button
                  onClick={() => handleExport('json')}
                  disabled={exportLoading}
                  className="flex-1 px-4 py-2.5 bg-bg border border-border rounded-xl hover:border-accent/30 disabled:opacity-50 text-sm text-muted hover:text-text transition-all"
                >
                  Export JSON
                </button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json"
                onChange={handleImport}
                disabled={importLoading}
                className="block w-full text-sm text-muted file:mr-3 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:bg-bg file:text-text file:font-medium hover:file:bg-border/50 file:text-sm file:cursor-pointer file:transition-colors"
              />
            </div>
          </div>

          {/* ── Developer (dev-only) ──
              Vite replaces `import.meta.env.DEV` with a literal `true`/`false`
              at build time, so this whole block is dead-code-eliminated from
              the production bundle. Safe to ship. */}
          {import.meta.env.DEV && (
            <div>
              <SectionHeading icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                </svg>
              }>
                Developer
              </SectionHeading>

              <p className="text-xs text-muted mb-3">
                Wipe settings + vocabulary so you re-enter onboarding. Auth account stays.
              </p>

              <button
                onClick={handleResetOnboarding}
                disabled={resetting}
                className="w-full px-4 py-2.5 border border-red-300/50 text-red-600 rounded-xl text-sm font-medium hover:bg-red-50 disabled:opacity-50 transition-all"
              >
                {resetting ? 'Resetting...' : 'Reset Onboarding'}
              </button>
            </div>
          )}

          {/* ── Footer ── */}
          <div className="pt-2 border-t border-border">
            <p className="text-center text-xs text-muted">
              Grateful for any feedback — <a href="mailto:valentinmaissen@gmail.com" className="text-accent hover:underline underline-offset-2">contact me</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
