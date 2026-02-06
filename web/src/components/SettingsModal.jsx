import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../stores/authStore'
import { userApi, importExportApi } from '../services/api'

const LANGUAGES = [
  'Arabic', 'Chinese', 'English', 'French', 'German', 'Italian', 'Russian', 'Spanish'
]

export default function SettingsModal({ onClose }) {
  const { settings, updateSettings } = useAuthStore()
  const [motherTongue, setMotherTongue] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [hasApiKey, setHasApiKey] = useState(false)
  const [usage, setUsage] = useState(null)
  const [saving, setSaving] = useState(false)
  const [importLoading, setImportLoading] = useState(false)
  const [exportLoading, setExportLoading] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (settings) {
      setMotherTongue(settings.mother_tongue || '')
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

  const handleSaveSettings = async () => {
    setSaving(true)
    try {
      await updateSettings({ mother_tongue: motherTongue })
    } catch (err) {
      console.error('Failed to save settings:', err)
      alert('Failed to save settings')
    } finally {
      setSaving(false)
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
        'English',
        motherTongue || 'English',
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-text/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-surface rounded-2xl shadow-lift max-w-md w-full max-h-[90vh] overflow-y-auto border border-border animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h2 className="text-lg font-semibold text-text">Settings</h2>
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
          {/* Mother Tongue */}
          <div>
            <label className="block text-sm font-medium text-text mb-3">
              Mother Tongue
            </label>
            <div className="flex gap-2">
              <select
                value={motherTongue}
                onChange={(e) => setMotherTongue(e.target.value)}
                className="flex-1 px-4 py-2.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer"
                style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', backgroundSize: '16px' }}
              >
                <option value="">Select language</option>
                {LANGUAGES.map(lang => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
              <button
                onClick={handleSaveSettings}
                disabled={saving}
                className="px-5 py-2.5 bg-accent text-white rounded-xl hover:bg-accent-hover disabled:opacity-50 text-sm font-medium transition-colors"
              >
                Save
              </button>
            </div>
          </div>

          {/* Token Usage */}
          <div>
            <h3 className="text-sm font-medium text-text mb-3">Token Usage</h3>
            {usage ? (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Used this month</span>
                  <span className="text-text font-medium">{usage.tokens_used?.toLocaleString() || 0} / {usage.token_limit?.toLocaleString() || '∞'}</span>
                </div>
                <div className="h-2 bg-bg rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-500"
                    style={{ width: `${Math.min((usage.tokens_used / (usage.token_limit || 1)) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">Loading...</p>
            )}
          </div>

          {/* API Key */}
          <div>
            <h3 className="text-sm font-medium text-text mb-2">OpenAI API Key</h3>
            <p className="text-xs text-muted mb-3">
              Use your own key to bypass token limits.
            </p>
            {hasApiKey ? (
              <div className="flex items-center justify-between text-sm p-3 bg-success-light rounded-xl border border-success/20">
                <span className="text-success font-medium">✓ Configured</span>
                <button
                  onClick={handleRemoveApiKey}
                  className="text-accent hover:underline underline-offset-2"
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

          {/* Import/Export */}
          <div>
            <h3 className="text-sm font-medium text-text mb-3">Import / Export</h3>
            <div className="space-y-3">
              <div className="flex gap-2">
                <button
                  onClick={() => handleExport('csv')}
                  disabled={exportLoading}
                  className="flex-1 px-4 py-2.5 border border-border rounded-xl hover:bg-bg disabled:opacity-50 text-sm text-muted hover:text-text transition-colors"
                >
                  Export CSV
                </button>
                <button
                  onClick={() => handleExport('json')}
                  disabled={exportLoading}
                  className="flex-1 px-4 py-2.5 border border-border rounded-xl hover:bg-bg disabled:opacity-50 text-sm text-muted hover:text-text transition-colors"
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

          {/* Feedback */}
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
