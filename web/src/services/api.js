import axios from 'axios'

// In dev: VITE_API_URL = 'http://localhost:8000' (different port)
// In production (Vercel): VITE_API_URL is empty/undefined, 
// so requests go to same origin where the API is served via rewrites
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

// Session getter, set by authStore once it initializes.
// This avoids a circular import (authStore imports from api.js).
let getSession = () => null
export const setSessionGetter = (fn) => { getSession = fn }

// Add auth token to requests — reads from in-memory store (instant)
// instead of calling supabase.auth.getSession() (async) on every request.
// The store session is kept up to date by onAuthStateChange in authStore.
api.interceptors.request.use((config) => {
  const session = getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// Vocabulary
export const vocabularyApi = {
  list: (params) => api.get('/api/vocabulary', { params }),
  get: (id) => api.get(`/api/vocabulary/${id}`),
  create: (data) => api.post('/api/vocabulary', data),
  update: (id, data) => api.put(`/api/vocabulary/${id}`, data),
  delete: (id) => api.delete(`/api/vocabulary/${id}`),
  enhance: (data) => api.post('/api/vocabulary/enhance', data),
  getDue: (params) => api.get('/api/vocabulary/due', { params }),
  getStatistics: (params) => api.get('/api/vocabulary/statistics', { params }),
  submitReview: (id, score) => api.post(`/api/vocabulary/${id}/review`, { score }),
}

// User
export const userApi = {
  getSettings: () => api.get('/api/user/settings'),
  createSettings: (data) => api.post('/api/user/settings', data),
  updateSettings: (data) => api.put('/api/user/settings', data),
  getUsage: () => api.get('/api/user/usage'),
  setApiKey: (apiKey) => api.put('/api/user/api-key', { api_key: apiKey }),
  removeApiKey: () => api.delete('/api/user/api-key'),
  // Dev-only: wipes user_settings + vocabulary so onboarding triggers again on next page load.
  resetOnboarding: () => api.delete('/api/user/settings'),
}

// Onboarding words
export const onboardingApi = {
  getWords: (languageCode) => api.get(`/api/onboarding-words/${languageCode}`),
  addWords: (data) => api.post('/api/onboarding-words/add', data),
}

// Generate
export const generateApi = {
  story: (data) => api.post('/api/generate/story', data),
  audio: (data) => api.post('/api/generate/audio', data, { responseType: 'blob' }),
  languages: () => api.get('/api/vocabulary/languages'),
}

// Import/Export
export const importExportApi = {
  export: (format, languageFrom) =>
    api.get('/api/export', {
      params: { format, language_from: languageFrom },
      responseType: 'blob'
    }),
  import: (file, languageFrom, languageTo, conflictResolution = 'skip') => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/import', formData, {
      params: { language_from: languageFrom, language_to: languageTo, conflict_resolution: conflictResolution }
    })
  },
}

// Podcasts
export const podcastApi = {
  search: (q, language) => api.get('/api/podcasts/search', { params: { q, language } }),
  list: (language) => api.get('/api/podcasts', { params: { language } }),
  add: (data) => api.post('/api/podcasts', data),
  remove: (id) => api.delete(`/api/podcasts/${id}`),
  episodes: (podcastId) => api.get(`/api/podcasts/${podcastId}/episodes`),
  transcribe: (podcastId, data) => api.post(`/api/podcasts/${podcastId}/episodes/transcribe`, data),
  getEpisode: (podcastId, episodeId) => api.get(`/api/podcasts/${podcastId}/episodes/${episodeId}`),
}

export default api
