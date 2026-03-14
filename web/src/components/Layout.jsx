import { useState } from 'react'
import { Outlet, Navigate, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import SettingsModal from './SettingsModal'

const navItems = [
  { path: '/vocabulary', label: 'Vocabulary' },
  { path: '/review', label: 'Review' },
  { path: '/story', label: 'Story' },
  { path: '/podcast', label: 'Podcast' },
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
      <main className="max-w-5xl mx-auto px-6 py-10 pb-24 md:pb-10">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-surface border-t border-border md:hidden safe-area-bottom">
        <div className="flex justify-around items-center h-16">
          <Link
            to="/vocabulary"
            className={`flex flex-col items-center gap-1 px-6 py-2 transition-colors ${
              location.pathname === '/vocabulary' ? 'text-accent' : 'text-muted'
            }`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span className="text-xs font-medium">Words</span>
          </Link>
          <Link
            to="/review"
            className={`flex flex-col items-center gap-1 px-6 py-2 transition-colors ${
              location.pathname === '/review' ? 'text-accent' : 'text-muted'
            }`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span className="text-xs font-medium">Review</span>
          </Link>
          <Link
            to="/story"
            className={`flex flex-col items-center gap-1 px-6 py-2 transition-colors ${
              location.pathname === '/story' ? 'text-accent' : 'text-muted'
            }`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span className="text-xs font-medium">Story</span>
          </Link>
          <Link
            to="/podcast"
            className={`flex flex-col items-center gap-1 px-6 py-2 transition-colors ${
              location.pathname === '/podcast' ? 'text-accent' : 'text-muted'
            }`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m-4 0h8m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            <span className="text-xs font-medium">Podcast</span>
          </Link>
        </div>
      </nav>

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  )
}
