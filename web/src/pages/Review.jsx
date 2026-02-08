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
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (words.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-up">
        <div className="w-20 h-20 bg-success/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <span className="text-4xl">✓</span>
        </div>
        <h1 className="text-2xl font-semibold text-text mb-2">All caught up!</h1>
        <p className="text-muted mb-8">No words to review right now.</p>
        <Link to="/" className="text-accent font-medium hover:underline underline-offset-2">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  if (completed) {
    const total = sessionStats.correct + sessionStats.incorrect
    const percentage = total > 0 ? Math.round((sessionStats.correct / total) * 100) : 0

    return (
      <div className="max-w-md mx-auto text-center py-10 animate-fade-up">
        <h1 className="text-2xl font-semibold text-text mb-8">Session Complete</h1>

        {/* Big percentage */}
        <div className="bg-surface rounded-2xl p-8 shadow-soft border border-border mb-6">
          <div className="text-6xl font-semibold text-accent mb-2">{percentage}%</div>
          <p className="text-muted">Accuracy</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-10">
          <div className="bg-success-light rounded-xl p-5 border border-success/20">
            <div className="text-2xl font-semibold text-success mb-1">{sessionStats.correct}</div>
            <p className="text-sm text-muted">Correct</p>
          </div>
          <div className="bg-accent-light rounded-xl p-5 border border-accent/20">
            <div className="text-2xl font-semibold text-accent mb-1">{sessionStats.incorrect}</div>
            <p className="text-sm text-muted">Needs Practice</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
          <Link 
            to="/" 
            className="px-6 py-3 border border-border text-muted rounded-xl hover:bg-bg transition-colors text-center"
          >
            Dashboard
          </Link>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-accent text-white rounded-xl font-medium hover:bg-accent-hover transition-all hover:-translate-y-0.5"
          >
            Review Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto">
      {/* Progress */}
      <div className="mb-8 animate-fade-up">
        <div className="flex justify-between text-sm text-muted mb-2">
          <span>{currentIndex + 1} of {words.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-1.5 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Flashcard */}
      <div
        className="relative h-72 mb-8 cursor-pointer perspective-1000 animate-fade-up delay-1"
        onClick={() => setFlipped(!flipped)}
      >
        <div className={`absolute inset-0 transition-transform duration-500 transform-style-3d ${flipped ? 'rotate-y-180' : ''}`}>
          {/* Front */}
          <div className={`absolute inset-0 bg-surface rounded-2xl shadow-medium border border-border p-8 flex flex-col items-center justify-center backface-hidden ${flipped ? 'invisible' : ''}`}>
            <p className="text-xs text-muted uppercase tracking-widest mb-4">{currentWord.language_from}</p>
            <p className="text-4xl font-semibold text-text text-center mb-3">{currentWord.lemma || currentWord.word}</p>
            <p className="text-sm text-muted/60 mt-6">Tap to reveal</p>
          </div>

          {/* Back */}
          <div className={`absolute inset-0 bg-surface rounded-2xl shadow-medium border border-border p-8 flex flex-col items-center justify-center backface-hidden rotate-y-180 ${!flipped ? 'invisible' : ''}`}>
            <p className="text-xs text-muted uppercase tracking-widest mb-4">{currentWord.language_to}</p>
            <p className="text-3xl font-semibold text-accent text-center mb-2">{currentWord.translation}</p>
            {currentWord.secondary_translation && (
              <p className="text-muted mb-4">{currentWord.secondary_translation}</p>
            )}
            {currentWord.example_sentence_original && (
              <div className="mt-4 text-center border-t border-border pt-4 w-full">
                <p className="text-sm text-text italic">"{currentWord.example_sentence_original}"</p>
                {currentWord.example_sentence_translation && (
                  <p className="text-xs text-muted mt-2">"{currentWord.example_sentence_translation}"</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Score buttons */}
      {flipped && (
        <div className="animate-fade-up">
          <p className="text-center text-sm text-muted mb-4">How well did you know this?</p>
          <div className="grid grid-cols-6 gap-2">
            {[0, 1, 2, 3, 4, 5].map(score => (
              <button
                key={score}
                onClick={() => handleScore(score)}
                disabled={submitting}
                className={`py-4 rounded-xl font-semibold transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:transform-none ${
                  score < 3
                    ? 'bg-accent-light text-accent border border-accent/20 hover:bg-accent/10'
                    : 'bg-success-light text-success border border-success/20 hover:bg-success/10'
                }`}
              >
                {score}
              </button>
            ))}
          </div>
          <div className="flex justify-between text-xs text-muted mt-3 px-1">
            <span>Forgot</span>
            <span>Perfect</span>
          </div>
        </div>
      )}
    </div>
  )
}
