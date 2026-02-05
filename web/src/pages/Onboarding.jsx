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
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
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
    <div className="min-h-screen bg-bg flex items-center justify-center p-6">
      {/* Decorative elements */}
      <div className="fixed top-0 left-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 -translate-x-1/2" />
      <div className="fixed bottom-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl translate-y-1/2 translate-x-1/2" />

      <div className="max-w-md w-full relative">
        {/* Logo */}
        <div className="flex justify-center mb-8 animate-fade-up">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-accent rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">∞</span>
            </div>
            <span className="text-2xl tracking-tight">
              <span className="font-semibold text-text">Infini</span>
              <span className="font-light text-muted">Ling</span>
            </span>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="flex justify-center mb-8 animate-fade-up delay-1">
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full transition-colors ${step >= 1 ? 'bg-accent' : 'bg-border'}`} />
            <div className={`w-10 h-0.5 transition-colors ${step >= 2 ? 'bg-accent' : 'bg-border'}`} />
            <div className={`w-2.5 h-2.5 rounded-full transition-colors ${step >= 2 ? 'bg-accent' : 'bg-border'}`} />
          </div>
        </div>

        <div className="bg-surface rounded-2xl p-8 shadow-medium border border-border animate-fade-up delay-2">
          {step === 1 && (
            <>
              <h1 className="text-2xl font-semibold text-center text-text mb-2">Welcome</h1>
              <p className="text-muted text-center mb-8">
                First things first — what's your native language?
              </p>

              <div className="mb-8">
                <select
                  value={motherTongue}
                  onChange={(e) => setMotherTongue(e.target.value)}
                  className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text appearance-none cursor-pointer"
                  style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2378756F'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', backgroundSize: '20px' }}
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
                className="w-full py-3.5 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:-translate-y-0.5 disabled:hover:translate-y-0"
              >
                Continue
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <h1 className="text-2xl font-semibold text-center text-text mb-8">How it works</h1>
              
              <div className="space-y-8 mb-10">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-xl">📝</span>
                  </div>
                  <div>
                    <p className="font-medium text-text mb-1">Add words</p>
                    <p className="text-sm text-muted">
                      Add words in any language you're learning. We'll handle translations automatically.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-xl">✨</span>
                  </div>
                  <div>
                    <p className="font-medium text-text mb-1">Generate stories</p>
                    <p className="text-sm text-muted">
                      Create infinite stories using your vocabulary. Context is how we actually learn.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleComplete}
                disabled={saving}
                className="w-full py-3.5 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover disabled:opacity-50 transition-all hover:-translate-y-0.5"
              >
                {saving ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Setting up...
                  </span>
                ) : (
                  "Let's go"
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
