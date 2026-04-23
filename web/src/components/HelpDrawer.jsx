import { useState, useEffect, useRef } from 'react'
import { useLocation, Link } from 'react-router-dom'

// Page-specific help content.
// Each key maps a route path to a title and a list of tips.
// Tips use { text, icon } so each one gets a small visual cue.
const helpContent = {
  '/': {
    title: 'Dashboard',
    description: 'Your learning overview at a glance.',
    tips: [
      { icon: 'chart', text: 'See how many words you\'ve collected, how many are due, and how many you\'ve mastered.' },
      { icon: 'review', text: 'When words are due for review, a button appears here to start a session.' },
      { icon: 'nav', text: 'Use the navigation above (or below on mobile) to switch between features.' },
    ],
  },
  '/vocabulary': {
    title: 'Vocabulary',
    description: 'Manage your personal word list.',
    tips: [
      { icon: 'add', text: 'Tap "Add Word" to enter a word — the AI will find its translation, frequency, and example sentences for you.' },
      { icon: 'search', text: 'Use the search bar to quickly find words by spelling or translation.' },
      { icon: 'tap', text: 'Tap any word card to expand it — you can edit translations, see example sentences, and check review dates.' },
      { icon: 'sort', text: 'Sort your list by date added, frequency level, or next review date.' },
    ],
  },
  '/review': {
    title: 'Review',
    description: 'Practice with spaced repetition flashcards.',
    tips: [
      { icon: 'tap', text: 'Tap the flashcard to flip it and reveal the translation.' },
      { icon: 'score', text: 'Rate how well you remembered: 0–2 means you need more practice, 3–5 means you got it.' },
      { icon: 'schedule', text: 'The app schedules each word based on your score — harder words come back sooner.' },
      { icon: 'stats', text: 'At the end of a session, you\'ll see your accuracy and a breakdown of correct vs. incorrect.' },
    ],
  },
  '/story': {
    title: 'Story Generator',
    description: 'Learn through AI-generated texts.',
    tips: [
      { icon: 'preset', text: 'Pick a preset (Quick, Standard, or Deep Dive) to control story length and word count.' },
      { icon: 'tap', text: 'Click any word in the generated text to see its translation instantly.' },
      { icon: 'audio', text: 'Hit "Read aloud" to generate audio — the text highlights as it plays.' },
      { icon: 'style', text: 'Customize the style (casual, formal, humorous) and format (dialogue, essay, letter) for variety.' },
    ],
  },
  '/podcast': {
    title: 'Podcast',
    description: 'Study by listening to real content.',
    tips: [
      { icon: 'search', text: 'Search for any podcast by name — starter podcasts for your language are added automatically.' },
      { icon: 'transcribe', text: 'Tap "Save & Transcribe" on an episode to generate a transcript using Whisper AI.' },
      { icon: 'tap', text: 'In study mode, click any word in the transcript for its translation.' },
      { icon: 'audio', text: 'The transcript highlights in sync as audio plays, so you can follow along.' },
    ],
  },
}

// Small icon components for each tip type — keeps things visual without emoji
const tipIcons = {
  chart: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  ),
  review: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15" />
    </svg>
  ),
  nav: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
  ),
  add: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  ),
  search: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  ),
  tap: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672 13.684 16.6m0 0-2.51 2.225.569-9.47 5.227 7.917-3.286-.672ZM12 2.25V4.5m5.834.166-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243-1.59-1.59" />
    </svg>
  ),
  sort: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5 7.5 3m0 0L12 7.5M7.5 3v13.5m13.5 0L16.5 21m0 0L12 16.5m4.5 4.5V7.5" />
    </svg>
  ),
  score: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" />
    </svg>
  ),
  schedule: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  ),
  stats: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  ),
  preset: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
    </svg>
  ),
  audio: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
    </svg>
  ),
  style: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.53 16.122a3 3 0 0 0-5.78 1.128 2.25 2.25 0 0 1-2.4 2.245 4.5 4.5 0 0 0 8.4-2.245c0-.399-.078-.78-.22-1.128Zm0 0a15.998 15.998 0 0 0 3.388-1.62m-5.043-.025a15.994 15.994 0 0 1 1.622-3.395m3.42 3.42a15.995 15.995 0 0 0 4.764-4.648l3.876-5.814a1.151 1.151 0 0 0-1.597-1.597L14.146 6.32a15.996 15.996 0 0 0-4.649 4.763m3.42 3.42a6.776 6.776 0 0 0-3.42-3.42" />
    </svg>
  ),
  transcribe: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  ),
}

// Quick links to other pages shown at the bottom of the drawer
const quickLinks = [
  { path: '/', label: 'Dashboard', desc: 'Stats overview' },
  { path: '/vocabulary', label: 'Vocabulary', desc: 'Manage words' },
  { path: '/review', label: 'Review', desc: 'Flashcards' },
  { path: '/story', label: 'Story', desc: 'AI-generated texts' },
  { path: '/podcast', label: 'Podcast', desc: 'Listen & study' },
]

export default function HelpDrawer() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const drawerRef = useRef(null)

  // Determine which content to show based on the current route
  const content = helpContent[location.pathname] || helpContent['/']

  // Filter quick links to exclude the current page
  const otherPages = quickLinks.filter(link => link.path !== location.pathname)

  // Close on Escape key
  useEffect(() => {
    if (!open) return
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [open])

  // Close when clicking outside the drawer
  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    // Use a timeout so the opening click doesn't immediately close it
    const id = setTimeout(() => {
      window.addEventListener('click', handleClick)
    }, 10)
    return () => {
      clearTimeout(id)
      window.removeEventListener('click', handleClick)
    }
  }, [open])

  // Close the drawer when navigating to a different page
  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  return (
    <>
      {/* Floating help button — bottom-right, raised above mobile nav */}
      <button
        onClick={() => setOpen(true)}
        className="fixed right-5 bottom-20 md:bottom-6 z-40
          w-11 h-11 rounded-full bg-accent text-white shadow-lg
          flex items-center justify-center
          hover:bg-accent-hover hover:scale-105 hover:shadow-xl
          active:scale-95
          transition-all duration-200"
        title="Help"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M12 18h.01" />
        </svg>
      </button>

      {/* Backdrop overlay — dims background when drawer is open */}
      {open && (
        <div className="fixed inset-0 bg-black/30 z-40 animate-fade-in" />
      )}

      {/* Slide-up drawer */}
      <div
        ref={drawerRef}
        className={`fixed inset-x-0 bottom-0 z-50 transform transition-transform duration-300 ease-out ${
          open ? 'translate-y-0' : 'translate-y-full'
        }`}
      >
        <div className="max-w-lg mx-auto bg-surface rounded-t-2xl shadow-xl border border-border border-b-0 max-h-[80vh] overflow-y-auto">
          {/* Drag handle — visual cue that this is a drawer */}
          <div className="flex justify-center pt-3 pb-1">
            <div className="w-10 h-1 bg-border rounded-full" />
          </div>

          <div className="px-6 pb-6 pt-2">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="font-display text-2xl text-text">{content.title}</h2>
                <p className="text-sm text-muted mt-0.5">{content.description}</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 text-muted hover:text-text hover:bg-bg rounded-lg transition-all mt-1"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Tips list */}
            <div className="space-y-3 mb-6">
              {content.tips.map((tip, i) => (
                <div
                  key={i}
                  className="flex gap-3 items-start animate-fade-up"
                  style={{ animationDelay: `${i * 0.05}s` }}
                >
                  {/* Icon badge */}
                  <div className="w-8 h-8 rounded-lg bg-accent/8 text-accent flex items-center justify-center flex-shrink-0 mt-0.5">
                    {tipIcons[tip.icon]}
                  </div>
                  <p className="text-sm text-text leading-relaxed">{tip.text}</p>
                </div>
              ))}
            </div>

            {/* Quick links to other pages */}
            <div className="border-t border-border pt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">Other pages</p>
              <div className="flex flex-wrap gap-2">
                {otherPages.map(link => (
                  <Link
                    key={link.path}
                    to={link.path}
                    className="px-3 py-1.5 bg-bg border border-border rounded-lg text-xs text-muted hover:text-text hover:border-accent/30 transition-all"
                  >
                    <span className="font-medium text-text">{link.label}</span>
                    <span className="mx-1 text-border">·</span>
                    {link.desc}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
