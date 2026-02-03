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

  if (loading) return <div className="text-center py-12">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Welcome back!</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Words" value={stats?.total_words || 0} />
        <StatCard label="Due for Review" value={stats?.due_words || 0} color="yellow" />
        <StatCard label="New Words" value={stats?.new_words || 0} color="green" />
        <StatCard label="Mastered" value={stats?.future_words || 0} color="primary" />
      </div>

      {stats?.due_words > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-lg font-semibold mb-2">Ready to review?</h2>
          <p className="text-gray-600 mb-4">You have {stats.due_words} words waiting.</p>
          <Link to="/review" className="inline-block bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
            Start Review
          </Link>
        </div>
      )}

    </div>
  )
}

function StatCard({ label, value, color = 'gray' }) {
  const colors = {
    gray: 'text-gray-900',
    yellow: 'text-yellow-600',
    green: 'text-green-600',
    primary: 'text-primary-600',
  }
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${colors[color]}`}>{value}</p>
    </div>
  )
}
