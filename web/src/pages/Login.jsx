import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const signIn = useAuthStore((s) => s.signIn)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await signIn(email, password)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg p-6">
      {/* Subtle decorative element */}
      <div className="fixed top-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      
      <div className="max-w-sm w-full relative">
        {/* Logo & Tagline */}
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
          <p className="text-muted text-sm">Learn languages through stories</p>
        </div>

        {/* Form Card */}
        <div className="bg-surface rounded-2xl shadow-medium p-8 animate-fade-up delay-1">
          {error && (
            <div className="mb-6 p-3 bg-accent-light border border-accent/20 rounded-xl text-accent text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <input
                type="email"
                placeholder="Email"
                className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 transition-all"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                className="w-full px-4 py-3.5 bg-bg border border-border rounded-xl text-text placeholder:text-muted/60 transition-all"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
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
                  Signing in...
                </span>
              ) : (
                'Welcome back'
              )}
            </button>
          </form>

          <p className="text-center mt-8 text-muted text-sm">
            New here?{' '}
            <Link to="/signup" className="text-accent font-medium hover:underline underline-offset-2">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
