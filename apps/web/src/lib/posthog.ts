'use client'
import posthog from 'posthog-js'
import type { EventName } from '@jc/shared-types'

let initialized = false

export function initPostHog() {
  if (initialized || typeof window === 'undefined') return
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST
  if (!key) return
  posthog.init(key, { api_host: host, person_profiles: 'identified_only' })
  initialized = true
}

export function track(event: EventName, props?: Record<string, unknown>) {
  if (!initialized) return
  posthog.capture(event, props)
}

export function identify(userId: string) {
  if (!initialized) return
  posthog.identify(userId)
}
