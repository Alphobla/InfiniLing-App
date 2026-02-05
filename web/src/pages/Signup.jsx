import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const signUp = useAuthStore((s) => s.signUp)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await signUp(email, password)
      navigate('/onboarding')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg p-6">
      {/* Subtle decorative element */}
      <div className="fixed bottom-0 left-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
      
      <div className="max-w-sm w-full relative">
        {/* Logo */}
        <div className="text-center mb-10 animate-fade-up">
          <Link to="/" className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-accent rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">∞</span>
            </div>
            <span className="text-3xl tracking-tight">
              <span className="font-semibold text-text">Infini</span>
              <span className="font-light text-muted">Ling</span>
            </span>
          </Link>
        </div>

        {/* Form Card */}
        <div className="bg-surface rounded-2xl shadow-medium p-8 animate-fade-up delay-1">
          <h1 className="text-xl font-semibold text-center mb-6 text-text">Create your account</h1>
          
          {error && (
            <div className="mb-6 p-3 bg-accent-light border border-accent/20 rounded-xl text-accent text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-muted mb-2">Email</label>
              <input
                type="email"
                className="w-full px-4 py-3 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 transition-all"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-muted mb-2">Password</label>
              <input
                type="password"
                className="w-full px-4 py-3 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 transition-all"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent text-white py-3.5 rounded-xl font-medium hover:bg-accent-hover disabled:opacity-50 transition-all hover:-translate-y-0.5"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>
          
          <p className="text-center mt-8 text-muted text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-accent font-medium hover:underline underline-offset-2">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
