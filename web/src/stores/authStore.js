import { create } from 'zustand'
import { supabase } from '../services/supabase'
import { userApi, setSessionGetter } from '../services/api'

let initialized = false
let authListener = null

export const useAuthStore = create((set) => ({
  user: null,
  session: null,
  settings: null,
  loading: true,

  initialize: async () => {
    // Prevent multiple initializations
    if (initialized) return
    initialized = true

    // Wire up the API interceptor to read session from this store (instant, no async call)
    setSessionGetter(() => useAuthStore.getState().session)

    // Set up auth listener BEFORE getSession() so it catches the initial session.
    // This single listener handles both initial load and future changes (login/logout/token refresh),
    // and is the only place that fetches settings — no duplicate calls.
    if (!authListener) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
        set({ user: session?.user || null, session })
        if (session) {
          try {
            const { data } = await userApi.getSettings()
            set({ settings: data })
          } catch (e) { /* Settings might not exist yet */ }
        } else {
          set({ settings: null })
        }
        set({ loading: false })
      })
      authListener = subscription
    }

    // Trigger the listener above with the current session.
    // If there's no session (logged out), the listener won't fire,
    // so we still need to clear loading.
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) set({ loading: false })
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        console.warn('Auth initialization aborted (harmless Web Locks issue)')
      } else {
        console.error('Auth initialization failed:', e)
      }
      set({ loading: false })
    }
  },

  signUp: async (email, password) => {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
    return data
  },

  signIn: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    return data
  },

  signOut: async () => {
    await supabase.auth.signOut()
    set({ user: null, session: null, settings: null })
  },

  createSettings: async (motherTongue) => {
    const { data } = await userApi.createSettings({ mother_tongue: motherTongue })
    set({ settings: data })
    return data
  },

  updateSettings: async (data) => {
    const { data: updated } = await userApi.updateSettings(data)
    set({ settings: updated })
    return updated
  },
}))
