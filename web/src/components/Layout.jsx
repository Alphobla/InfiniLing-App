import { useState } from 'react'
import { Outlet, Navigate, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import SettingsModal from './SettingsModal'

const navItems = [
  { path: '/vocabulary', label: 'Vocabulary' },
  { path: '/review', label: 'Review' },
  { path: '/story', label: 'Story' },
]

export default function Layout() {
  const { user, settings, loading, signOut } = useAuthStore()
  const location = useLocation()
  const [showSettings, setShowSettings] = useState(false)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Redirect to onboarding if settings don't exist
  if (!settings) {
    return <Navigate to="/onboarding" replace />
  }

  return (
    <div className="min-h-screen bg-bg">
      {/* Navigation */}
      <nav className="bg-surface border-b border-border">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex justify-between h-16">
            {/* Logo & Nav */}
            <div className="flex items-center gap-12">
              <Link to="/" className="flex items-center gap-0.8 group">
                <img 
                  src="/zoom_logo.png" 
                  alt="InfiniLing" 
                  className="w-10 h-10 rounded-xl transition-transform group-hover:scale-105"
                />
                <span className="text-xl tracking-tight">
                  <span className="font-semibold text-text">Infini</span>
                  <span className="font-light text-muted">Ling</span>
                </span>
              </Link>
              
              <div className="hidden md:flex items-center gap-1">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`nav-link px-4 py-2 text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'text-accent active'
                        : 'text-muted hover:text-text'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowSettings(true)}
                className="p-2.5 text-muted hover:text-text hover:bg-bg rounded-lg transition-all"
                title="Settings"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <button
                onClick={signOut}
                className="text-sm text-muted hover:text-text transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 py-10">
        <Outlet />
      </main>

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  )
}
