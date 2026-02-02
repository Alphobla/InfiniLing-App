import { create } from 'zustand'
import { supabase } from '../services/supabase'
import { userApi } from '../services/api'

export const useAuthStore = create((set) => ({
  user: null,
  session: null,
  settings: null,
  loading: true,

  initialize: async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        set({ user: session.user, session })
        try {
          const { data } = await userApi.getSettings()
          set({ settings: data })
        } catch (e) { /* Settings might not exist yet */ }
      }
    } catch (e) {
      console.error('Auth initialization failed:', e)
    } finally {
      set({ loading: false })
    }

    supabase.auth.onAuthStateChange(async (event, session) => {
      set({ user: session?.user || null, session })
      if (session) {
        try {
          const { data } = await userApi.getSettings()
          set({ settings: data })
        } catch (e) {}
      } else {
        set({ settings: null })
      }
    })
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
