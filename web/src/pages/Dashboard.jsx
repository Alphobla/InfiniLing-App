import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { vocabularyApi } from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    vocabularyApi.getStatistics()
      .then(({ data }) => setStats(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-10 animate-fade-up">
        <h1 className="text-2xl font-semibold text-text mb-1">Welcome back y'all</h1>
        <p className="text-muted">Let's look at your stats first</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <StatCard 
          label="Total Words" 
          value={stats?.total_words || 0} 
          delay="delay-1"
        />
        <StatCard 
          label="Due for Review" 
          value={stats?.due_words || 0} 
          accent={stats?.due_words > 0}
          delay="delay-2"
        />
        <StatCard 
          label="New Words" 
          value={stats?.new_words || 0} 
          color="success"
          delay="delay-3"
        />
        <StatCard 
          label="Mastered" 
          value={stats?.future_words || 0} 
          delay="delay-4"
        />
      </div>

      {/* Review CTA */}
      {stats?.due_words > 0 && (
        <div className="bg-surface rounded-2xl p-6 md:p-8 shadow-soft border border-border animate-fade-up delay-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-text mb-1">Ready to review?</h2>
              <p className="text-muted">
                You have <span className="text-accent font-medium">{stats.due_words} words</span> waiting
              </p>
            </div>
            <Link 
              to="/review" 
              className="px-6 py-3 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover transition-all hover:-translate-y-0.5 flex items-center justify-center gap-2 w-full sm:w-auto"
            >
              Start Review
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      )}

      {/* Empty state */}
      {stats?.total_words === 0 && (
        <div className="bg-surface rounded-2xl p-10 shadow-soft border border-border text-center animate-fade-up delay-5">
          <div className="w-16 h-16 bg-accent/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">📚</span>
          </div>
          <h2 className="text-lg font-semibold text-text mb-2">Let's hit it!</h2>
          <p className="text-muted mb-6 max-w-sm mx-auto">
            Add your first words to begin learning. From there on, it only gets better.
          </p>
          <Link 
            to="/vocabulary" 
            className="inline-flex items-center gap-2 px-6 py-3 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover transition-all hover:-translate-y-0.5"
          >
            Add your first word
          </Link>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color, accent, delay = '' }) {
  const valueColor = accent 
    ? 'text-accent' 
    : color === 'success' 
      ? 'text-success' 
      : 'text-text'

  return (
    <div className={`bg-surface rounded-xl p-5 shadow-soft border border-border card-hover animate-fade-up ${delay}`}>
      <p className="text-sm text-muted mb-1">{label}</p>
      <p className={`text-3xl font-semibold ${valueColor}`}>{value}</p>
    </div>
  )
}
