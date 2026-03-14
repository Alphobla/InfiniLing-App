import { useState, useCallback } from 'react'

/**
 * useWordPopover — shared hook for word-click-to-translate popover.
 *
 * Stores { word, rect } where rect is a DOMRect from getBoundingClientRect().
 * Both StoryGenerator and Podcast use this hook.
 */
export default function useWordPopover() {
  const [popover, setPopover] = useState(null)

  const openPopover = useCallback((word, rect) => {
    setPopover({ word, rect })
  }, [])

  const closePopover = useCallback(() => {
    setPopover(null)
  }, [])

  return { popover, openPopover, closePopover }
}
