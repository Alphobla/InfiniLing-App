import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { userApi, importExportApi } from '../services/api'

const LANGUAGES = [
  'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
  'Dutch', 'Russian', 'Japanese', 'Chinese', 'Korean', 'Arabic'
]

export default function Settings() {
  const navigate = useNavigate()
  const { settings, updateSettings, signOut } = useAuthStore()
  const [motherTongue, setMotherTongue] = useState('')
  const [learningLanguage, setLearningLanguage] = useState('')
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
      setLearningLanguage(settings.learning_language || '')
      setHasApiKey(!!settings.has_api_key)
    }
    loadUsage()
  }, [settings])

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
      await updateSettings({
        mother_tongue: motherTongue,
        learning_language: learningLanguage,
      })
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
      const { data: blob } = await importExportApi.export(format, learningLanguage)
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
        learningLanguage || 'English',
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

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Language Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold mb-4">Languages</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mother Tongue
            </label>
            <select
              value={motherTongue}
              onChange={(e) => setMotherTongue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select language</option>
              {LANGUAGES.map(lang => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Learning Language
            </label>
            <select
              value={learningLanguage}
              onChange={(e) => setLearningLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select language</option>
              {LANGUAGES.map(lang => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Languages'}
          </button>
        </div>
      </div>

      {/* Token Usage */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold mb-4">Token Usage</h2>

        {usage ? (
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Used this month</span>
              <span className="font-medium">{usage.tokens_used?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Limit</span>
              <span className="font-medium">{usage.token_limit?.toLocaleString() || 'Unlimited'}</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden mt-2">
              <div
                className="h-full bg-primary-600"
                style={{ width: `${Math.min((usage.tokens_used / (usage.token_limit || 1)) * 100, 100)}%` }}
              />
            </div>
          </div>
        ) : (
          <p className="text-gray-500">Loading usage...</p>
        )}
      </div>

      {/* API Key */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold mb-4">OpenAI API Key</h2>
        <p className="text-sm text-gray-600 mb-4">
          Use your own API key to bypass token limits.
        </p>

        {hasApiKey ? (
          <div className="flex items-center justify-between">
            <span className="text-green-600">API key configured</span>
            <button
              onClick={handleRemoveApiKey}
              className="text-red-600 hover:underline text-sm"
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
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
            />
            <button
              onClick={handleSaveApiKey}
              disabled={!apiKey.trim() || saving}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              Save
            </button>
          </div>
        )}
      </div>

      {/* Import/Export */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold mb-4">Import / Export</h2>

        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-2">Export your vocabulary</p>
            <div className="flex gap-2">
              <button
                onClick={() => handleExport('csv')}
                disabled={exportLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Export CSV
              </button>
              <button
                onClick={() => handleExport('json')}
                disabled={exportLoading}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Export JSON
              </button>
            </div>
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-2">Import vocabulary (CSV or JSON)</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json"
              onChange={handleImport}
              disabled={importLoading}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
            />
          </div>
        </div>
      </div>

      {/* Sign Out */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <button
          onClick={handleSignOut}
          className="w-full py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
        >
          Sign Out
        </button>
      </div>
    </div>
  )
}
