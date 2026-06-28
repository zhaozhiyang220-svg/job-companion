'use client'
import { useEffect, useState } from 'react'

const TITLE_NORMAL = 'Job Companion'
const TITLE_DISGUISE = 'TimeFlow - Pomodoro & Tasks'

export function useDisguise() {
  const [on, setOn] = useState(false)

  useEffect(() => {
    document.title = on ? TITLE_DISGUISE : TITLE_NORMAL
    const link = document.querySelector("link[rel*='icon']") as HTMLLinkElement | null
    if (link) link.href = on ? '/disguise-favicon.svg' : '/favicon.ico'
  }, [on])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault()
        setOn((p) => !p)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return { on, toggle: () => setOn((p) => !p) }
}
