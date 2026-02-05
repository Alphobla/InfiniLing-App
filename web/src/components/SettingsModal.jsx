import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../stores/authStore'
import { userApi, importExportApi } from '../services/api'

const LANGUAGES = [
  'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
  'Dutch', 'Russian', 'Japanese', 'Chinese', 'Korean', 'Arabic'
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
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Mother Tongue */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mother Tongue
            </label>
            <div className="flex gap-2">
              <select
                value={motherTongue}
                onChange={(e) => setMotherTongue(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Select language</option>
                {LANGUAGES.map(lang => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
              <button
                onClick={handleSaveSettings}
                disabled={saving}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
              >
                Save
              </button>
            </div>
          </div>

          {/* Token Usage */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Token Usage</h3>
            {usage ? (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Used this month</span>
                  <span>{usage.tokens_used?.toLocaleString() || 0} / {usage.token_limit?.toLocaleString() || '∞'}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-600 transition-all"
                    style={{ width: `${Math.min((usage.tokens_used / (usage.token_limit || 1)) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">Loading...</p>
            )}
          </div>

          {/* API Key */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">OpenAI API Key</h3>
            <p className="text-xs text-gray-500 mb-2">
              Use your own key to bypass token limits.
            </p>
            {hasApiKey ? (
              <div className="flex items-center justify-between text-sm">
                <span className="text-green-600">✓ Configured</span>
                <button
                  onClick={handleRemoveApiKey}
                  className="text-red-600 hover:underline"
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
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
                <button
                  onClick={handleSaveApiKey}
                  disabled={!apiKey.trim() || saving}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
                >
                  Save
                </button>
              </div>
            )}
          </div>

          {/* Import/Export */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Import / Export</h3>
            <div className="space-y-3">
              <div className="flex gap-2">
                <button
                  onClick={() => handleExport('csv')}
                  disabled={exportLoading}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm"
                >
                  Export CSV
                </button>
                <button
                  onClick={() => handleExport('json')}
                  disabled={exportLoading}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm"
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
                className="block w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200 file:text-sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
