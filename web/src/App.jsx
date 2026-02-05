import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import VocabularyList from './pages/VocabularyList'
import Review from './pages/Review'
import StoryGenerator from './pages/StoryGenerator'
import Onboarding from './pages/Onboarding'

function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <BrowserRouter>
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
    </BrowserRouter>
  )
}

export default App
