import { useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'

// Lazy-loaded pages — each becomes a separate JS chunk that is only
// downloaded when the user navigates to that route.
const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const VocabularyList = lazy(() => import('./pages/VocabularyList'))
const Review = lazy(() => import('./pages/Review'))
const StoryGenerator = lazy(() => import('./pages/StoryGenerator'))
const Onboarding = lazy(() => import('./pages/Onboarding'))

const PageLoader = () => (
  <div className="flex items-center justify-center py-20">
    <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
  </div>
)

function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/vocabulary" element={<VocabularyList />} />
            <Route path="/review" element={<Review />} />
            <Route path="/story" element={<StoryGenerator />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
