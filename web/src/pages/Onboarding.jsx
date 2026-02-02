import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

const LANGUAGES = [
  'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
  'Dutch', 'Russian', 'Japanese', 'Chinese', 'Korean', 'Arabic'
]

export default function Onboarding() {
  const navigate = useNavigate()
  const { createSettings } = useAuthStore()
  const [step, setStep] = useState(1)
  const [motherTongue, setMotherTongue] = useState('')
  const [saving, setSaving] = useState(false)

  const handleNext = () => {
    if (step === 1 && motherTongue) {
      setStep(2)
    }
  }

  const handleComplete = async () => {
    setSaving(true)
    try {
      await createSettings(motherTongue)
      navigate('/')
    } catch (err) {
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
              <h1 className="text-2xl font-bold text-center mb-2">Welcome to InfiniLing</h1>
              <p className="text-gray-600 text-center mb-8">
                Let's get you set up. First, what's your native language?
              </p>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mother Tongue
                </label>
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
              <h1 className="text-2xl font-bold text-center mb-2">You're all set!</h1>
              <p className="text-gray-600 text-center mb-8">
                Here's how InfiniLing helps you learn:
              </p>

              <div className="space-y-4 mb-8">
                <Feature
                  icon="📚"
                  title="Build Your Vocabulary"
                  description="Add words you encounter and we'll help you remember them."
                />
                <Feature
                  icon="🔄"
                  title="Smart Reviews"
                  description="Our spaced repetition system optimizes when you review each word."
                />
                <Feature
                  icon="📖"
                  title="Learn in Context"
                  description="Generate stories using your vocabulary to see words in action."
                />
              </div>

              <button
                onClick={handleComplete}
                disabled={saving}
                className="w-full py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
              >
                {saving ? 'Setting up...' : 'Get Started'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function Feature({ icon, title, description }) {
  return (
    <div className="flex gap-4">
      <div className="text-2xl">{icon}</div>
      <div>
        <h3 className="font-medium">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  )
}
