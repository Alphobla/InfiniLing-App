import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { vocabularyApi } from '../services/api'

export default function Review() {
  const [words, setWords] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [sessionStats, setSessionStats] = useState({ correct: 0, incorrect: 0 })
  const [completed, setCompleted] = useState(false)

  useEffect(() => {
    vocabularyApi.getDue({ limit: 20 })
      .then(({ data }) => setWords(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const currentWord = words[currentIndex]
  const progress = words.length > 0 ? ((currentIndex) / words.length) * 100 : 0

  const handleScore = async (score) => {
    if (submitting) return
    setSubmitting(true)

    try {
      await vocabularyApi.submitReview(currentWord.id, score)

      setSessionStats(prev => ({
        correct: prev.correct + (score >= 3 ? 1 : 0),
        incorrect: prev.incorrect + (score < 3 ? 1 : 0),
      }))

      if (currentIndex + 1 >= words.length) {
        setCompleted(true)
      } else {
        setCurrentIndex(prev => prev + 1)
        setFlipped(false)
      }
    } catch (err) {
      console.error('Failed to submit review:', err)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading review session...</div>
  }

  if (words.length === 0) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">No words to review</h1>
        <p className="text-gray-600 mb-6">Great job! You're all caught up.</p>
        <Link to="/" className="text-primary-600 hover:underline">Back to Dashboard</Link>
      </div>
    )
  }

  if (completed) {
    const total = sessionStats.correct + sessionStats.incorrect
    const percentage = total > 0 ? Math.round((sessionStats.correct / total) * 100) : 0

    return (
      <div className="max-w-md mx-auto text-center py-12">
        <h1 className="text-2xl font-bold mb-6">Session Complete!</h1>

        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <div className="text-5xl font-bold text-primary-600 mb-2">{percentage}%</div>
          <p className="text-gray-600">Accuracy</p>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-green-50 rounded-xl p-4">
            <div className="text-2xl font-bold text-green-600">{sessionStats.correct}</div>
            <p className="text-sm text-gray-600">Correct</p>
          </div>
          <div className="bg-red-50 rounded-xl p-4">
            <div className="text-2xl font-bold text-red-600">{sessionStats.incorrect}</div>
            <p className="text-sm text-gray-600">Needs Practice</p>
          </div>
        </div>

        <div className="flex gap-4 justify-center">
          <Link to="/" className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            Dashboard
          </Link>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Review Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto">
      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>{currentIndex + 1} of {words.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-600 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Flashcard */}
      <div
        className="relative h-64 mb-6 cursor-pointer perspective-1000"
        onClick={() => setFlipped(!flipped)}
      >
        <div className={`absolute inset-0 transition-transform duration-500 transform-style-3d ${flipped ? 'rotate-y-180' : ''}`}>
          {/* Front */}
          <div className={`absolute inset-0 bg-white rounded-xl shadow-sm p-6 flex flex-col items-center justify-center backface-hidden ${flipped ? 'invisible' : ''}`}>
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{currentWord.language_from}</p>
            <p className="text-3xl font-bold text-center">{currentWord.word}</p>
            {currentWord.lemma && currentWord.lemma !== currentWord.word && (
              <p className="text-sm text-gray-500 mt-2">({currentWord.lemma})</p>
            )}
            <p className="text-sm text-gray-400 mt-4">Tap to reveal</p>
          </div>

          {/* Back */}
          <div className={`absolute inset-0 bg-white rounded-xl shadow-sm p-6 flex flex-col items-center justify-center backface-hidden rotate-y-180 ${!flipped ? 'invisible' : ''}`}>
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{currentWord.language_to}</p>
            <p className="text-2xl font-bold text-center text-primary-600">{currentWord.translation}</p>
            {currentWord.secondary_translation && (
              <p className="text-sm text-gray-500 mt-1">{currentWord.secondary_translation}</p>
            )}
            {currentWord.example_sentence_original && (
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-700 italic">"{currentWord.example_sentence_original}"</p>
                {currentWord.example_sentence_translation && (
                  <p className="text-xs text-gray-500 mt-1">"{currentWord.example_sentence_translation}"</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Score buttons - only show when flipped */}
      {flipped && (
        <div>
          <p className="text-center text-sm text-gray-600 mb-3">How well did you know this?</p>
          <div className="grid grid-cols-6 gap-2">
            {[0, 1, 2, 3, 4, 5].map(score => (
              <button
                key={score}
                onClick={() => handleScore(score)}
                disabled={submitting}
                className={`py-3 rounded-lg font-medium transition-colors ${
                  score < 3
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                } disabled:opacity-50`}
              >
                {score}
              </button>
            ))}
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2 px-1">
            <span>Forgot</span>
            <span>Perfect</span>
          </div>
        </div>
      )}
    </div>
  )
}
