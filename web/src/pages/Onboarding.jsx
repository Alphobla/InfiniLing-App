import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

const LANGUAGES = [
  'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
  'Dutch', 'Russian', 'Japanese', 'Chinese', 'Korean', 'Arabic'
]

export default function Onboarding() {
  const { user, settings, loading, createSettings } = useAuthStore()
  const [step, setStep] = useState(1)
  const [motherTongue, setMotherTongue] = useState('')
  const [saving, setSaving] = useState(false)

  // If still loading, show loading state
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  // If not logged in, redirect to login
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // If already has settings, redirect to dashboard
  if (settings) {
    return <Navigate to="/" replace />
  }

  const handleNext = () => {
    if (step === 1 && motherTongue) {
      setStep(2)
    }
  }

  const handleComplete = async () => {
    setSaving(true)
    try {
      await createSettings(motherTongue)
    } catch (err) {
      // Ignore abort errors — they mean navigation already happened (settings were created)
      if (err instanceof DOMException && err.name === 'AbortError') return
      console.error('Failed to save settings:', err)
      alert('Failed to complete setup. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Progress indicator */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${step >= 1 ? 'bg-primary-600' : 'bg-gray-300'}`} />
            <div className={`w-8 h-0.5 ${step >= 2 ? 'bg-primary-600' : 'bg-gray-300'}`} />
            <div className={`w-3 h-3 rounded-full ${step >= 2 ? 'bg-primary-600' : 'bg-gray-300'}`} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-8 shadow-sm">
          {step === 1 && (
            <>
              <h1 className="text-2xl font-bold text-center mb-2">Welcome 👋</h1>
              <p className="text-gray-600 text-center mb-8">
                First things first — what's your native language?
              </p>

              <div className="mb-6">
                <select
                  value={motherTongue}
                  onChange={(e) => setMotherTongue(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg"
                >
                  <option value="">Select your language</option>
                  {LANGUAGES.map(lang => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleNext}
                disabled={!motherTongue}
                className="w-full py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <h1 className="text-2xl font-bold text-center mb-3">Here's how it works</h1>
              
              <div className="space-y-6 mb-8">
                <div className="text-center">
                  <div className="text-3xl mb-2">📝</div>
                  <p className="text-gray-700">
                    <span className="font-medium">Add words</span> in any language you're learning.
                    <br />
                    <span className="text-gray-500 text-sm">We'll handle translations automatically.</span>
                  </p>
                </div>

                <div className="flex justify-center">
                  <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>

                <div className="text-center">
                  <div className="text-3xl mb-2">✨</div>
                  <p className="text-gray-700">
                    <span className="font-medium">Generate infinite stories</span> using your personal word bank.
                    <br />
                    <span className="text-gray-500 text-sm">Context is how we actually learn — not flashcards.</span>
                  </p>
                </div>
              </div>

              <button
                onClick={handleComplete}
                disabled={saving}
                className="w-full py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
              >
                {saving ? 'Setting up...' : "Let's go"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
