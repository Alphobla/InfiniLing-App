import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const signUp = useAuthStore((s) => s.signUp)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await signUp(email, password)
      setSuccess(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Show confirmation message after successful signup
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg p-6">
        <div className="fixed top-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        
        <div className="max-w-sm w-full relative">
          <div className="text-center mb-10 animate-fade-up">
            <Link to="/" className="inline-flex items-center gap-1 mb-4">
              <img 
                src="/zoom_logo.png" 
                alt="InfiniLing" 
                className="w-14 h-14 rounded-xl"
              />
              <span className="text-3xl tracking-tight">
                <span className="font-semibold text-text">Infini</span>
                <span className="font-light text-muted">Ling</span>
              </span>
            </Link>
          </div>

          <div className="bg-surface rounded-2xl shadow-medium p-8 animate-fade-up delay-1 text-center">
            <div className="w-16 h-16 bg-success-light rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-3xl">📬</span>
            </div>
            
            <h1 className="text-xl font-semibold text-text mb-3">Check out your inbox plz</h1>
            
            <p className="text-muted text-sm mb-6 leading-relaxed">
              I've sent a confirmation link to <span className="font-medium text-text">{email}</span>. 
              Click it to activate your account.
            </p>
            
            <div className="bg-warning-light border border-warning/20 rounded-xl p-4 mb-6">
              <p className="text-sm text-warning font-medium">
                📁 Don't see it? Check your spam bro!
              </p>
            </div>
            
            <Link 
              to="/login" 
              className="text-accent font-medium hover:underline underline-offset-2 text-sm"
            >
              Go to login →
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg p-6">
      {/* Subtle decorative element */}
      <div className="fixed bottom-0 left-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
      
      <div className="max-w-sm w-full relative">
        {/* Logo */}
        <div className="text-center mb-10 animate-fade-up">
          <Link to="/" className="inline-flex items-center gap-1 mb-4">
            <img 
              src="/zoom_logo.png" 
              alt="InfiniLing" 
              className="w-14 h-14 rounded-xl"
            />
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
                type="text"
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
