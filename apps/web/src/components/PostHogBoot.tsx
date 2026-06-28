'use client'
import { useEffect } from 'react'
import { initPostHog } from '@/lib/posthog'

export function PostHogBoot() {
  useEffect(() => {
    initPostHog()
  }, [])
  return null
}
