import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables. Check your .env file.')
}

// Custom lock implementation to avoid Web Locks API issues
const lock = navigator.locks
  ? (name, acquireTimeout, callback) => {
      return navigator.locks.request(
        name,
        acquireTimeout === 0 ? { ifAvailable: true } : {},
        async (lock) => {
          if (lock === null) return false
          try {
            return await callback()
          } catch {
            return false
          }
        }
      )
    }
  : // Fallback for browsers without Web Locks API
    async (_name, _acquireTimeout, callback) => {
      return await callback()
    }

export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key',
  {
    auth: {
      flowType: 'pkce',
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      storageKey: 'infiniling-auth',
      lock,
    }
  }
)
