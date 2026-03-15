import { useState, useEffect, useMemo } from 'react'
import api from '../services/api'

/**
 * Hook to fetch and cache available languages from the API.
 * Single source of truth: api/services/languages.py
 * 
 * Returns:
 * - languages: Array of { code: 'en', name: 'English' } objects, sorted alphabetically
 * - languageMap: Object mapping code to name, e.g. { en: 'English', fr: 'French' }
 * - loading: Boolean indicating if languages are still being fetched
 * - error: Error message if fetch failed, null otherwise
 * 
 * The languages are cached in module scope, so subsequent calls
 * across different components don't re-fetch.
 */

// Module-level cache - shared across all component instances
let cachedLanguages = null
let fetchPromise = null

export function useLanguages() {
  const [languages, setLanguages] = useState(cachedLanguages || [])
  const [loading, setLoading] = useState(!cachedLanguages)
  const [error, setError] = useState(null)

  useEffect(() => {
    // If already cached, we're done
    if (cachedLanguages) {
      setLanguages(cachedLanguages)
      setLoading(false)
      return
    }

    // If already fetching, wait for that promise
    if (fetchPromise) {
      fetchPromise
        .then(langs => {
          setLanguages(langs)
          setLoading(false)
        })
        .catch(err => {
          setError(err.message)
          setLoading(false)
        })
      return
    }

    // Start fetching
    fetchPromise = api.get('/api/languages')
      .then(response => {
        // API returns { languages: [{ code: 'fr', name: 'French' }, ...] }
        const langs = response.data.languages
        cachedLanguages = langs
        return langs
      })
      .catch(err => {
        console.error('Failed to fetch languages:', err)
        throw err
      })

    fetchPromise
      .then(langs => {
        setLanguages(langs)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  // Create a lookup map: { code: name } for easy access
  // Example: { en: 'English', fr: 'French' }
  const languageMap = useMemo(() => {
    const map = {}
    languages.forEach(lang => {
      map[lang.code] = lang.name
    })
    return map
  }, [languages])

  return { languages, languageMap, loading, error }
}

/**
 * Helper to get language name from code.
 * Use after languages are loaded.
 */
export function getLanguageName(languages, code) {
  const lang = languages.find(l => l.code === code)
  return lang ? lang.name : code
}

/**
 * Helper to get language code from name.
 * Use after languages are loaded.
 */
export function getLanguageCode(languages, name) {
  const lang = languages.find(l => l.name.toLowerCase() === name.toLowerCase())
  return lang ? lang.code : null
}
